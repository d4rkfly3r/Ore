from django.db.models import QuerySet
from model_utils import FieldTracker
from rest_framework.serializers import ModelSerializer


class FieldSecurityPolicy(object):
    class Base(object):
        def __and__(self, other):
            return FieldSecurityPolicy.And(self, other)

        def __or__(self, other):
            return FieldSecurityPolicy.Or(self, other)

        def __xor__(self, other):
            return FieldSecurityPolicy.Xor(self, other)

    class Permission(Base):
        def __init__(self, permission_slug):
            self.permission_slug = permission_slug

        def __call__(self, user, obj, field):
            if obj is None:
                return False
            return obj.user_has_permission(user, self.permission_slug)

    class And(Base):
        def __init__(self, left, right):
            self.left, self.right = left, right

        def __call__(self, user, obj, field):
            return self.left(user, obj, field) and self.right(user, obj, field)

    class Or(Base):
        def __init__(self, left, right):
            self.left, self.right = left, right

        def __call__(self, user, obj, field):
            return self.left(user, obj, field) or self.right(user, obj, field)

    class Not(Base):
        def __init__(self, inner):
            self.inner = inner

        def __call__(self, user, obj, field):
            return not self.inner(user, obj, field)

    class Xor(Base):
        def __init__(self, left, right):
            self.left, self.right = left, right

        def __call__(self, user, obj, field):
            l = self.left(user, obj, field)
            r = self.right(user, obj, field)
            return (l and not r) or (r and not l)

    class Creating(Base):
        def __call__(self, user, obj, field):
            return obj is None

    class AllowWriteIf(Base):
        def __init__(self, inner):
            self.inner = inner

        def __call__(self, user, obj, field):
            field.read_only = not self.inner(user, obj, field)

    @classmethod
    def AllowWriteCreatingOrIf(cls, inner):
        return cls.AllowWriteIf(cls.Or(cls.Creating(), inner))

    class SetQuerySet(Base):
        def __init__(self, queryset):
            self.queryset = queryset

        def __call__(self, user, obj, field):
            q = self.queryset
            if callable(q):
                q = q(user, obj, field)
            field.queryset = q


class FieldSurrogate(object):
    def __init__(self):
        self.read_only = None
        self.queryset = None


class FieldSecurityPolicyEnforcer(object):
    def __init__(self, policy):
        self.policy = policy

    def enforce_policy(self, fields, instance, user):
        # make everything read-only
        for field in fields.values():
            field.read_only = True

        policy = self.policy
        for field_name, field_policies in policy.items():
            field = fields[field_name]
            if isinstance(field_policies, FieldSecurityPolicy.Base):
                field_policies = [field_policies]
            for field_policy in field_policies:
                field_policy(user, instance, field)

        return fields


class FieldSecurityPolicySerializerMixin(object):
    def get_fields(self):
        fields = super(FieldSecurityPolicySerializerMixin, self).get_fields()

        instance = getattr(self, 'instance', None)
        instance = instance if instance is not None and not isinstance(instance, QuerySet) else None

        user = self.context['request'].user
        fields = self.get_policy_enforcer().enforce_policy(fields, instance, user)

        return fields

    def get_policy(self):
        if not getattr(self, 'policy', None):
            if isinstance(self, ModelSerializer) and getattr(self.Meta.model, 'policy', None):
                return getattr(self.Meta.model, 'policy', None)

            raise ValueError("'policy' or 'get_policy' must be overriden to use the FieldSecurityPolicySerializerMixin")
        return self.policy

    def get_policy_enforcer(self):
        return FieldSecurityPolicyEnforcer(self.get_policy())


class FieldSecurityPolicyViolation(Exception):
    pass


class FieldSecurityPolicyModelMixin(object):
    def save(self, force_insert=False, force_update=False, update_fields=None, as_user=None, *args, **kwargs):
        if getattr(self, 'tracker', None) is None:
            raise Exception('tracker must be a FieldTracker')

        if as_user is not None:
            changed_fields = set(self.tracker.changed().keys())
            if update_fields and not force_insert:
                changed_fields = changed_fields.intersection(update_fields)

            if force_insert and force_update:
                raise ValueError('how about no - only one of force_insert or force_update please')

            instance = None if not self.pk or force_insert else self

            fields = {}
            for model_field in self._meta.fields:
                fields[model_field.name] = FieldSurrogate()

            fresh_instance = None
            if instance is not None:
                fresh_instance = type(instance).objects.get(pk=instance.pk)
            fields = self.get_policy_enforcer().enforce_policy(fields, fresh_instance, as_user)

            for field_name, field in fields.items():
                field_newval = getattr(self, field_name)

                if field.read_only == True and (
                            field_name in changed_fields or
                            (field_name + '_id') in changed_fields
                ):
                    raise FieldSecurityPolicyViolation(
                        'Attempted to update {}'.format(field_name)
                    )
                elif field.queryset is not None and not field.queryset.filter(pk=field_newval.id).exists():
                    raise FieldSecurityPolicyViolation(
                        'Attempted to set {} to {}'.format(field_name, field_newval)
                    )


        return super(FieldSecurityPolicyModelMixin, self).save(
            force_insert=force_insert, force_update=force_update, update_fields=update_fields, *args, **kwargs
        )

    def get_policy(self):
        if not getattr(self, 'policy', None):
            raise ValueError("'policy' or 'get_policy' must be overridden to use the FieldSecurityPolicyModelMixin")
        return self.policy

    def get_policy_enforcer(self):
        return FieldSecurityPolicyEnforcer(self.get_policy())