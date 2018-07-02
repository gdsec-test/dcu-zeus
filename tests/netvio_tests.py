# import os
#
# from mock import patch
# from nose.tools import assert_true, assert_multi_line_equal
#
# from zeus.events.netvio.netvio import Netvio
# from zeus.events.netvio.soap import SoapBase
#
#
# class TestNetvio:
#     shopper_id = 0
#     guid = "00a00a00-a00a-00a0-0a00-a00a00a00a00"
#     abuse_type = 'PHISHING'
#     value = 'http://comicsn.beer/junk/\nhttps://comicsn.beer/bad/content.php'
#     netvio_ticket_id = 144
#     env = 'test'
#
#     @classmethod
#     def setup(cls):
#         os.environ['sysenv'] = cls.env
#         cls._nv = Netvio()
#
#     def test_constructor(self):
#         assert_true(self._nv._config.NETVIO_API_URL == 'https://netvio.api.int.test-godaddy.com/Api.svc?wsdl')
#
#     @patch('zeus.events.netvio.netvio.strftime')
#     def test_create_message(self, strftime):
#         strftime.return_value = '2017-12-06T23:01:22'
#         expected_message = '''
#             <Tickets xmlns="http://schemas.datacontract.org/2004/07/CustomerSupport.CopyrightTool.Services.Contracts">
#                 <Ticket>
#                   <Categories>
#                     <TicketCategory>
#                       <CategoryMtmID>32</CategoryMtmID>
#                     </TicketCategory>
#                   </Categories>
#                   <CreateDate>2017-12-06T23:01:22</CreateDate>
#                   <Description>Network Violation</Description>
#                   <EnteredBy>{name}</EnteredBy>
#                   <Notes>
#                     <TicketNotes>
#                       <Note>{abuse_type} Violation
#
# {value}</Note>
#                     </TicketNotes>
#                   </Notes>
#                   <Resources>
#                     <TicketResource>
#                       <Fname>{guid}</Fname>
#                       <OrderID />
#                       <ResourceID>{guid}</ResourceID>
#                       <ShopperId>{shopper_id}</ShopperId>
#                     </TicketResource>
#                   </Resources>
#                   <TicketTypeID>1</TicketTypeID>
#                   <TicketTypeStatusID>22</TicketTypeStatusID>
#                 </Ticket>
#             </Tickets>
#         '''.format(shopper_id=self.shopper_id,
#                    guid=self.guid,
#                    name=self._nv._config.NETVIO_ENTERED_BY,
#                    abuse_type=self.abuse_type,
#                    value=self.value)
#
#         returned_message = self._nv._create_message(self.shopper_id,
#                                                     self.guid,
#                                                     self.abuse_type,
#                                                     self.value)
#         assert_multi_line_equal(expected_message, returned_message)
#
#     def test_get_message(self):
#         expected_message = '''
# <TicketReferences xmlns="http://schemas.datacontract.org/2004/07/CustomerSupport.CopyrightTool.Services.Contracts">
#     <TicketReference>
#         <ID>{id}</ID>
#     </TicketReference>
# </TicketReferences>
#         '''.format(id=self.netvio_ticket_id)
#         returned_message = self._nv._get_message(self.netvio_ticket_id)
#         assert_multi_line_equal(expected_message, returned_message)
#
#     @patch.object(SoapBase, 'req')
#     def test_get_ticket(self, req):
#         class TestTickets:
#             Ticket = 1
#
#         class OnTheFly:
#             IsSuccess = True
#             Tickets = TestTickets()
#
#         req.return_value = OnTheFly()
#
#         expected_result = self._nv.get_ticket(self.netvio_ticket_id)
#         assert_true(expected_result == 1)
