from django.db.models import QuerySet


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
            return ((l and not r) or (r and not l))

    class AllowWriteIf(Base):
        def __init__(self, inner):
            self.inner = inner

        def __call__(self, user, obj, field):
            field.read_only = not self.inner(user, obj, field)

    class SetQuerySet(Base):
        def __init__(self, queryset):
            self.queryset = queryset

        def __call__(self, user, obj, field):
            q = self.queryset
            if callable(q):
                q = q(user, obj, field)
            field.queryset = q


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


class FieldSecurityPolicyMixin(object):
    def get_fields(self):
        fields = super(FieldSecurityPolicyMixin, self).get_fields()

        instance = getattr(self, 'instance', None)
        has_instance = instance is not None and not isinstance(instance, QuerySet)

        if has_instance:
            user = self.context['request'].user
            fields = self.get_policy_enforcer().enforce_policy(fields, instance, user)

        return fields

    def get_policy(self):
        if not getattr(self, 'policy', None):
            raise ValueError("'policy' or 'get_policy' must be overriden to use the FieldSecurityPolicyEnforcer")
        return self.policy

    def get_policy_enforcer(self):
        return FieldSecurityPolicyEnforcer(self.get_policy())