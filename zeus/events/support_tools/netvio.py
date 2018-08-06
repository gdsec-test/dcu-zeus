import logging
from time import localtime, strftime
from xml.sax.saxutils import escape

from suds.sax.text import Raw

from zeus.events.support_tools.soap import SoapBase
from zeus.persist.notification_timeouts import Throttle


class ThrottledNetvio:
    def __init__(self, app_settings):
        self._logger = logging.getLogger(__name__)
        self._decorated = Netvio()
        self._throttle = Throttle(app_settings.REDIS, app_settings.NOTIFICATION_LOCK_TIME)  # one day throttle

    def create_ticket(self, shopper_id, guid, abuse_type, values):
        if self._throttle.can_netvio_be_created(guid):
            return self._decorated.create_ticket(shopper_id, guid, abuse_type, values)

        self._logger.info("Netvio for {} already created".format(guid))
        return True

    def get_ticket(self, ticket_id):
        return self._decorated.get_ticket(ticket_id)


class Netvio(SoapBase):
    _name = 'Netvio'

    def __init__(self):
        super(Netvio, self).__init__()
        self._url = self._config.NETVIO_API_URL
        self._client_crt = self._config.NETVIO_SSL_CERT
        self._client_key = self._config.NETVIO_SSL_KEY
        self._dcu_username = self._config.NETVIO_ENTERED_BY

    def _create_message(self, shopper_id, guid, abuse_type, values):
        """
        Private method to create a formatted message
        :param shopper_id: Must be a string
        :param guid: Must be a string guid
        :param abuse_type: Must be a string like PHISHING
        :param values: Must be a string
        :return:
        """
        current_time = strftime('%Y-%m-%dT%H:%M:%S', localtime())

        # Support for a list of multiple category id's
        # Categories are: 23=SOC-Compromised, 26=SOC-Malicious Activity, 32=SOC-Other
        # Hard-coding SOC-Other, to make HA generated netvios easier to locate @bxberry
        categories = 32

        category = ''
        if isinstance(categories, int):
            category = '''
                <TicketCategory>
                      <CategoryMtmID>{}</CategoryMtmID>
                    </TicketCategory>
            '''.format(categories)
        elif isinstance(categories, list):
            for cat in categories:
                category += '''
                <TicketCategory>
                      <CategoryMtmID>{}</CategoryMtmID>
                    </TicketCategory>
                '''.format(cat)

        # we need to prepare the values for xml
        values = escape(values)

        # TicketTypeID is always set to 1, which is the enumerated value for 'Network Violations'
        # TicketTypeStatusID is always set to 22, which is 'Closed Notification Only'
        # EnteredBy is your Manager User Id (different for dev/test/prod), which can be viewed in CRM
        message = '''
            <Tickets xmlns="http://schemas.datacontract.org/2004/07/CustomerSupport.CopyrightTool.Services.Contracts">
                <Ticket>
                  <Categories>
                    {category}
                  </Categories>
                  <CreateDate>{create_date}</CreateDate>
                  <Description>Network Violation</Description>
                  <EnteredBy>{dcu_username}</EnteredBy>
                  <Notes>
                    <TicketNotes>
                      <Note>{abuse_type} Violation\n\n{values}</Note>
                    </TicketNotes>
                  </Notes>
                  <Resources>
                    <TicketResource>
                      <Fname>{guid}</Fname>
                      <OrderID />
                      <ResourceID>{guid}</ResourceID>
                      <ShopperId>{shopper_id}</ShopperId>
                    </TicketResource>
                  </Resources>
                  <TicketTypeID>1</TicketTypeID>
                  <TicketTypeStatusID>22</TicketTypeStatusID>
                </Ticket>
            </Tickets>
        '''.format(category=category.strip(),
                   create_date=current_time,
                   dcu_username=self._dcu_username,
                   abuse_type=abuse_type,
                   values=values,
                   guid=guid,
                   shopper_id=shopper_id)
        return message

    @staticmethod
    def _get_message(ticket_id):
        """
        Private method to create a formatted message
        :param ticket_id: Must be an int32
        :return:
        """
        message = '''
<TicketReferences xmlns="http://schemas.datacontract.org/2004/07/CustomerSupport.CopyrightTool.Services.Contracts">
    <TicketReference>
        <ID>{id}</ID>
    </TicketReference>
</TicketReferences>
        '''.format(id=ticket_id)
        return message

    def create_ticket(self, shopper_id, guid, abuse_type, values):
        """
        Will create a new netvio ticket when passed appropriate parameters
        :param shopper_id: Must be a string
        :param guid: Must be a string guid
        :param abuse_type: Must be a string like PHISHING
        :param values: Must be a string
        :return:
        """
        self._logger.info("Attempting to create the netvio ticket: {}, {}, {}, {}".format(shopper_id,
                                                                                          guid,
                                                                                          abuse_type,
                                                                                          values))
        message = self._create_message(shopper_id, guid, abuse_type, values)
        raw_message = Raw(message)

        self.connect()
        results = self.req('Create', raw_message)

        fail_message = 'Unable to create netvio ticket for {}'.format(shopper_id)
        if results and results.IsSuccess:
            return results.TicketReferences.TicketReference[0].ID
        else:
            self._logger.error(fail_message)
            return False

    def get_ticket(self, ticket_id):
        """
        Method to get a netvio ticket information given the netvio ticket id
        :param ticket_id: Must be an int32
        :return:
        """
        self._logger.info("Attempting to get the netvio ticket: {}".format(ticket_id))

        message = self._get_message(ticket_id)
        raw_message = Raw(message)

        self.connect()
        results = self.req('Get', raw_message)

        fail_message = "Unable to get netvio ticket for {}".format(ticket_id)
        if results:
            if results.IsSuccess is True:
                return results.Tickets.Ticket
            else:
                raise Exception("{}, the results were not successful: {}".format(fail_message, results))
        else:
            raise Exception("{}, did not return any results".format(fail_message))
