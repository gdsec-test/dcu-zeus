import logging

from zeus.events.support_tools.constants import note_mappings
from zeus.events.support_tools.crm import ThrottledCRM
from zeus.utils.slack import SlackFailures, ThrottledSlack


class HostedScribe:
    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self.crm = ThrottledCRM(app_settings)
        self.slack = SlackFailures(ThrottledSlack(app_settings))

    def customer_warning(self, ticket, guid, url, report_type, shopper_id):
        crm_note = note_mappings['hosted']['customerWarning']['crm'].format(guid=guid, type=report_type, location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)
        return True

    def suspension(self, ticket, guid, url, report_type, shopper_id):
        crm_note = note_mappings['hosted']['suspension']['crm'].format(guid=guid, type=report_type, location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)
        return True

    def intentionally_malicious(self, ticket, guid, url, report_type, shopper_id):
        crm_note = note_mappings['hosted']['intentionallyMalicious']['crm'].format(guid=guid, type=report_type,
                                                                                   location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)
        return True

    def shopper_compromise(self, ticket, guid, url, report_type, shopper_id):
        crm_note = note_mappings['hosted']['shopperCompromise']['crm'].format(guid=guid, type=report_type, location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)
        return True

    def content_removed(self, ticket, guid, url, report_type, shopper_id):
        crm_note = note_mappings['hosted']['contentRemoved']['crm'].format(guid=guid, type=report_type, location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)
        return True

    def repeat_offender(self, ticket, guid, url, report_type, shopper_id):
        crm_note = note_mappings['hosted']['repeatOffender']['crm'].format(guid=guid, type=report_type, location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)
        return True

    def extensive_compromise(self, ticket, guid, url, report_type, shopper_id):
        crm_note = note_mappings['hosted']['extensiveCompromise']['crm'].format(guid=guid, type=report_type,
                                                                                location=url)
        self.crm.notate_crm_account(shopper_id, ticket, crm_note)
        return True
