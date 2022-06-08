import os
import urllib.parse
from collections import OrderedDict


class AppConfig(object):
    NOTIFICATION_LOCK_TIME = 60  # Just 60 seconds for testing purposes
    SUSPEND_HOSTING_LOCK_TIME = SUSPEND_DOMAIN_LOCK_TIME = 5 * 60  # Seconds in 5 minutes
    HOLD_TIME = 60  # Time to place something in review
    SUCURI_HOLD_TIME = 60  # Just 60 seconds for testing purposes
    FRAUD_REVIEW_TIME = 365  # Year for testing purposes
    HIGH_VALUE_HOLD_TIME = 60  # Just 60 seconds for testing purposes

    DB = 'test'
    DB_USER = 'dbuser'
    DB_HOST = 'localhost'

    DB_KELVIN = 'test'
    DB_KELVIN_HOST = 'localhost'
    DB_KELVIN_USER = 'user'

    COLLECTION = 'incidents'
    LOGGING_COLLECTION = 'logs'

    # Temporary From address for OC Messaging until we determine why emails
    #  aren't being received by dcueng@, contact bxberry@ with questions.
    NON_PROD_EMAIL_ADDRESS = os.getenv('EMAIL_RECIPIENT', 'dcuinternal@godaddy.com')

    DIABLO_URL = 'https://cpanelprovapi.prod.phx3.secureserver.net/v1/accounts/'
    GOCENTRAL_URL = os.getenv('GOCENTRAL_URL')
    MWPONE_URL = 'https://api.servicemanager.godaddy.com/v1/accounts/'
    PLESK_URL = 'https://p3nwplskapp-v01.shr.prod.phx3.secureserver.net:8084/v1/accounts/'
    VERT_URL = ''

    # For SLACK notifications on suspension failures
    SLACK_URL = os.getenv('SLACK_HANDLER')
    SLACK_CHANNEL = '#queue_bot_test'

    ENTERED_BY = 'DCU'  # The 'Entered By' field in CRM Shopper Notes
    DOMAIN_SERVICE = '0.0.0.0:8080'
    PROTECTED_DOMAINS = {'myftpupload.com', 'godaddysites.com', 'secureserver.net'}
    SUCURI_PRODUCT_LIST = ['Website Security Deluxe', 'Website Security Essential', 'Website Security Express',
                           'Website Security Ultimate']

    # Retrieve certs and keys for sending Customer Emails
    OCM_SSL_CERT = os.getenv('OCM_SSL_CERT')
    OCM_SSL_KEY = os.getenv('OCM_SSL_KEY')
    ZEUS_SSL_CERT = os.getenv('ZEUS_SSL_CERT')
    ZEUS_SSL_KEY = os.getenv('ZEUS_SSL_KEY')
    GOCENTRAL_SSL_CERT = os.getenv('GOCENTRAL_SSL_CERT')
    GOCENTRAL_SSL_KEY = os.getenv('GOCENTRAL_SSL_KEY')
    CMAP_API_CERT = os.getenv('CMAP_API_CERT', 'api.crt')
    CMAP_API_KEY = os.getenv('CMAP_API_KEY', 'api.key')

    REDIS = os.getenv('REDIS', 'localhost')

    SHOPLOCKED_URL = ''
    CRMALERT_URL = ''

    BROKER_URL = os.getenv('MULTIPLE_BROKERS')
    GDBS_QUEUE = 'devgdbrandservice'
    ZEUSQUEUE = 'devzeus'

    def __init__(self):
        self.DB_PASS = urllib.parse.quote(os.getenv('DB_PASS', 'password'))
        self.DBURL = 'mongodb://{}:{}@{}/{}'.format(self.DB_USER, self.DB_PASS, self.DB_HOST, self.DB)

        self.DB_KELVIN_PASS = urllib.parse.quote(os.getenv('DB_KELVIN_PASS', 'password'))
        self.DB_KELVIN_URL = 'mongodb://{}:{}@{}/{}'.format(self.DB_KELVIN_USER, self.DB_KELVIN_PASS, self.DB_HOST, self.DB_KELVIN)

        self.DIABLOUSER = os.getenv('DIABLOUSER', 'diablouser')
        self.DIABLOPASS = os.getenv('DIABLOPASS', 'diablopass')
        self.PLESKUSER = os.getenv('PLESKUSER', 'pleskuser')
        self.PLESKPASS = os.getenv('PLESKPASS', 'pleskpass')

        self.CMAP_PROXY_USER = os.getenv('CMAP_PROXY_USER', 'cmapproxyuser')
        self.CMAP_PROXY_PASS = os.getenv('CMAP_PROXY_PASS', 'cmapproxypass')
        self.CMAP_PROXY_CERT = os.getenv('CMAP_PROXY_CERT', 'cmapproxy.crt')
        self.CMAP_PROXY_KEY = os.getenv('CMAP_PROXY_KEY', 'cmapproxy.key')

        # VPS4 User/Pass are creds for a DCU Service account in the DCU-PHISHSTORY AD Group
        self.VPS4USER = os.getenv('VPS4USER', 'vps4user')
        self.VPS4PASS = os.getenv('VPS4PASS', 'vps4pass')

        self.CAN_FLOOD = os.getenv('sysenv', 'dev') in ['dev', 'test']


