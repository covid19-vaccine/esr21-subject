from django.core.validators import RegexValidator
from django.db import models
from django.apps import apps as django_apps

from django_crypto_fields.fields import EncryptedCharField
from edc_base.model_fields import OtherCharField
from edc_base.model_managers import HistoricalRecords
from edc_base.model_mixins import BaseUuidModel
from edc_base.sites import CurrentSiteManager
from edc_base.sites.site_model_mixin import SiteModelMixin
from edc_base.utils import get_utcnow
from edc_consent.field_mixins import IdentityFieldsMixin, ReviewFieldsMixin
from edc_consent.field_mixins import PersonalFieldsMixin, VulnerabilityFieldsMixin
from edc_consent.managers import ConsentManager
from edc_consent.model_mixins import ConsentModelMixin
from edc_consent.validators import eligible_if_yes
from edc_constants.choices import YES_NO
from edc_identifier.model_mixins import NonUniqueSubjectIdentifierModelMixin
from edc_registration.model_mixins import UpdatesOrCreatesRegistrationModelMixin
from edc_search.model_mixins import SearchSlugManager

from ..choices import GENDER_OTHER
from ..choices import IDENTITY_TYPE
from ..subject_identifier import SubjectIdentifier
from .model_mixins import SearchSlugModelMixin


class InformedConsentManager(ConsentManager, SearchSlugManager, models.Manager):

    def get_by_natural_key(self, subject_identifier, version):
        return self.get(
            subject_identifier=subject_identifier, version=version)


class InformedConsent(ConsentModelMixin, SiteModelMixin,
                      UpdatesOrCreatesRegistrationModelMixin,
                      NonUniqueSubjectIdentifierModelMixin, IdentityFieldsMixin,
                      ReviewFieldsMixin, PersonalFieldsMixin, VulnerabilityFieldsMixin,
                      SearchSlugModelMixin, BaseUuidModel):

    subject_screening_model = 'esr21_subject.eligibilityconfirmation'

    initials = EncryptedCharField(
        validators=[RegexValidator(
            regex=r'^[A-Z]{2,3}$',
            message=('Ensure initials consist of letters '
                     'only in upper case, no spaces.'))],
        help_text=('Ensure initials consist of letters '
                   'only in upper case, no spaces.'),
        null=True, blank=False)

    screening_identifier = models.CharField(
        verbose_name='Screening identifier',
        max_length=50)

    screened_out = models.BooleanField(
        verbose_name='screened out',
        default=False,
    )

    is_duplicate = models.BooleanField(
        verbose_name='informed consent duplicate',
        default=False,
    )

    consent_datetime = models.DateTimeField(
        verbose_name='Consent date and time',
        default=get_utcnow,
        help_text='Date and time of consent.')

    identity_type = models.CharField(
        verbose_name='What type of identity number is this?',
        max_length=30,
        choices=IDENTITY_TYPE)

    gender = models.CharField(
        verbose_name="Gender",
        choices=GENDER_OTHER,
        max_length=5,
        null=True,
        blank=False)

    optional_sample_collection = models.CharField(
        verbose_name='Do you consent to optional sample storage?',
        choices=YES_NO,
        max_length=3,)

    consent_to_participate = models.CharField(
        verbose_name='Do you consent to participate in the study?',
        choices=YES_NO,
        max_length=3,
        validators=[eligible_if_yes, ],
        help_text='Participant is not eligible if no')

    cohort = models.CharField(
        verbose_name='Cohort enrolled',
        max_length=15,
        null=True, blank=True)

    gender_other = OtherCharField()

    objects = InformedConsentManager()

    consent = ConsentManager()

    on_site = CurrentSiteManager()

    history = HistoricalRecords()

    def __str__(self):
        return f'{self.subject_identifier} V{self.version}'

    def natural_key(self):
        return (self.subject_identifier, self.version)

    def save(self, *args, **kwargs):
        self.version = self.consent_version
        super().save(*args, **kwargs)

    def make_new_identifier(self):
        """Returns a new and unique identifier.

        Override this if needed.
        """
        subject_identifier = SubjectIdentifier(
            identifier_type='subject',
            requesting_model=self._meta.label_lower,
            site=self.site)
        return subject_identifier.identifier

    @property
    def consent_version(self):
        if self.version:
            return self.version
        return '3'

    @property
    def consent_model_cls(self):
        return django_apps.get_model(self.consent_model)

    class Meta(ConsentModelMixin.Meta):
        app_label = 'esr21_subject'
        verbose_name = 'Informed Consent'
        verbose_name_plural = 'Informed Consent'
        unique_together = (
            ('subject_identifier', 'version'),
            ('subject_identifier', 'screening_identifier', 'version'),
            ('subject_identifier', 'first_name', 'dob', 'initials', 'version'))
