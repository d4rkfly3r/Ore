from ore.core.models import Namespace
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, AnonymousUser, UserManager
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _t
import hashlib
from ore.core.util import UserFilteringQuerySet, prefix_q
import reversion


class OreUserManager(UserManager):
    def _create_user(self, username, email, password, is_staff, is_superuser, **extra_fields):
        now = timezone.now()
        if not username:
            raise ValueError("The given username must be set")
        email = self.normalize_email(email)
        user = self.model(
            name=username,
            email=email,
            is_staff=is_staff,
            status=OreUser.STATUS.active,
            is_superuser=is_superuser,
            date_joined=now,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user


class OreUser(AbstractBaseUser, PermissionsMixin, Namespace):
    # All taken from AbstractUser
    # name from Namespace
    email = models.EmailField('email', blank=True)
    is_staff = models.BooleanField('staff status', default=False,
                                   help_text='Designates whether the user can log into this admin '
                                             'site.')
    date_joined = models.DateTimeField(_t('creation date'), default=timezone.now)

    objects = OreUserManager.from_queryset(UserFilteringQuerySet)()

    USERNAME_FIELD = 'name'
    REQUIRED_FIELDS = ['email']

    @staticmethod
    def is_visible_q(prefix, user):
        if user.is_anonymous():
            return prefix_q(prefix, status='active')
        elif user.is_superuser:
            return Q()

        return (
            prefix_q(prefix, status='active') |
            (
                ~prefix_q(prefix, status='deleted') &
                prefix_q(prefix, id=user.id)
            )
        )

    @property
    def is_active(self):
        return self.status == OreUser.STATUS.active

    @property
    def avatar(self):
        return "//www.gravatar.com/avatar/%s?d=mm" % hashlib.md5(
            self.email.encode('UTF-8').strip().lower()
        ).hexdigest()

    def get_short_name(self):
        return self.name

    def get_full_name(self):
        return self.name

    def email_user(self, subject, message, from_email=None, **kwargs):
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def user_has_permission(self, user, perm_slug, project=None):
        if isinstance(user, AnonymousUser):
            return False
        elif user.is_superuser:
            return True
        return user == self

    def __str__(self):
        return self.name

    def __repr__(self):
        props = (['staff'] if self.is_staff else []) + (['active'] if self.is_active else [])
        return '<RepoUser %s <%s> [%s]>' % (self.name, self.email, ' '.join(props))


reversion.register(OreUser, follow=['namespace_ptr'])
