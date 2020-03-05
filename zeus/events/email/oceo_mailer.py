import logging

from hermes.messenger import send_mail

from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event
from zeus.persist.notification_timeouts import Throttle


class OCEOMailer(Mailer):
    RECIPIENTS = 'recipients'

    def __init__(self, app_settings):
        super(OCEOMailer, self).__init__(app_settings)
        self._logger = logging.getLogger(__name__)
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)
        self.testing_email_address = [app_settings.NON_PROD_EMAIL_ADDRESS] if self.env != 'prod' else []

    def send_termination_email(self, ticket_id, account_number, domain, malicious_activity):
        """
        Sends an email to oceo@godadddy.com to terminate a customer associated with an intentionally malicious incident
        :param ticket_id:
        :param account_number:
        :param domain:
        :param malicious_activity:
        :return:
        """
        template = 'oceo.shopper_termination'

        message_type = 'oceo_shopper_termination'
        exception_type = 'oceo_shopper_termination_exception'
        success_message = 'oceo_shopper_termination_email_sent'

        kwargs = {'env': self.env}

        try:
            if self._throttle.can_shopper_termination_email_be_sent(domain):
                substitution_values = {'ACCOUNT_NUMBER': account_number,
                                       'DOMAIN': domain,
                                       'MALICIOUS_ACTIVITY': malicious_activity}
                kwargs[self.RECIPIENTS] = self.testing_email_address
                send_mail(template, substitution_values, **kwargs)
                generate_event(ticket_id, success_message)
        except Exception as e:
            self._logger.error('Unable to send {} for {}: {}'.format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True
