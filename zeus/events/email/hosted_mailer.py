import logging

from hermes.messenger import send_mail

from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event
from zeus.persist.notification_timeouts import Throttle
from zeus.utils.functions import sanitize_url


class HostedMailer(Mailer):
    def __init__(self, app_settings):
        super(HostedMailer, self).__init__(app_settings)
        self._logger = logging.getLogger('celery.tasks')
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)
        self._CAN_FLOOD = app_settings.CAN_FLOOD

    def send_hosted_warning(self, ticket_id, domain, shopper_id, source):
        """
        Sends a notification to the shopper account email address found for the hosted domain
        success_message = 'hosted_shopper_warning_email_sent', 'template': 3996
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param source:
        :return:
        """

        template = 'hosted.suspension_warning'
        message_type = 'hosted_24hr_warning'
        exception_type = 'hosted_shopper_warning_email_exception'

        redis_key = f'{domain}_warning_email'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain,
                                       'MALICIOUS_CONTENT_REPORTED': sanitize_url(source)}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_sucuri_hosted_warning(self, ticket_id, domain, shopper_id, source):
        """
        Sends a notification to the shopper account email address found for the hosted domain
        success_message = 'hosted_sucuri_shopper_warning_email_sent', 'template': 6041
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param source:
        :return:
        """

        template = 'hosted.sucuri_warning'
        message_type = 'hosted_sucuri_72hr_warning'
        exception_type = 'hosted_sucuri_warning_email_exception'

        redis_key = f'{domain}_sucuri_warning_email'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain,
                                       'SANITIZED_URL': sanitize_url(source)}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_content_removed(self, ticket_id, domain, shopper_id):
        """
        Sends a notification to the shopper account email address found for the hosted domain regarding
        content that was removed
        success_message = 'hosted_content_removed_notice_email_sent', 'template': 3994
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :return:
        """

        template = 'hosted.content_removed'
        message_type = 'hosted_content_removed_notice'
        exception_type = 'hosted_content_removed_notice_email_exception'

        redis_key = f'{domain}_cleaned_email'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_repeat_offender(self, ticket_id, domain, shopper_id, source):
        """
        Sends a notification to the shopper account email address found for the hosted domain regarding
        action taken due to repeat hosting offenses
        success_message = 'hosted_repeat_offender_email_sent', 'template': 4807
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param source:
        :return:
        """

        template = 'hosted.repeat_offender'
        message_type = 'hosted_repeat_offender'
        exception_type = 'hosted_repeat_offender_email_exception'

        redis_key = f'{domain}_repeat_offender'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain,
                                       'SANITIZED_URL': sanitize_url(source)}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_shopper_hosted_suspension(self, ticket_id, domain, shopper_id, source):
        """
        Sends a notification to the shopper account email address found for the hosting account
        success_message = 'hosted_shopper_suspend_notice_email_sent', 'template': 3998
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param source:
        :return:
        """

        template = 'hosted.suspend'
        message_type = 'hosted_shopper_suspend_notice'
        exception_type = 'hosted_shopper_suspend_email_exception'

        redis_key = f'{domain}_suspended_email'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain,
                                       'MALICIOUS_CONTENT_REPORTED': sanitize_url(source)}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_shopper_hosted_intentional_suspension(self, ticket_id, domain, shopper_id, report_type):
        """
        Sends a notification to the shopper account email address found for the hosting account
        success_message = 'hosted_shopper_suspend_intentional_notice_email_sent', 'template': 4046
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param report_type:
        :return:
        """

        template = 'hosted.suspend_intentionally_malicious'
        message_type = 'hosted_shopper_suspend_intentional_notice'
        exception_type = 'hosted_shopper_suspend_intentional_email_exception'

        redis_key = f'{domain}_intentional_suspended_email'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain,
                                       'MALICIOUS_ACTIVITY': report_type}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_shopper_compromise_hosted_suspension(self, ticket_id, domain, shopper_id):
        """
        Sends a notification to the shopper account email address found for the hosting account
        success_message = 'hosted_shopper_compromise_suspend_notice_email_sent', 'template': 5282
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :return:
        """

        template = 'hosted.suspend_shopper_compromise'
        message_type = 'hosted_shopper_compromise_suspend_notice'
        exception_type = 'hosted_shopper_compromise_suspend_email_exception'

        redis_key = f'{domain}_compromise_suspended_email'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_extensive_compromise(self, ticket_id, domain, shopper_id):
        """
        Sends a notification to the shopper account email address found for the hosting account regarding
        action taken due to extensive compromise
        success_message = 'hosted_extensive_compromise_email_sent', 'template': 4809
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :return:
        """

        template = 'hosted.extensive_compromise'
        message_type = 'hosted_extensive_compromise'
        exception_type = 'hosted_extensive_compromise_email_exception'

        redis_key = f'{domain}_extensive_compromise'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_csam_hosted_suspension(self, ticket_id, domain, shopper_id):
        """
        Sends a notification to the shopper account email address found for the hosting account
        success_message = 'hosted_shopper_suspend_CSAM_notice_email_sent', 'template': 5722
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :return:
        """

        template = 'csam.suspend'
        message_type = 'hosted_shopper_suspend_CSAM_notice'
        exception_type = 'hosted_shopper_suspend_CSAM_email_exception'

        redis_key = f'{domain}_suspended_email'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain}

                send_mail(template, substitution_values, **self.generate_kwargs_for_hermes())
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True