class ProductionAppConfig(AppConfig):
    NOTIFICATION_LOCK_TIME = 24 * 60 * 60  # Seconds in a day
    SUSPEND_HOSTING_LOCK_TIME = SUSPEND_DOMAIN_LOCK_TIME = 60 * 60  # Seconds in an hour
    HOLD_TIME = 24 * 60 * 60  # Time to place something in review
    SUCURI_HOLD_TIME = 72 * 60 * 60  # Tickets with domains that have Sucuri malware removal products given 72 hour hold
    FRAUD_REVIEW_TIME = 90  # If it is within 90 days, Fraud can review
    HIGH_VALUE_HOLD_TIME = 72 * 60 * 60  # Tickets with domains identified as High Value given 72 hour hold

    ZEUSQUEUE = 'zeus'

    DB = 'phishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_p_phishv2'

    DB_KELVIN = 'dcu_kelvin'
    DB_KELVIN_HOST = '10.22.9.209'
    DB_KELVIN_USER = 'sau_service_kelvinv2'

    SLACK_CHANNEL = '#dcu_alerts'

    DOMAIN_SERVICE = 'domainservice-rest.abuse-api-prod.svc.cluster.local:8080'

    SSO_URL = 'https://sso.godaddy.com'
    MIMIR_URL = 'https://mimir.int.godaddy.com'
    SHOPLOCKED_URL = 'https://shoplocked.api.int.godaddy.com'
    VERT_URL = 'https://vertigo.cmap.proxy.int.godaddy.com/vertigo/v1/container/'
    CRMALERT_URL = 'https://crm-alert.int.godaddy.com'

    VPS4_URLS = OrderedDict([('IAD2', 'https://vps4.api.iad2.godaddy.com'),
                             ('SIN2', 'https://vps4.api.sin2.godaddy.com'),
                             ('AMS3', 'https://vps4.api.ams3.godaddy.com')])

    GDBS_QUEUE = 'gdbrandservice'

    def __init__(self):
        super(ProductionAppConfig, self).__init__()


class OTEAppConfig(AppConfig):
    ZEUSQUEUE = 'otezeus'

    DB = 'otephishstory'
    DB_HOST = '10.22.9.209'
    DB_USER = 'sau_o_phish'

    DB_KELVIN = 'ote_dcu_kelvin'
    DB_KELVIN_HOST = '10.22.9.209'
    DB_KELVIN_USER = 'sau_service_otedcu'

    DOMAIN_SERVICE = 'domainservice-rest.abuse-api-ote.svc.cluster.local:8080'

    SSO_URL = 'https://sso.ote-godaddy.com'
    MIMIR_URL = 'https://mimir.int.ote-godaddy.com'
    CRMALERT_URL = 'https://crm-alert.int.ote-godaddy.com'

    VPS4_URLS = OrderedDict([('IAD2', 'https://vps4.api.test-godaddy.com'),
                             ('SIN2', 'https://vps4.api.test-godaddy.com'),
                             ('AMS3', 'https://vps4.api.test-godaddy.com')])

    GDBS_QUEUE = 'otegdbrandservice'

    def __init__(self):
        super(OTEAppConfig, self).__init__()


