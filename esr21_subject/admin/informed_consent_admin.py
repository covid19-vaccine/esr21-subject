from collections import OrderedDict
from django.contrib import admin, messages
from django.apps import apps as django_apps

from django_revision.modeladmin_mixin import ModelAdminRevisionMixin
from django.urls.base import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils.safestring import mark_safe
from edc_consent.actions import (flag_as_verified_against_paper,
                                 unflag_as_verified_against_paper)
from edc_model_admin import (
    ModelAdminFormAutoNumberMixin, ModelAdminInstitutionMixin,
    audit_fieldset_tuple, audit_fields, ModelAdminNextUrlRedirectMixin,
    ModelAdminNextUrlRedirectError, ModelAdminReplaceLabelTextMixin,
    ModelAdminFormInstructionsMixin, ModelAdminAuditFieldsMixin)
from edc_model_admin import ModelAdminBasicMixin, ModelAdminReadOnlyMixin
from simple_history.admin import SimpleHistoryAdmin

from .exportaction_mixin import ExportActionMixin
from ..forms import InformedConsentForm
from ..models import InformedConsent
from .modeladmin_mixins import VersionControlMixin
from ..admin_site import esr21_subject_admin


class ModelAdminMixin(ModelAdminNextUrlRedirectMixin, ModelAdminFormAutoNumberMixin,
                      ModelAdminRevisionMixin, ModelAdminReplaceLabelTextMixin,
                      ModelAdminInstitutionMixin, ModelAdminReadOnlyMixin,
                      VersionControlMixin, ModelAdminFormInstructionsMixin,
                      ModelAdminAuditFieldsMixin, ExportActionMixin):

    list_per_page = 10
    date_hierarchy = 'modified'
    empty_value_display = '-'
    enable_nav_sidebar = False

    def redirect_url(self, request, obj, post_url_continue=None):
        redirect_url = super().redirect_url(
            request, obj, post_url_continue=post_url_continue)
        if request.GET.dict().get('next'):
            url_name = request.GET.dict().get('next').split(',')[0]
            attrs = request.GET.dict().get('next').split(',')[1:]
            options = {k: request.GET.dict().get(k) for k in attrs if request.GET.dict().get(k)}
            try:
                redirect_url = reverse(url_name, kwargs=options)
            except NoReverseMatch as e:
                raise ModelAdminNextUrlRedirectError(
                    f'{e}. Got url_name={url_name}, kwargs={options}.')
        return redirect_url

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['form_version'] = self.get_form_version(request)

        return super().add_view(
            request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):

        extra_context = extra_context or {}

        extra_context['form_version'] = self.get_form_version(request)

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    @property
    def consent_model_cls(self):
        return django_apps.get_model('esr21_subject.informedconsent')


@admin.register(InformedConsent, site=esr21_subject_admin)
class InformedConsentAdmin(ModelAdminBasicMixin, ModelAdminMixin,
                           SimpleHistoryAdmin, admin.ModelAdmin):
    form = InformedConsentForm

    fieldsets = (
        (None, {
            'fields': (
                'screening_identifier',
                'subject_identifier',
                'consent_datetime',
                'first_name',
                'last_name',
                'initials',
                'language',
                'is_literate',
                'witness_name',
                'gender',
                'gender_other',
                'dob',
                'is_dob_estimated',
                'identity',
                'identity_type',
                'confirm_identity',
                'consent_to_participate',
                'optional_sample_collection',
                'version',
                'cohort'
            ),
        }),
        ('Review Questions', {
            'fields': (
                'consent_reviewed',
                'study_questions',
                'assessment_score',
                'consent_signature',
                'consent_copy'),
            'description': 'The following questions are directed to the interviewer.'}),
        audit_fieldset_tuple
    )

    radio_fields = {
        'language': admin.VERTICAL,
        'is_literate': admin.VERTICAL,
        'gender': admin.VERTICAL,
        'identity_type': admin.VERTICAL,
        'is_dob_estimated': admin.VERTICAL,
        'optional_sample_collection': admin.VERTICAL,
        'consent_to_participate': admin.VERTICAL,
        'consent_reviewed': admin.VERTICAL,
        'study_questions': admin.VERTICAL,
        'assessment_score': admin.VERTICAL,
        'consent_signature': admin.VERTICAL,
        'consent_copy': admin.VERTICAL
    }

    list_display = ('subject_identifier',
                    'verified_by',
                    'is_verified',
                    'is_verified_datetime',
                    'first_name',
                    'initials',
                    'gender',
                    'dob',
                    'consent_datetime',
                    'created',
                    'modified',
                    'user_created',
                    'user_modified')

    search_fields = ('subject_identifier', 'dob',)

    def get_actions(self, request):
        super_actions = super().get_actions(request)

        if ('esr21_subject.change_informedconsent'
                in request.user.get_group_permissions()):

            consent_actions = [
                flag_as_verified_against_paper,
                unflag_as_verified_against_paper,
                update_screened_out]

            # Add actions from this ModelAdmin.
            actions = (self.get_action(action) for action in consent_actions)
            # get_action might have returned None, so filter any of those out.
            actions = filter(None, actions)

            actions = self._filter_actions_by_permissions(request, actions)
            # Convert the actions into an OrderedDict keyed by name.
            actions = OrderedDict(
                (name, (func, name, desc))
                for func, name, desc in actions
            )

            super_actions.update(actions)

        return super_actions

    def get_readonly_fields(self, request, obj=None):
        return super().get_readonly_fields(request, obj=obj) + audit_fields + ('version', 'cohort', )

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context.update({
            'show_save': True,
            'show_save_and_continue': False,
            'show_save_and_add_another': False,
            'show_delete': True
        })
        return super().render_change_form(request, context, add, change, form_url, obj)

    def add_view(self, request, form_url='', extra_context=None):
        subject_identifier = request.GET.dict().get('subject_identifier')
        if extra_context:
            extra_context.update({
                'subject_identifier': subject_identifier,
                })

        else:
            extra_context = {
                'subject_identifier': subject_identifier,
            }
        extra_context = self.update_add_instructions(extra_context)
        return super().add_view(
            request, form_url=form_url, extra_context=extra_context)

    def update_add_instructions(self, extra_context):
        consent = None
        message = ''
        subject_identifier = extra_context.get('subject_identifier')
        try:
            consent = self.consent_model_cls.objects.get(
                subject_identifier=subject_identifier)
        except self.consent_model_cls.DoesNotExist:
            pass
        else:
            message = f'Participant has previously consented for version {consent.version} <br>'
        additional_instructions = mark_safe(
                f'{message} Please complete the questions below. Required questions are in bold. '
                'When all required questions are complete click SAVE. <br> Based on your '
                'responses, additional questions may be required or some answers may '
                'need to be corrected.<br>')
        extra_context['additional_instructions'] = additional_instructions
        return extra_context


def update_screened_out(modeladmin, request, queryset, **kwargs):
    for consent_obj in queryset:
        consent_obj.screened_out = True
        consent_obj.save()
        messages.add_message(
            request,
            messages.SUCCESS,
            f'\'{consent_obj._meta.verbose_name}\' for \' '
            f'{consent_obj.subject_identifier}\' '
            f'has been verified as screening failure')
