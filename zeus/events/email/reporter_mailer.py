import logging

from hermes.messenger import send_mail

from zeus.events.email.interface import Mailer
from zeus.events.user_logging.events import generate_event


class ReporterMailer(Mailer):
    def __init__(self, app_settings):
        super(ReporterMailer, self).__init__(app_settings)
        self._logger = logging.getLogger(__name__)

    def send_acknowledgement_email(self, ticket_id, reporter_email):
        """
        Sends an acknowledgement email to FOS reporters
        :param ticket_id:
        :param reporter_email:
        :return:
        """
        template = "reporter.mail_reporter"

        message_type = "reporter_ack_email"
        exception_type = "reporter_ack_email_exception"
        success_message = "reporter_ack_email_sent"

        kwargs = self.generate_kwargs_for_hermes()

        try:
            kwargs['recipients'] = [{'email': reporter_email}]
            resp = send_mail(template, {}, **kwargs)
            resp.update({'type': message_type, 'template': 3454})
            generate_event(ticket_id, success_message, **resp)
        except Exception as e:
            self._logger.error("Unable to send {} for {}: {}".format(template, ticket_id, e.message))
            generate_event(ticket_id, exception_type, type=message_type)
            return False
        return True
