import logging

from hermes.messenger import send_mail

from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event
from zeus.persist.notification_timeouts import Throttle


class UtilityMailer(Mailer):
    def __init__(self, app_settings):
        super(UtilityMailer, self).__init__(app_settings)
        self._logger = logging.getLogger('celery.tasks')
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)
        self._CAN_FLOOD = app_settings.CAN_FLOOD

    def send_account_compromised_email(self, shopper_id: int) -> bool:
        # Sends an OCM template 5282 to impacted shoppers regarding possible account compromise

        template = 'hosted.suspend_shopper_compromise'
        message_type = 'shopper_compromise_email'
        exception_type = 'shopper_compromise_email_exception'

        redis_key = f'{shopper_id}_shopper_compromise_email'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())

            else:
                self._logger.warning(f'Cannot send {template} for {shopper_id}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {shopper_id}: {e}')
            generate_event(shopper_id, exception_type, type=message_type)
            return False
        return True

    def send_pci_compliance_violation(self, shopper_id: int, domain: str) -> bool:
        # Sends an OCM template 6471 to hosted shoppers regarding pci compliance violations

        template = 'hosted.suspend_pci_compliance'
        message_type = 'pci_compliance_email'
        exception_type = 'pci_compliance_email_exception'

        redis_key = f'{domain}_pci_compliance_email'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())

            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(domain, exception_type, type=message_type)
            return False
        return True
