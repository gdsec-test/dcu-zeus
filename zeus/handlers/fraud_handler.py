import logging

from zeus.events.email.fraud_mailer import FraudMailer
from zeus.utils.functions import get_shopper_id_from_dict, \
    get_shopper_create_date_from_dict, \
    get_domain_create_date_from_dict, \
    get_host_shopper_id_from_dict, \
    get_hosting_created_date_from_dict


class FraudHandler:
    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self.mailer = FraudMailer(app_settings)

    def new_domain(self, data):
        self._logger.info('Sending new domain registration to fraud for {}'.format(data.get('ticketId')))

        ticket_id = data.get('ticketId')
        domain = data.get('sourceDomainOrIp')
        shopper_id = get_shopper_id_from_dict(data)
        domain_create_date = get_domain_create_date_from_dict(data)
        report_type = data.get('type')
        source = data.get('source')
        target = data.get('target')

        return self.mailer.send_new_domain_notification(ticket_id, domain, shopper_id, domain_create_date,
                                                        report_type, source, target)

    def new_shopper(self, data):
        self._logger.info('Sending new shopper account to fraud for {}'.format(data.get('ticketId')))

        shopper_id = get_shopper_id_from_dict(data)
        shopper_create_date = get_shopper_create_date_from_dict(data)
        ticket_id = data.get('ticketId')
        domain = data.get('sourceDomainOrIp')
        report_type = data.get('type')
        source = data.get('source')
        target = data.get('target')

        return self.mailer.send_new_shopper_notification(ticket_id, domain, shopper_id, shopper_create_date,
                                                         report_type, source, target)

    def new_hosting_account(self, data):
        self._logger.info('Sending new hosting account to fraud for {}'.format(data.get('ticketId')))

        shopper_id = get_host_shopper_id_from_dict(data)
        if not shopper_id:
            return False

        ticket_id = data.get('ticketId')
        domain = data.get('sourceDomainOrIp')
        shopper_id = get_host_shopper_id_from_dict(data)
        account_create_date = get_hosting_created_date_from_dict(data)
        report_type = data.get('type')
        source = data.get('source')
        target = data.get('target')

        return self.mailer.send_new_hosting_account_notification(ticket_id, domain, shopper_id, account_create_date,
                                                                 report_type, source, target)
