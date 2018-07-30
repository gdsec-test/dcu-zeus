import logging

from hermes.messenger import send_mail

from settings import config_by_name
from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event
from zeus.persist.notification_timeouts import Throttle
from zeus.utils.functions import sanitize_url


class RegisteredMailer(Mailer):
    def __init__(self, app_settings):
        super(RegisteredMailer, self).__init__(app_settings)
        self._logger = logging.getLogger(__name__)
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)
        self._CAN_FLOOD = app_settings.CAN_FLOOD
        self.testing_email_address = [
            {'email': config_by_name[self.env].NON_PROD_EMAIL_ADDRESS}] if self.env != 'prod' else []

    def send_registrant_warning(self, ticket_id, domain, shopper_ids, source):
        """
        Sends a notification to the shopper account email address found for the domain
        :param ticket_id:
        :param domain:
        :param shopper_ids:
        :param source:
        :return:
        """
        if not shopper_ids:
            return False

        template = "registered.suspension_warning"

        message_type = "reg-only_24hr_warning"
        exception_type = "reg-only_shopper_warning_email_exception"
        success_message = "reg-only_shopper_warning_email_sent"

        try:
            if self._throttle.can_shopper_email_be_sent(domain) or self._CAN_FLOOD:

                # If the domain is associated with a parent/child API reseller
                #  account, then email both the parent and child account
                for shopper_id in shopper_ids:
                    substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                           'DOMAIN': domain,
                                           'SANITIZED_URL': sanitize_url(source)}

                    resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                    resp.update(
                        {'type': message_type, 'template': 3132})  # template provided for backwards compatibility
                    generate_event(ticket_id, success_message, **resp)
                return True
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
        return False

    def send_shopper_suspension(self, ticket_id, domain, shopper_ids, source, report_type):
        """
        Sends a suspension notification to the shopper account email address found for the domain
        :param ticket_id:
        :param domain:
        :param shopper_ids:
        :param source:
        :param report_type:
        :return:
        """
        if not shopper_ids:
            return False

        template = "registered.suspend"

        message_type = "reg-only_domain_suspension"
        exception_type = "reg-only_shopper_suspend_email_exception"
        success_message = "reg-only_shopper_suspend_email_sent"

        try:
            if self._throttle.can_shopper_email_be_sent(domain) or self._CAN_FLOOD:

                # If the domain is associated with a parent/child API reseller
                #  account, then email both the parent and child account
                for shopper_id in shopper_ids:
                    substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                           'DOMAIN': domain,
                                           'SANITIZED_URL': sanitize_url(source),
                                           'MALICIOUS_ACTIVITY': report_type}

                    resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                    resp.update(
                        {'type': message_type, 'template': 3760})  # template provided for backwards compatibility
                    generate_event(ticket_id, success_message, **resp)
                return True
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
        return False

    def send_shopper_intentional_suspension(self, ticket_id, domain, shopper_ids, report_type):
        """
        Sends an intentional suspension notification to the shopper account email address found for the domain
        :param ticket_id:
        :param domain:
        :param shopper_ids:
        :param report_type:
        :return:
        """
        if not shopper_ids:
            return False

        template = "registered.suspend_intentionally_malicious"

        message_type = "reg-only_domain_suspension_intentional"
        exception_type = "reg-only_shopper_suspend_intentional_email_exception"
        success_message = "reg-only_shopper_suspend_intentional_email_sent"

        try:
            if self._throttle.can_shopper_email_be_sent(domain) or self._CAN_FLOOD:

                # If the domain is associated with a parent/child API reseller
                #  account, then email both the parent and child account
                for shopper_id in shopper_ids:
                    substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                           'DOMAIN': domain,
                                           'MALICIOUS_ACTIVITY': report_type}

                    resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                    resp.update(
                        {'type': message_type, 'template': 4044})  # template provided for backwards compatibility
                    generate_event(ticket_id, success_message, **resp)
                return True
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
        return False

    def send_hosting_provider_notice(self, ticket_id, domain, source, hosting_brand, recipients,
                                     ip_address="Unable to ascertain IP Address"):
        """
        Sends a notification to the abuse contact address found for the 3rd party hosting provider of registered domain
        :param ticket_id:
        :param domain:
        :param source:
        :param hosting_brand:
        :param recipients:
        :param ip_address:
        :return:
        """
        if hosting_brand in ['GODADDY', 'EMEA']:
            return False

        if not recipients:
            return False

        template = "foreign.hosting_abuse_notice"

        message_type = "hosting_abuse_notice"
        exception_type = "hosting_abuse_notice_email_exception"
        success_message = "hosting_abuse_notice_email_sent"

        kwargs = self.generate_kwargs_for_hermes()

        try:
            substitution_values = {'DOMAIN': domain,
                                   'SANITIZED_URL': sanitize_url(source),
                                   'IPADDRESS': ip_address}

            for email in recipients:
                if email and any(x in email.lower() for x in ['abuse', 'noc']):
                    kwargs['recipients'] = self.testing_email_address or [{'email': email}]
                    resp = send_mail(template, substitution_values, **kwargs)
                    resp.update({'type': message_type, 'template': 3103})
                    generate_event(ticket_id, success_message, **resp)
            return True
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
        return False
