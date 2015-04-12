from ore.accounts.models import OreUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

# Create your models here.
from django.utils import timezone
from model_utils import Choices
from model_utils.fields import StatusField
import reversion


@reversion.register
class Flag(models.Model):
    STATUS = Choices('new', 'quashed', 'retracted', 'content_removed_moderator', 'content_removed_creator')
    status = StatusField()

    flagger = models.ForeignKey(OreUser, null=False, blank=False, related_name='flagger_flags')
    resolver = models.ForeignKey(OreUser, null=True, blank=True, related_name='resolver_flags')
    date_flagged = models.DateTimeField(auto_now_add=True, null=False, blank=False)
    date_resolved = models.DateTimeField(null=True, blank=True, default=None)

    FLAG_TYPE = Choices('inappropriate', 'spam')
    flag_type = StatusField(choices_name='FLAG_TYPE')

    extra_comments = models.TextField(blank=True, null=False)

    content_type = models.ForeignKey(ContentType, null=False, blank=False)
    object_id = models.PositiveIntegerField(null=False, blank=False)
    content_object = GenericForeignKey('content_type', 'object_id')

    @classmethod
    def create_flag(cls, flag_content, flag_type, flagger, extra_comments):
        content_type = ContentType.objects.get_for_model(flag_content)
        if cls.flagged(flag_content, flagger=flagger):
            return None
        return Flag.objects.get_or_create(content_type=content_type, object_id=flag_content.id, flag_type=flag_type, flagger=flagger, extra_comments=extra_comments)

    @classmethod
    def flagged(cls, flag_content, flagger=None, include_resolved=False):
        content_type = ContentType.objects.get_for_model(flag_content)
        qs = Flag.objects.filter(content_type=content_type, object_id=flag_content.id)
        if flagger is not None:
            qs = qs.filter(flagger=flagger)
        if not include_resolved:
            qs = qs.filter(status=cls.STATUS.new)
        return qs.exists()

    def remove_content(self, user):
        if self.status != self.STATUS.new:
            raise ValueError("Incorrect state")

        self.status = self.STATUS.content_removed_creator if not user.is_staff else self.STATUS.content_removed_moderator
        self.content_object.status = self.content_object.STATUS.deleted
        self.date_resolved = timezone.now()
        self.resolver = user
        self.save()

    def quash(self, user):
        if self.status != self.STATUS.new:
            raise ValueError("Incorrect state")

        self.status = self.STATUS.quashed
        self.date_resolved = timezone.now()
        self.resolver = user
        self.save()

    def retract(self, user):
        if self.status != self.STATUS.new:
            raise ValueError("Incorrect state")

        self.status = self.STATUS.retracted
        self.date_resolved = timezone.now()
        self.resolver = user
        self.save()
