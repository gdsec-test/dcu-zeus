import logging

from hermes.messenger import send_mail

from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event
from zeus.persist.notification_timeouts import Throttle


class SSLMailer(Mailer):
    RECIPIENTS = 'recipients'

    def __init__(self, app_settings):
        super(SSLMailer, self).__init__(app_settings)
        self._logger = logging.getLogger(__name__)
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)
        self.testing_email_address = [app_settings.NON_PROD_EMAIL_ADDRESS] if self.env != 'prod' else []

    def send_revocation_email(self, ticket_id, domain, shopper_id, ssl_subscriptions):
        """
        Sends an email to practices@godadddy.com to revoke the ssl certificate associated with a malicious domain
        success_message = 'cert_authority_ssl_revocation_email_sent'
        :param ticket_id
        :param domain:
        :param shopper_id:
        :param ssl_subscriptions
        :return:
        """
        template = 'ssl.revocation'
        cert_template = 'Common Name: {certCommonName}, Created Date: {createdAt}, Expiration Date: {expiresAt}\n'
        message_type = 'cert_authority_ssl_revocation'
        exception_type = 'cert_authority_ssl_revocation_exception'

        kwargs = {'env': self.env}

        '''
        Return if there are no ssl certificates associated with the domain.
        Also return if the ticket does not contain both shopper and domain
        '''
        try:
            if self._throttle.can_ssl_revocation_email_be_sent(domain):
                cert_details = ''
                for idx, ssl_subscription in enumerate(ssl_subscriptions):
                    cert_details += '{}) {}'.format(idx + 1, cert_template.format(**ssl_subscription))
                substitution_values = {'SHOPPER': shopper_id, 'CERT_DETAILS': cert_details}
                kwargs[self.RECIPIENTS] = self.testing_email_address
                send_mail(template, substitution_values, **kwargs)
        except Exception as e:
            self._logger.error('Unable to send {} for {}: {}'.format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True
