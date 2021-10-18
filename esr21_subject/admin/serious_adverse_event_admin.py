from django.contrib import admin
from edc_model_admin.inlines import StackedInlineMixin
from edc_model_admin import audit_fieldset_tuple
from .modeladmin_mixins import CrfModelAdminMixin
from ..forms import SeriousAdverseEventForm, SeriousAdverseEventRecordForm
from ..models import SeriousAdverseEventRecord, SeriousAdverseEvent
from ..admin_site import esr21_subject_admin


class SeriousAdverseEventRecordInlineAdmin(StackedInlineMixin, admin.StackedInline):
    model = SeriousAdverseEventRecord
    form = SeriousAdverseEventRecordForm

    extra = 0
    max_num = 3

    fieldsets = (
        (None, {
            'fields': [
                'sae_name',
                'meddra_pname',
                'meddra_pcode',
                'meddra_version',
                'sae_details',
                'sae_intensity',
                'start_date',
                'resolution_date',
                'date_aware_of',
                'seriousness_criteria',
                'admission_date',
                'discharge_date',
                'incapacity_specify',
                'medical_event_other',
                'rationale',
                'describe_sae_treatmnt',
                'test_performed',
                'additional_info',
                'ae_number',
                'ae_term',
                'aes_dat',
                'ae_siadat',
                'dthcaus_1',
                'dthcaus_2',
                'ad',
                'ae_caad',
                'ae_smedca',
                'ae_smed',
                'ae_caussp',
                'ae_sp',
                'ae_sdth',
                'ae_shosp',
                'ae_scong',
                'ae_slife',
                'ae_sdisab',
                'ae_smie',
                'ae_shodat',
                'ae_sautop'
            ]}
        ),)

    radio_fields = {
        'sae_intensity': admin.VERTICAL,
        'ae_sdth':       admin.VERTICAL,
        'ae_shosp':      admin.VERTICAL,
        'ae_scong':      admin.VERTICAL,
        'ae_slife':      admin.VERTICAL,
        'ae_sdisab':     admin.VERTICAL,
        'ae_smie':       admin.VERTICAL,
        'ae_shodat':     admin.VERTICAL,
        'ae_sautop':     admin.VERTICAL,
        }

    filter_horizontal = ('seriousness_criteria',)


@admin.register(SeriousAdverseEvent, site=esr21_subject_admin)
class SeriousAdverseEventAdmin(CrfModelAdminMixin, admin.ModelAdmin):
    form = SeriousAdverseEventForm
    inlines = [SeriousAdverseEventRecordInlineAdmin, ]

    fieldsets = (
        (None, {
            'fields': (
                'subject_visit',
                'report_datetime',
            )
        }),
        audit_fieldset_tuple
    )

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context.update({
            'show_save': True,
            'show_save_and_continue': False,
            'show_save_and_add_another': False,
            'show_delete': True
        })
        return super().render_change_form(request, context, add, change, form_url, obj)
