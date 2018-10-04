from datetime import datetime, timedelta

from zeus.events.email.foreign_mailer import ForeignMailer
from zeus.reviews.reviews import BasicReview
from zeus.utils.functions import (get_host_abuse_email_from_dict,
                                  get_host_brand_from_dict,
                                  get_host_info_from_dict)
from zeus.utils.slack import SlackFailures, ThrottledSlack


class ForeignHandler:
    TYPES = ['PHISHING']
    FOREIGN = 'FOREIGN'

    def __init__(self, app_settings):
        self.mailer = ForeignMailer(app_settings)
        self.slack = SlackFailures(ThrottledSlack(app_settings))

        self.basic_review = BasicReview(app_settings)
        self.HOLD_TIME = app_settings.HOLD_TIME

    def foreign_notice(self, data):
        hosted_brand = get_host_brand_from_dict(data)
        recipients = get_host_abuse_email_from_dict(data)
        ip = get_host_info_from_dict(data).get('ip')
        ticket_id = data.get('ticketId')
        domain = data.get('sourceDomainOrIp')
        source = data.get('source')

        if not self._validate_required_args(data):
            return False

        self.basic_review.place_in_review(ticket_id, datetime.utcnow() + timedelta(seconds=self.HOLD_TIME),
                                          '24hr_notice_sent')

        if not self.mailer.send_foreign_hosting_notice(ticket_id, domain, source, hosted_brand, recipients, ip):
            self.slack.failed_to_send_foreign_hosting_notice(domain)
            return False
        return True

    def _validate_required_args(self, data):
        ticket_id = data.get('ticketId')

        if data.get('hosted_status') != self.FOREIGN:
            self.slack.invalid_hosted_status(ticket_id)
        elif data.get('type') not in self.TYPES:
            self.slack.invalid_abuse_type(ticket_id)
        else:
            return True
        return False
