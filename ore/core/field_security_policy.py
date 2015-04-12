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

        def resolve(self, user, obj):
            return obj.user_has_permission(user, self.permission_slug)

    class And(Base):
        def __init__(self, left, right):
            self.left, self.right = left, right

        def resolve(self, user, obj):
            return self.left.resolve(user, obj) and self.right.resolve(user, obj)

    class Or(Base):
        def __init__(self, left, right):
            self.left, self.right = left, right

        def resolve(self, user, obj):
            return self.left.resolve(user, obj) or self.right.resolve(user, obj)

    class Xor(Base):
        def __init__(self, left, right):
            self.left, self.right = left, right

        def resolve(self, user, obj):
            l = self.left.resolve(user, obj)
            r = self.right.resolve(user, obj)
            return ((l and not r) or (r and not l))

class FieldSecurityPolicyEnforcer(object):
    def __init__(self, policy):
        self.policy = policy

    def enforce_policy(self, fields, instance, user):
        # make everything read-only
        for field in fields.values():
            field.read_only = True

        policy = self.policy
        for field_name, field_policy in policy.items():
            if field_policy.resolve(user, instance):
                fields[field_name].read_only = False

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