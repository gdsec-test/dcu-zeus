import logging

from hermes.messenger import send_mail

from settings import config_by_name
from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event
from zeus.persist.persist import Persist


class FraudMailer(Mailer):
    fraud_email = [{'email': 'ccinquiries@godaddy.com'}]  # Updated from verifypayment@ (requested by Sarah Neiswonger)
    RECIPIENTS = 'recipients'

    def __init__(self, app_settings):
        super(FraudMailer, self).__init__(app_settings)
        self._logger = logging.getLogger(__name__)
        self._throttle = Persist(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)
        self.testing_email_address = [
            {'email': config_by_name[self.env].NON_PROD_EMAIL_ADDRESS}] if self.env != 'prod' else []

    def send_new_domain_notification(self, ticket_id, domain, shopper_id, domain_create_date, report_type, source,
                                     target='Unknown Brand'):
        """
        Sends a potentially fraudulent new domain to fraud
        :param shopper_id:
        :param domain_create_date:
        :param report_type:
        :param source:
        :param target:
        :param domain:
        :param ticket_id:
        :return:
        """
        template = 'fraud.new_domain_registration'

        message_type = 'fraud_new_domain_registration'
        exception_type = 'fraud_new_domain_registration_email_exception'
        success_message = 'fraud_new_domain_registration_email_sent'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_fraud_email_be_sent(domain):
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN_CREATION_DATE': str(domain_create_date),
                                       'DOMAIN': domain,
                                       'MALICIOUS_ACTIVITY': report_type,
                                       'BRAND_TARGETED': target,
                                       'SANITIZED_URL': self.sanitize_url(source)}

                kwargs[self.RECIPIENTS] = self.testing_email_address or self.fraud_email
                resp = send_mail(template, substitution_values, **kwargs)
                resp.update({'type': message_type, 'template': 3716})
                generate_event(ticket_id, success_message, **resp)
                return True
        except Exception as e:
            self._logger.error('Unable to send {} for {}: {}'.format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
        return False

    def send_new_shopper_notification(self, ticket_id, domain, shopper_id, shopper_create_date, report_type, source,
                                      target='Unknown Brand'):
        """
        Sends a potentially fraudulent new shopper to fraud
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param shopper_create_date:
        :param report_type:
        :param source:
        :param target:
        :return:
        """
        template = 'fraud.new_shopper_account'

        message_type = 'fraud_new_shopper_account'
        exception_type = 'fraud_new_shopper_account_email_exception'
        success_message = 'fraud_new_shopper_account_email_sent'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_fraud_email_be_sent(domain):
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'SHOPPER_CREATION_DATE': str(shopper_create_date),
                                       'DOMAIN': domain,
                                       'MALICIOUS_ACTIVITY': report_type,
                                       'BRAND_TARGETED': target,
                                       'SANITIZED_URL': self.sanitize_url(source)}

                kwargs[self.RECIPIENTS] = self.testing_email_address or self.fraud_email
                resp = send_mail(template, substitution_values, **kwargs)
                resp.update({'type': message_type, 'template': 3693})
                generate_event(ticket_id, success_message, **resp)
                return True
        except Exception as e:
            self._logger.error('Unable to send {} for {}: {}'.format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
        return False

    def send_malicious_domain_notification(self, ticket_id, domain, shopper_id, report_type, source,
                                           target='Unknown Brand'):
        """
        Sends a malicious notification to fraud
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param report_type:
        :param source:
        :param target:
        :return:
        """
        template = 'fraud.intentionally_malicious_domain'

        message_type = 'fraud_intentionally_malicious_domain'
        exception_type = 'fraud_intentionally_malicious_domain_email_exception'
        success_message = 'fraud_intentionally_malicious_domain_email_sent'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_fraud_email_be_sent(domain):
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain,
                                       'MALICIOUS_ACTIVITY': report_type,
                                       'BRAND_TARGETED': target,
                                       'SANITIZED_URL': self.sanitize_url(source)}

                kwargs[self.RECIPIENTS] = self.testing_email_address or self.fraud_email
                resp = send_mail(template, substitution_values, **kwargs)
                resp.update({'type': message_type, 'template': 3694})
                generate_event(ticket_id, success_message, **resp)
                return True
        except Exception as e:
            self._logger.error('Unable to send {} for {}: {}'.format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
        return False

    def send_new_hosting_account_notification(self, ticket_id, domain, shopper_id, account_create_date, report_type,
                                              source, target='Unknown Brand'):
        """
        Sends a potentially fraudulent new hosting account to fraud.
        This template utilizes a variation of the New Shopper Account template.
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param account_create_date:
        :param report_type:
        :param source:
        :param target:
        :return:
        """
        template = 'fraud.new_shopper_account'

        message_type = 'fraud_new_hosting_account'
        exception_type = 'fraud_new_hosting_account_email_exception'
        success_message = 'fraud_new_hosting_account_email_sent'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_fraud_email_be_sent(domain):
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'SHOPPER_CREATION_DATE': str(account_create_date),
                                       'DOMAIN': domain,
                                       'MALICIOUS_ACTIVITY': report_type,
                                       'BRAND_TARGETED': target,
                                       'SANITIZED_URL': self.sanitize_url(source)}

                kwargs[self.RECIPIENTS] = self.testing_email_address or self.fraud_email
                resp = send_mail(template, substitution_values, **kwargs)
                resp.update({'type': message_type, 'template': 3693})
                generate_event(ticket_id, success_message, **resp)
                return True
        except Exception as e:
            self._logger.error('Unable to send {} for {}: {}'.format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
        return False

    def send_malicious_hosting_notification(self, ticket_id, domain, shopper_id, guid, source, report_type,
                                            target='Unknown Brand'):
        """
        Sends a malicious notification to fraud
        Using DMV Fraud template; DOMAIN = item reported to Fraud (guid here, for hosting)
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param guid:
        :param source:
        :param report_type:
        :param target:
        :return:
        """
        template = 'fraud.intentionally_malicious_domain'

        message_type = 'fraud_intentionally_malicious_domain'
        exception_type = 'fraud_intentionally_malicious_domain_email_exception'
        success_message = 'fraud_intentionally_malicious_domain_email_sent'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_fraud_email_be_sent(domain):
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': guid,  # Template requires DOMAIN param
                                       'MALICIOUS_ACTIVITY': report_type,
                                       'BRAND_TARGETED': target,
                                       'SANITIZED_URL': self.sanitize_url(source)}

                kwargs[self.RECIPIENTS] = self.testing_email_address or self.fraud_email
                resp = send_mail(template, substitution_values, **kwargs)
                resp.update({'type': message_type, 'template': 3694})
                generate_event(ticket_id, success_message, **resp)
                return True
        except Exception as e:
            self._logger.error('Unable to send {} for {}: {}'.format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
        return False
