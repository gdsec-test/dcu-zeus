import logging

from hermes.messenger import send_mail

from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event
from zeus.persist.notification_timeouts import Throttle
from zeus.utils.functions import sanitize_url


class HostedMailer(Mailer):
    def __init__(self, app_settings):
        super(HostedMailer, self).__init__(app_settings)
        self._logger = logging.getLogger(__name__)
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)
        self._CAN_FLOOD = app_settings.CAN_FLOOD

    def send_hosted_warning(self, ticket_id, domain, shopper_id, source):
        """
        Sends a notification to the shopper account email address found for the hosted domain
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param source:
        :return:
        """

        template = "hosted.suspension_warning"

        message_type = "hosted_24hr_warning"
        exception_type = "hosted_shopper_warning_email_exception"
        success_message = "hosted_shopper_warning_email_sent"

        redis_key = "{}_warning_email".format(domain)

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain,
                                       'MALICIOUS_CONTENT_REPORTED': sanitize_url(source)}

                resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                resp.update({'type': message_type, 'template': 3996})
                generate_event(ticket_id, success_message, **resp)
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_content_removed(self, ticket_id, domain, shopper_id):
        """
        Sends a notification to the shopper account email address found for the hosted domain regarding
        content that was removed
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :return:
        """

        template = "hosted.content_removed"

        message_type = "hosted_content_removed_notice"
        exception_type = "hosted_content_removed_notice_email_exception"
        success_message = "hosted_content_removed_notice_email_sent"

        redis_key = "{}_cleaned_email".format(domain)

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain}

                resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                resp.update({'type': message_type, 'template': 3994})
                generate_event(ticket_id, success_message, **resp)
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_repeat_offender(self, ticket_id, domain, shopper_id, source):
        """
        Sends a notification to the shopper account email address found for the hosted domain regarding
        action taken due to repeat hosting offenses
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param source:
        :return:
        """

        template = "hosted.repeat_offender"

        message_type = "hosted_repeat_offender"
        exception_type = "hosted_repeat_offender_email_exception"
        success_message = "hosted_repeat_offender_email_sent"

        redis_key = "{}_repeat_offender".format(domain)

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain,
                                       'SANITIZED_URL': sanitize_url(source)}

                resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                resp.update({'type': message_type, 'template': 4807})
                generate_event(ticket_id, success_message, **resp)
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_shopper_hosted_suspension(self, ticket_id, domain, shopper_id, source):
        """
        Sends a notification to the shopper account email address found for the hosting account
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param source:
        :return:
        """

        template = "hosted.suspend"

        message_type = "hosted_shopper_suspend_notice"
        exception_type = "hosted_shopper_suspend_email_exception"
        success_message = "hosted_shopper_suspend_notice_email_sent"

        redis_key = "{}_suspended_email".format(domain)

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain,
                                       'MALICIOUS_CONTENT_REPORTED': sanitize_url(source)}

                resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                resp.update({'type': message_type, 'template': 3998})
                generate_event(ticket_id, success_message, **resp)
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_shopper_hosted_intentional_suspension(self, ticket_id, domain, shopper_id, report_type):
        """
        Sends a notification to the shopper account email address found for the hosting account
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param report_type:
        :return:
        """

        template = "hosted.suspend_intentionally_malicious"

        message_type = "hosted_shopper_suspend_intentional_notice"
        exception_type = "hosted_shopper_suspend_intentional_email_exception"
        success_message = "hosted_shopper_suspend_intentional_notice_email_sent"

        redis_key = "{}_intentional_suspended_email".format(domain)

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain,
                                       'MALICIOUS_ACTIVITY': report_type}

                resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                resp.update({'type': message_type, 'template': 4046})
                generate_event(ticket_id, success_message, **resp)
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_shopper_compromise_hosted_suspension(self, ticket_id, domain, shopper_id):
        """
        Sends a notification to the shopper account email address found for the hosting account
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :return:
        """

        template = "hosted.suspend_shopper_compromise"

        message_type = "hosted_shopper_compromise_suspend_notice"
        exception_type = "hosted_shopper_compromise_suspend_email_exception"
        success_message = "hosted_shopper_compromise_suspend_notice_email_sent"

        redis_key = "{}_compromise_suspended_email".format(domain)

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id}

                resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                resp.update({'type': message_type, 'template': 5282})
                generate_event(ticket_id, success_message, **resp)
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_extensive_compromise(self, ticket_id, domain, shopper_id):
        """
        Sends a notification to the shopper account email address found for the hosting account regarding
        action taken due to extensive compromise
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :return:
        """

        template = "hosted.extensive_compromise"

        message_type = "hosted_extensive_compromise"
        exception_type = "hosted_extensive_compromise_email_exception"
        success_message = "hosted_extensive_compromise_email_sent"

        redis_key = "{}_extensive_compromise".format(domain)

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain}

                resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                resp.update({'type': message_type, 'template': 4809})
                generate_event(ticket_id, success_message, **resp)
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_csam_hosted_suspension(self, ticket_id, domain, shopper_id):
        """
        Sends a notification to the shopper account email address found for the hosting account
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :return:
        """

        template = "csam.suspend"

        message_type = "hosted_shopper_suspend_CSAM_notice"
        exception_type = "hosted_shopper_suspend_CSAM_email_exception"
        success_message = "hosted_shopper_suspend_CSAM_notice_email_sent"

        redis_key = "{}_suspended_email".format(domain)

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain}

                resp = send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
                resp.update({'type': message_type, 'template': 5722})
                generate_event(ticket_id, success_message, **resp)
            else:
                self._logger.warning("Cannot send {} for {}... still within 24hr window".format(template, domain))
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, domain, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True