class DevelopmentAppConfig(AppConfig):
    DB = 'devphishstory'
    DB_HOST = '10.36.190.222'
    DB_USER = 'devuser'

    DB_KELVIN = 'devkelvin'
    DB_KELVIN_HOST = '10.36.190.222'
    DB_KELVIN_USER = 'devkelvin'

    DOMAIN_SERVICE = 'localhost:8080/domains'
    GOCENTRAL_URL = 'http://localhost:8080/orion/account/accountoperations.asmx'
    MWPONE_URL = 'http://localhost:8080/mwpone/v1/accounts/'
    DIABLO_URL = 'http://localhost:8080/diablo/v1/accounts/'

    SSO_URL = 'https://sso.dev-godaddy.com'
    MIMIR_URL = 'https://mimir.int.dev-godaddy.com'
    SHOPLOCKED_URL = 'http://localhost:8080/shoplocked'
    CRMALERT_URL = 'https://crm-alert.int.dev-godaddy.com'

    VPS4_URLS = OrderedDict([('IAD2', 'https://vps4.api.dev-godaddy.com'),
                             ('SIN2', 'https://vps4.api.dev-godaddy.com'),
                             ('AMS3', 'https://vps4.api.dev-godaddy.com')])
    GDBS_QUEUE = 'devgdbrandservice'

    def __init__(self):
        super(DevelopmentAppConfig, self).__init__()


class TestAppConfig(AppConfig):
    ZEUSQUEUE = 'testzeus'

    DB = 'testphishstory'
    DB_HOST = '10.36.190.222'
    DB_USER = 'testuser'

    DB_KELVIN = 'testkelvin'
    DB_KELVIN_HOST = '10.36.190.222'
    DB_KELVIN_USER = 'testkelvin'

    DOMAIN_SERVICE = 'domainservice-rest.abuse-api-test.svc.cluster.local:8080'

    DIABLO_URL = 'https://diablo.api.test-godaddy.com/v1/accounts/'
    GOCENTRAL_URL = 'https://services.orion.test.glbt1.gdg/account/accountoperations.asmx'
    MWPONE_URL = 'https://api.servicemanager.test-godaddy.com/v1/accounts/'
    PLESK_URL = 'https://p3nwplskapp.test-godaddy.com:8084/v1/accounts/'
    VERT_URL = ''

    SSO_URL = 'https://sso.test-godaddy.com'
    MIMIR_URL = 'https://mimir.int.test-godaddy.com'
    SHOPLOCKED_URL = 'https://shoplocked.api.int.test-godaddy.com'
    CRMALERT_URL = 'https://crm-alert.int.test-godaddy.com'

    VPS4_URLS = OrderedDict([('IAD2', 'https://vps4.api.test-godaddy.com'),
                             ('SIN2', 'https://vps4.api.test-godaddy.com'),
                             ('AMS3', 'https://vps4.api.test-godaddy.com')])
    GDBS_QUEUE = 'testgdbrandservice'

    HOLD_TIME = 1 * 60 * 30
    SUCURI_HOLD_TIME = 1 * 60 * 30
    HIGH_VALUE_HOLD_TIME = 1 * 60 * 30

    def __init__(self):
        super(TestAppConfig, self).__init__()


class UnitTestConfig(AppConfig):
    DBURL = 'mongodb://localhost/devphishstory'
    DB = 'test'
    COLLECTION = 'test'
    HOLD_TIME = 1
    SUCURI_HOLD_TIME = 1
    HIGH_VALUE_HOLD_TIME = 1

    REDIS = 'localhost'
    CAN_FLOOD = False

    CMAP_API_CERT = 'api.crt'
    CMAP_API_KEY = 'api.key'
    DIABLOUSER = 'diablouser'
    DIABLOPASS = 'diablopass'
    PLESKUSER = 'pleskuser'
    PLESKPASS = 'pleskpass'
    VPS4USER = 'vps4user'
    VPS4PASS = 'vps4pass'

    CMAP_PROXY_USER = 'cmapproxyuser'
    CMAP_PROXY_PASS = 'cmapproxypass'
    CMAP_PROXY_CERT = 'cmapproxy.crt'
    CMAP_PROXY_KEY = 'cmapproxy.key'
    GOCENTRAL_SSL_CERT = 'cert'
    GOCENTRAL_SSL_KEY = 'key'

    DOMAIN_SERVICE = 'domainservice-rest.abuse-api-dev.svc.cluster.local:8080'

    SLACK_URL = 'test-url'
    SLACK_CHANNEL = 'test-channel'
    NOTIFICATION_LOCK_TIME = 60

    SSO_URL = ''
    MIMIR_URL = ''
    CRMALERT_URL = ''
    GOCENTRAL_URL = ''

    VPS4_URLS = OrderedDict([('IAD2', ''),
                             ('SIN2', ''),
                             ('AMS3', '')])


config_by_name = {'dev': DevelopmentAppConfig, 'prod': ProductionAppConfig, 'ote': OTEAppConfig, 'unit-test': UnitTestConfig, 'test': TestAppConfig}
