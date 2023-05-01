import logging
import os

from crm_notate.message_factory import Message

from zeus.persist.notification_timeouts import Throttle


class ThrottledCRM:
    def __init__(self, app_settings):
        self._logger = logging.getLogger('celery.tasks')
        self._decorated = CRM(app_settings)
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)  # one day throttle

    def notate_crm_account(self, shopper_id_list, ticket_id, note, domain_or_guid, action_type):
        if not isinstance(shopper_id_list, list):
            shopper_id_list = [shopper_id_list]

        if self._throttle.can_crm_be_notated(f'{domain_or_guid}-{action_type}'):
            self._decorated.notate_crm_accounts(shopper_id_list, ticket_id, note)
        else:
            self._logger.info(f'CRM for {domain_or_guid} already notated for 24hr hold')


class CRM:
    NOTES = "SNOW ID: {ticket} {entered_by} - Engineers. {notes}"
    SHOPPER_NOTE_SUCCESS = "Added CRM note to shopper {} for ticket {}"
    SHOPPER_NOTE_FAILURE = "Unable to add CRM note to shopper {} for ticket: {} : {}"

    def __init__(self, app_settings):
        self._logger = logging.getLogger('celery.tasks')
        self.env = os.getenv('sysenv', 'dev')
        self.author = app_settings.ENTERED_BY

    def notate_crm_accounts(self, shopper_id_list, ticket_id, notes):
        """
        Adds note to customer CRM account
        :param shopper_id_list:
        :param ticket_id:
        :param notes:
        :return:
        """
        if not isinstance(shopper_id_list, list):
            shopper_id_list = [shopper_id_list]

        try:
            messages = Message.factory(Message.WSCMS, self.env, self.author)
            notation = self.NOTES.format(ticket=ticket_id, entered_by=self.author, notes=notes)

            for shopper_id in shopper_id_list:
                if messages.add_note(shopper_id, notation, self.author):
                    self._logger.info(self.SHOPPER_NOTE_SUCCESS.format(shopper_id, ticket_id))
        except Exception as e:
            self._logger.error(self.SHOPPER_NOTE_FAILURE.format(shopper_id_list, ticket_id, e))
