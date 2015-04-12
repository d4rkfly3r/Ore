from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from model_utils.managers import InheritanceQuerySetMixin, InheritanceManagerMixin


def validate_not_prohibited(value):
    if value.lower() in settings.PROHIBITED_NAMES:
        raise ValidationError('%s is not allowed.' % value)


def prefix_q(prefix, **kwargs):
    return Q(**{
        prefix + k: v for k, v in kwargs.items()
    })


class UserFilteringQuerySet(models.QuerySet):
    def as_user(self, user):
        return self.filter(self.model.is_visible_q('', user)).distinct()

UserFilteringManager = models.Manager.from_queryset(UserFilteringQuerySet)

class UserFilteringInheritanceQuerySet(InheritanceQuerySetMixin, UserFilteringQuerySet):
    pass


class UserFilteringInheritanceManager(InheritanceManagerMixin, UserFilteringManager):
    def get_queryset(self):
        return UserFilteringInheritanceQuerySet(self.model, using=self._db)
