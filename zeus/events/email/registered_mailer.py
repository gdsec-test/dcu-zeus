import logging

from hermes.messenger import send_mail

from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event
from zeus.persist.notification_timeouts import Throttle
from zeus.utils.functions import sanitize_url


class RegisteredMailer(Mailer):
    DOMAIN_ID = 'domain_id'

    def __init__(self, app_settings):
        super(RegisteredMailer, self).__init__(app_settings)
        self._logger = logging.getLogger('celery.tasks')
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)
        self._CAN_FLOOD = app_settings.CAN_FLOOD
        self.testing_email_address = [
            {'email': app_settings.NON_PROD_EMAIL_ADDRESS}] if self.env != 'prod' else []

    def send_user_gen_complaint(self, ticket_id, subdomain, domain_id, shopper_id, source):
        """
        Sends a notice to the shopper and administrative contact email address(es) found for the user generated domain.
        This replaces manual review for these blacklisted Registered Only domains that will never be suspended.
        success_message = 'reg-only_user_gen_email_sent', 'template': 5518
        :param ticket_id:
        :param subdomain:
        :param domain_id:
        :param shopper_id:
        :param source:
        :return:
        """
        if not shopper_id:
            self._logger.info(f'User Generated Notice was not sent for {ticket_id}: No Shopper ID found')
            return False

        template = 'registered.forwarding_complaint'
        message_type = 'forwarded_user_gen_complaint'
        exception_type = 'reg-only_user_gen_email_exception'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_shopper_email_be_sent(subdomain) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'SANITIZED_URL': sanitize_url(source)}

                kwargs[self.DOMAIN_ID] = domain_id
                send_mail(template, substitution_values, **kwargs)
            else:
                self._logger.warning(f'Cannot send {template} for {subdomain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {subdomain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_registrant_warning(self, ticket_id, domain, domain_id, shopper_ids, source):
        """
        Sends a notification to the shopper account and administrative contact email address(es) found for the domain
        success_message = 'reg-only_shopper_warning_email_sent', 'template': 3132
        :param ticket_id:
        :param domain:
        :param domain_id:
        :param shopper_ids:
        :param source:
        :return:
        """
        if not shopper_ids:
            return False

        template = 'registered.suspension_warning'
        message_type = 'reg-only_24hr_warning'
        exception_type = 'reg-only_shopper_warning_email_exception'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_shopper_email_be_sent(domain) or self._CAN_FLOOD:

                # If the domain is associated with a parent/child API reseller
                #  account, then email both the parent and child account
                for shopper_id in shopper_ids:
                    substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                           'DOMAIN': domain,
                                           'SANITIZED_URL': sanitize_url(source)}

                    kwargs[self.DOMAIN_ID] = domain_id
                    send_mail(template, substitution_values, **kwargs)
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_sucuri_reg_warning(self, ticket_id, domain, domain_id, shopper_ids, source):
        """
        Sends a notification to the shopper account and administrative contact email address(es) found for the domain
        success_message = 'reg-only_sucuri_shopper_warning_email_sent', 'template': 6041
        :param ticket_id:
        :param domain:
        :param domain_id:
        :param shopper_ids:
        :param source:
        :return:
        """
        if not shopper_ids:
            return False

        template = 'registered.sucuri_warning'
        message_type = 'reg-only_sucuri_72hr_warning'
        exception_type = 'reg-only_sucuri_warning_email_exception'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_shopper_email_be_sent(domain) or self._CAN_FLOOD:

                # If the domain is associated with a parent/child API reseller
                #  account, then email both the parent and child account
                for shopper_id in shopper_ids:
                    substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                           'DOMAIN': domain,
                                           'SANITIZED_URL': sanitize_url(source)}

                    kwargs[self.DOMAIN_ID] = domain_id
                    send_mail(template, substitution_values, **kwargs)
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_repeat_offender_suspension(self, ticket_id, domain, domain_id, shopper_ids, source):
        """
        Sends a notification to the shopper account and administrative contact email address(es) found for the domain
        success_message = 'reg-only_repeat_offender_email_sent', 'template': 5493
        :param ticket_id:
        :param domain:
        :param domain_id:
        :param shopper_ids:
        :param source:
        :return:
        """
        if not shopper_ids:
            return False

        template = 'registered.repeat_offender'
        message_type = 'reg-only_repeat_offender'
        exception_type = 'reg-only_repeat_offender_email_exception'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_shopper_email_be_sent(domain) or self._CAN_FLOOD:

                # If the domain is associated with a parent/child API reseller
                #  account, then email both the parent and child account
                for shopper_id in shopper_ids:
                    substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                           'DOMAIN': domain,
                                           'SANITIZED_URL': sanitize_url(source)}

                    kwargs['domain_id'] = domain_id
                    send_mail(template, substitution_values, **kwargs)
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_shopper_suspension(self, ticket_id, domain, domain_id, shopper_ids, source, report_type):
        """
        Sends a suspension notification to the shopper account and administrative contact email address(es)
        success_message = 'reg-only_shopper_suspend_email_sent', 'template': 3760
        found for the domain
        :param ticket_id:
        :param domain:
        :param domain_id:
        :param shopper_ids:
        :param source:
        :param report_type:
        :return:
        """
        if not shopper_ids:
            return False

        template = 'registered.suspend'
        message_type = 'reg-only_domain_suspension'
        exception_type = 'reg-only_shopper_suspend_email_exception'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_shopper_email_be_sent(domain) or self._CAN_FLOOD:

                # If the domain is associated with a parent/child API reseller
                #  account, then email both the parent and child account
                for shopper_id in shopper_ids:
                    substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                           'DOMAIN': domain,
                                           'SANITIZED_URL': sanitize_url(source),
                                           'MALICIOUS_ACTIVITY': report_type}

                    kwargs[self.DOMAIN_ID] = domain_id
                    send_mail(template, substitution_values, **kwargs)
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_shopper_intentional_suspension(self, ticket_id, domain, domain_id, shopper_ids, report_type):
        """
        Sends an intentional suspension notification to the shopper account email address found for the domain
        success_message = 'reg-only_shopper_suspend_intentional_email_sent', 'template': 4044
        :param ticket_id:
        :param domain:
        :param domain_id:
        :param shopper_ids:
        :param report_type:
        :return:
        """
        if not shopper_ids:
            return False

        template = 'registered.suspend_intentionally_malicious'
        message_type = 'reg-only_domain_suspension_intentional'
        exception_type = 'reg-only_shopper_suspend_intentional_email_exception'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_shopper_email_be_sent(domain) or self._CAN_FLOOD:

                # If the domain is associated with a parent/child API reseller
                #  account, then email both the parent and child account
                for shopper_id in shopper_ids:
                    substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                           'DOMAIN': domain,
                                           'MALICIOUS_ACTIVITY': report_type}

                    kwargs[self.DOMAIN_ID] = domain_id
                    send_mail(template, substitution_values, **kwargs)
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_shopper_compromise_suspension(self, ticket_id, domain, domain_id, shopper_ids):
        """
        Sends an intentional suspension notification to the shopper account email address found for the domain
        success_message = 'reg-only_shopper_compromise_suspend_email_sent', 'template': 5282
        :param ticket_id:
        :param domain:
        :param domain_id:
        :param shopper_ids:
        :return:
        """
        if not shopper_ids:
            return False

        template = 'registered.suspend_shopper_compromise'
        message_type = 'reg-only_domain_suspension_compromise'
        exception_type = 'reg-only_shopper_compromise_suspend_email_exception'

        kwargs = self.generate_kwargs_for_hermes()

        try:
            if self._throttle.can_shopper_email_be_sent(domain) or self._CAN_FLOOD:

                # If the domain is associated with a parent/child API reseller
                #  account, then email both the parent and child account
                for shopper_id in shopper_ids:
                    substitution_values = {'ACCOUNT_NUMBER': shopper_id}

                    kwargs[self.DOMAIN_ID] = domain_id
                    send_mail(template, substitution_values, **kwargs)
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True

    def send_csam_shopper_suspension(self, ticket_id, domain, shopper_id, domain_id):
        """
        Sends a notification to the shopper account email address found for the domain account
        success_message = 'registered_shopper_suspend_CSAM_notice_email_sent', 'template': 5722
        :param ticket_id:
        :param domain:
        :param shopper_id:
        :param domain_id:
        :return:
        """

        if not shopper_id:
            return False

        template = 'csam.suspend'
        message_type = 'registered_shopper_suspend_CSAM_notice'
        exception_type = 'registered_shopper_suspend_CSAM_email_exception'

        kwargs = self.generate_kwargs_for_hermes()

        redis_key = f'{domain}_suspended_email'

        try:
            if self._throttle.can_shopper_email_be_sent(redis_key) or self._CAN_FLOOD:
                substitution_values = {'ACCOUNT_NUMBER': shopper_id,
                                       'DOMAIN': domain}

                kwargs[self.DOMAIN_ID] = domain_id
                send_mail(template, substitution_values, **kwargs)
            else:
                self._logger.warning(f'Cannot send {template} for {domain}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {domain}: {e}')
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True
