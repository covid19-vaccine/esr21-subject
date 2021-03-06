from django.apps import apps as django_apps
from dateutil.relativedelta import relativedelta
from django.core.exceptions import ObjectDoesNotExist
from edc_constants.constants import YES
from edc_visit_schedule.site_visit_schedules import site_visit_schedules


class EnrollmentHelper(object):

    def __init__(self, cohort=None, subject_identifier=None):
        self.cohort = cohort
        self.subject_identifier = subject_identifier
        self.vaccination_history_model = 'esr21_subject.vaccinationhistory'

    @property
    def vaccination_history_model_cls(self):
        return django_apps.get_model(self.vaccination_history_model)

    def schedule_enrol(self):
        onschedule_model = 'esr21_subject.onschedule'
        try:
            vaccination_history = self.vaccination_history_model_cls.objects.get(
                subject_identifier=self.subject_identifier)
        except ObjectDoesNotExist:
            pass
        else:
            onschedule_dt = vaccination_history.created.replace(microsecond=0)
            if vaccination_history.received_vaccine == YES:
                if vaccination_history.dose_quantity == '1':
                    self.put_on_schedule(
                        f'{self.cohort}_fu_schedule3',
                        onschedule_model=onschedule_model,
                        base_appt_datetime=onschedule_dt,
                        onschedule_datetime=onschedule_dt)

                    booster_dt = vaccination_history.created + relativedelta(days=100)
                    self.put_on_schedule(
                        f'{self.cohort}_boost_schedule',
                        onschedule_model=onschedule_model,
                        base_appt_datetime=booster_dt.replace(microsecond=0),
                        onschedule_datetime=onschedule_dt)

                elif vaccination_history.dose_quantity == '2':
                    self.put_on_schedule(
                        f'{self.cohort}_boost_schedule',
                        onschedule_model=onschedule_model,
                        base_appt_datetime=onschedule_dt,
                        onschedule_datetime=onschedule_dt)
            else:
                self.put_on_schedule(
                    f'{self.cohort}_enrol_schedule3',
                    onschedule_model=onschedule_model,
                    base_appt_datetime=onschedule_dt,
                    onschedule_datetime=onschedule_dt)

                # Schedule second dose, 70days after dose 1 schedule
                second_dose_dt = vaccination_history.created + relativedelta(days=70)
                self.put_on_schedule(
                    f'{self.cohort}_fu_schedule3',
                    onschedule_model=onschedule_model,
                    base_appt_datetime=second_dose_dt.replace(microsecond=0),
                    onschedule_datetime=onschedule_dt)

                # Schedule booster, 170days after dose 1 schedule
                booster_dt = vaccination_history.created + relativedelta(days=170)
                self.put_on_schedule(
                    f'{self.cohort}_boost_schedule',
                    onschedule_model=onschedule_model,
                    base_appt_datetime=booster_dt.replace(microsecond=0),
                    onschedule_datetime=onschedule_dt)

    def put_on_schedule(self, schedule_name, onschedule_model,
                        base_appt_datetime=None, onschedule_datetime=None):
        _, schedule = site_visit_schedules.get_by_onschedule_model_schedule_name(
            onschedule_model=onschedule_model, name=schedule_name)
        schedule.put_on_schedule(
            subject_identifier=self.subject_identifier,
            onschedule_datetime=onschedule_datetime,
            base_appt_datetime=base_appt_datetime,
            schedule_name=schedule_name)
