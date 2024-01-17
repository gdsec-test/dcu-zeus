import logging

from hermes.messenger import send_mail

from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event
from zeus.persist.notification_timeouts import Throttle


class ReporterMailer(Mailer):
    def __init__(self, app_settings):
        super(ReporterMailer, self).__init__(app_settings)
        self._logger = logging.getLogger('celery.tasks')
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)
        self._CAN_FLOOD = app_settings.CAN_FLOOD

    def send_acknowledgement_email(self, source, reporter_email, dsa=False):
        """
        Sends an acknowledgement email to FOS reporters
        :param source:
        :param reporter_email:
        :return: boolean
        """
        template = "reporter.mail_reporter"

        message_type = "reporter_ack_email"
        exception_type = "reporter_ack_email_exception"
        success_message = "reporter_ack_email_sent"
        kwargs = self.generate_kwargs_for_hermes()
        ocm_template = 7010
        if dsa:
            ocm_template = 7237
        try:
            if self._throttle.can_reporter_acknowledge_email_be_sent(reporter_email) or self._CAN_FLOOD:
                kwargs['recipients'] = [{'email': reporter_email}]
                resp = send_mail(template, {}, **kwargs)
                resp.update({'type': message_type, 'template': ocm_template})
                generate_event(source, success_message, **resp)
                return True
            else:
                self._logger.warning(f'Cannot send {template} for {source}... still within 24hr window')
        except Exception as e:
            self._logger.error(f'Unable to send {template} for {source}: {e}')
            generate_event(source, exception_type, type=message_type)
        return False
