import logging

from hermes.messenger import send_mail

from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event
from zeus.utils.functions import sanitize_url


class ForeignMailer(Mailer):
    def __init__(self, app_settings):
        super(ForeignMailer, self).__init__(app_settings)
        self._logger = logging.getLogger('celery.tasks')
        self.testing_email_address = [{'email': app_settings.NON_PROD_EMAIL_ADDRESS}] if self.env != 'prod' else []

    def send_foreign_hosting_notice(self, ticket_id, domain, source, hosting_brand, recipients,
                                    ip_address='Unable to ascertain IP Address'):
        """
        Sends a notification to the abuse contact address found for foreign providers
        success_message = 'hosting_abuse_notice_email_sent', 'template': 3103
        :param ticket_id:
        :param domain:
        :param source:
        :param hosting_brand:
        :param recipients: list of email addresses
        :param ip_address:
        :return:
        """
        if hosting_brand in ['GODADDY', 'EMEA'] or not recipients:
            return False

        template = 'foreign.hosting_abuse_notice'
        message_type = 'hosting_abuse_notice'
        exception_type = 'hosting_abuse_notice_email_exception'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            substitution_values = {'DOMAIN': domain,
                                   'SANITIZED_URL': sanitize_url(source),
                                   'IPADDRESS': ip_address}

            for email in recipients:
                kwargs['recipients'] = self.testing_email_address or [{'email': email}]
                send_mail(template, substitution_values, **kwargs)
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True
