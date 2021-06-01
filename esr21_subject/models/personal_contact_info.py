from django.db import models
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe
from edc_action_item.model_mixins import ActionModelMixin
from edc_base.model_mixins import BaseUuidModel
from edc_base.model_validators import datetime_not_future
from edc_base.sites import SiteModelMixin
from edc_base.utils import get_utcnow
from edc_constants.choices import YES_NO, YES_NO_NA, YES_NO_DOESNT_WORK
from edc_locator.model_mixins import LocatorModelMixin
from edc_protocol.validators import datetime_not_before_study_start

from ..action_items import CONTACT_INFORMATION_ACTION


class PersonalContactInfo(LocatorModelMixin, ActionModelMixin, SiteModelMixin,
                          BaseUuidModel):

    action_name = CONTACT_INFORMATION_ACTION

    tracking_identifier_prefix = 'CI'

    site = models.ForeignKey(
        Site, related_name='site_name', on_delete=models.PROTECT,
        null=True, editable=False)

    report_datetime = models.DateTimeField(
        default=get_utcnow,
        validators=[datetime_not_before_study_start, datetime_not_future])

    date_signed = models.DateField(
        verbose_name='Date Locator form signed',
        default=get_utcnow,)

    may_call = models.CharField(
        max_length=25,
        choices=YES_NO_NA,
        verbose_name=mark_safe(
            'Has the participant given his/her permission for study '
            'staff to call her for follow-up purposes during the study?'))

    may_visit_home = models.CharField(
        max_length=25,
        choices=YES_NO,
        verbose_name=mark_safe(
            'Has the participant given his/her permission for study staff <b>to '
            'make home visits</b> for follow-up purposes during the study??'))

    may_call_work = models.CharField(
        max_length=25,
        choices=YES_NO_DOESNT_WORK,
        verbose_name=mark_safe(
            'Has the participant given his/her permission for study staff '
            'to contact her at work for follow up purposes during the study?'))

    class Meta:
        app_label = 'esr21_subject'
        verbose_name = 'Personal Contact Information'
        verbose_name_plural = 'Personal Contact Information'
