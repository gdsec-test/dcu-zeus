from nose.tools import assert_equals

from zeus.utils.mimir import Mimir


class TestMimir:
    def test_inf_with_none_value(self):
        _dict = {'abuseType': 'PHISHING',
                 'domainId': '0001',
                 'hostedStatus': 'HOSTED',
                 'hostingGuid': '0000-0000-0000',
                 'infractionType': 'MANUAL_NOTE',
                 'ncmecReportID': None,
                 'note': 'Test note',
                 'recordType': 'INFRACTION',
                 'shopperId': '0001',
                 'sourceDomainOrIp': 'example.com',
                 'sourceSubDomain': 'www.example.com',
                 'ticketId': 'DCU0001'
                 }
        _clean_dict = Mimir._clean_dict_for_mimir(_dict)
        _dict.pop('ncmecReportID')
        assert_equals(_dict, _clean_dict)

    def test_non_inf(self):
        _dict = {'abuseType': 'CHILD_ABUSE',
                 'hostedStatus': 'HOSTED',
                 'hostingGuid': '0000-0000-0000',
                 'infractionType': 'MANUAL_NOTE',
                 'note': 'Test note',
                 'recordType': 'NOTE',
                 'shopperId': '0001',
                 'sourceDomainOrIp': 'example.com',
                 'sourceSubDomain': 'www.example.com',
                 'ticketId': 'DCU0001'
                 }
        _clean_dict = Mimir._clean_dict_for_mimir(_dict)
        assert_equals(_dict, _clean_dict)
