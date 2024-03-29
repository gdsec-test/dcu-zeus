import os
import urllib
from collections import OrderedDict
from urllib.parse import quote


class AppConfig(object):
    env = os.getenv('sysenv', 'dev')
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
    EMAIL_COLLECTION = 'acknowledge_email'
    LOGGING_COLLECTION = 'logs'

    # Temporary From address for OC Messaging until we determine why emails
    #  aren't being received by dcueng@, contact bxberry@ with questions.
    NON_PROD_EMAIL_ADDRESS = os.getenv('EMAIL_RECIPIENT', 'dcuinternal@godaddy.com')

    ENTITLEMENT_URL = 'https://entitlements-ext.cp.api.prod.godaddy.com/'
    SUBSCRIPTIONS_URL = 'https://subscriptions-shim-ext.cp.api.prod.godaddy.com/'

    # TODO CMAPT-5272: remove all references to DIABLO_URL, MWPONE_URL, and PLESK_URL variables
    DIABLO_URL = 'https://cpanelprovapi.prod.phx3.secureserver.net/v1/accounts/'
    MWPONE_URL = 'https://api.servicemanager.godaddy.com/v1/accounts/'
    MWPV3_URL = 'https://mwp.api.phx3.dev-godaddy.com'
    PLESK_URL = 'https://gdapi.plesk-shared-app.int.gdcorp.tools/v1/accounts/'
    SHOPPER_API_URL = 'https://shopper.api.int.godaddy.com'

    # For SLACK notifications on suspension failures
    SLACK_URL = os.getenv('SLACK_HANDLER')
    SLACK_CHANNEL = '#queue_bot_test'

    ENTERED_BY = 'DCU'  # The 'Entered By' field in CRM Shopper Notes
    DOMAIN_SERVICE = '0.0.0.0:8080'
    PROTECTED_DOMAINS = {'myftpupload.com', 'godaddysites.com', 'secureserver.net', 'go.studio', 'secureserversites.net', 'mywebsitetransfer.com'}
    SUCURI_PRODUCT_LIST = ['Website Security Deluxe', 'Website Security Essential', 'Website Security Express',
                           'Website Security Ultimate']

    # Retrieve certs and keys for sending Customer Emails
    ZEUS_CLIENT_CERT = os.getenv('ZEUS_CLIENT_CERT')
    ZEUS_CLIENT_KEY = os.getenv('ZEUS_CLIENT_KEY')
    CMAP_API_CERT = os.getenv('CMAP_API_CERT', 'api.crt')
    CMAP_API_KEY = os.getenv('CMAP_API_KEY', 'api.key')

    REDIS = os.getenv('REDIS', 'localhost')

    SHOPLOCKED_URL = ''
    CRMALERT_URL = ''

    BROKER_URL = os.getenv('MULTIPLE_BROKERS')
    GDBS_QUEUE = 'devgdbrandservice'
    ZEUSQUEUE = 'devzeus'

    def __init__(self):
        self.DB_KELVIN_PASS = urllib.parse.quote(os.getenv('DB_KELVIN_PASS', 'password'))
        self.DB_PASS = quote(os.getenv('DB_PASS', 'password'))
        self.CLIENT_CERT = os.getenv("MONGO_CLIENT_CERT", '')
        self.DBURL = f'mongodb://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}/?authSource={self.DB}&readPreference=primary&directConnection=true&tls=true&tlsCertificateKeyFile={self.CLIENT_CERT}'
        self.DB_KELVIN_PASS = quote(os.getenv('DB_KELVIN_PASS', 'password'))
        self.DB_KELVIN_URL = f'mongodb://{self.DB_KELVIN_USER}:{self.DB_KELVIN_PASS}@{self.DB_HOST}/?authSource={self.DB_KELVIN}&readPreference=primary&directConnection=true&tls=true&tlsCertificateKeyFile={self.CLIENT_CERT}'

        # TODO CMAPT-5272: Remove all DIABLO*, PLESK*, CMAP_PROXY*, VPS4* variables
        self.DIABLOUSER = os.getenv('DIABLOUSER', 'diablouser')
        self.DIABLOPASS = os.getenv('DIABLOPASS', 'diablopass')
        self.PLESKUSER = os.getenv('PLESKUSER', 'pleskuser')
        self.PLESKPASS = os.getenv('PLESKPASS', 'pleskpass')

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
    DB_HOST = 'p3plsocritmdb00-00-f0.prod.phx3.gdg'
    DB_USER = 'sau_p_phishv2'

    DB_KELVIN = 'dcu_kelvin'
    DB_KELVIN_HOST = 'p3plsocritmdb00-00-f0.prod.phx3.gdg'
    DB_KELVIN_USER = 'sau_service_kelvinv2'

    SLACK_CHANNEL = '#dcu_alerts'

    DOMAIN_SERVICE = 'domainservice-rest.abuse-api-prod.svc.cluster.local:8080'

    SSO_URL = 'https://sso.gdcorp.tools'
    MIMIR_URL = 'https://mimir.cset.int.gdcorp.tools'
    SHOPLOCKED_URL = 'https://shoplocked.cset.int.gdcorp.tools'
    CRMALERT_URL = 'https://crm-alert.cset.int.gdcorp.tools'
    MWPV3_URL = 'https://mwp.api.phx3.godaddy.com'

    # TODO CMAPT-5272: remove all references to VPS4_URLS variable
    VPS4_URLS = OrderedDict([('IAD2', 'https://vps4.api.iad2.godaddy.com'),
                             ('SIN2', 'https://vps4.api.sin2.godaddy.com'),
                             ('AMS3', 'https://vps4.api.ams3.godaddy.com')])

    GDBS_QUEUE = 'gdbrandservice'

    def __init__(self):
        super(ProductionAppConfig, self).__init__()


class OTEAppConfig(AppConfig):
    ZEUSQUEUE = 'otezeus'

    DB = 'otephishstory'
    DB_HOST = 'p3plsocritmdb00-00-f0.prod.phx3.gdg'
    DB_USER = 'sau_o_phish'

    DB_KELVIN = 'ote_dcu_kelvin'
    DB_KELVIN_HOST = 'p3plsocritmdb00-00-f0.prod.phx3.gdg'
    DB_KELVIN_USER = 'sau_service_otedcu'

    DOMAIN_SERVICE = 'domainservice-rest.abuse-api-ote.svc.cluster.local:8080'

    ENTITLEMENT_URL = 'https://entitlements-ext.cp.api.ote.godaddy.com/'
    SUBSCRIPTIONS_URL = 'https://subscriptions-shim-ext.cp.api.ote.godaddy.com/'

    SSO_URL = 'https://sso.ote-gdcorp.tools'
    MIMIR_URL = 'https://mimir.cset.int.ote-gdcorp.tools'
    CRMALERT_URL = 'https://crm-alert.cset.int.ote-gdcorp.tools'
    SHOPPER_API_URL = 'https://shopper.api.int.ote-godaddy.com'
    MWPV3_URL = 'https://mwp.api.phx3.ote-godaddy.com'

    VPS4_URLS = OrderedDict([('IAD2', 'https://vps4.api.test-godaddy.com'),
                             ('SIN2', 'https://vps4.api.test-godaddy.com'),
                             ('AMS3', 'https://vps4.api.test-godaddy.com')])

    GDBS_QUEUE = 'otegdbrandservice'

    def __init__(self):
        super(OTEAppConfig, self).__init__()


class DevelopmentAppConfig(AppConfig):
    DB = 'devphishstory'
    DB_HOST = 'mongodb.cset.int.dev-gdcorp.tools'
    DB_USER = 'devuser'

    DB_KELVIN = 'devkelvin'
    DB_KELVIN_HOST = 'mongodb.cset.int.dev-gdcorp.tools'
    DB_KELVIN_USER = 'devkelvin'

    DOMAIN_SERVICE = 'localhost:8080/domains'
    MWPONE_URL = 'http://localhost:8080/mwpone/v1/accounts/'
    DIABLO_URL = 'http://localhost:8080/diablo/v1/accounts/'
    MWPV3_URL = 'https://mwp.api.phx3.dev-godaddy.com'

    ENTITLEMENT_URL = 'https://entitlements-ext.cp.api.dp.godaddy.com/'
    SUBSCRIPTIONS_URL = 'https://subscriptions-shim-ext.cp.api.dp.godaddy.com/'

    SSO_URL = 'https://sso.dev-gdcorp.tools'
    MIMIR_URL = 'https://mimir.cset.int.dev-gdcorp.tools'
    SHOPLOCKED_URL = 'http://localhost:8080/shoplocked'
    CRMALERT_URL = 'https://crm-alert.cset.int.dev-gdcorp.tools'
    SHOPPER_API_URL = 'https://shopper.api.int.dev-godaddy.com'

    VPS4_URLS = OrderedDict([('IAD2', 'https://vps4.api.dev-godaddy.com'),
                             ('SIN2', 'https://vps4.api.dev-godaddy.com'),
                             ('AMS3', 'https://vps4.api.dev-godaddy.com')])
    GDBS_QUEUE = 'devgdbrandservice'

    def __init__(self):
        super(DevelopmentAppConfig, self).__init__()


class TestAppConfig(AppConfig):
    ZEUSQUEUE = 'testzeus'

    DB = 'testphishstory'
    DB_HOST = 'mongodb.cset.int.dev-gdcorp.tools'
    DB_USER = 'testuser'

    DB_KELVIN = 'testkelvin'
    DB_KELVIN_HOST = 'mongodb.cset.int.dev-gdcorp.tools'
    DB_KELVIN_USER = 'testkelvin'
    DOMAIN_SERVICE = 'domainservice-rest.abuse-api-test.svc.cluster.local:8080'

    DIABLO_URL = 'https://diablo.api.test-godaddy.com/v1/accounts/'
    MWPONE_URL = 'https://api.servicemanager.test-godaddy.com/v1/accounts/'
    PLESK_URL = 'https://gdapi.plesk-shared-app.int.test-gdcorp.tools/v1/accounts/'
    SHOPPER_API_URL = 'https://shopper.api.int.test-godaddy.com'
    MWPV3_URL = 'https://mwp.api.phx3.test-godaddy.com'

    ENTITLEMENT_URL = 'https://entitlements-ext.cp.api.test.godaddy.com/'
    SUBSCRIPTIONS_URL = 'https://subscriptions-shim-ext.cp.api.test.godaddy.com/'

    SSO_URL = 'https://sso.test-gdcorp.tools'
    MIMIR_URL = 'https://mimir.cset.int.test-gdcorp.tools'
    SHOPLOCKED_URL = 'https://shoplocked.cset.int.test-gdcorp.tools'
    CRMALERT_URL = 'https://crm-alert.cset.int.test-gdcorp.tools'

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
    def __init__(self):
        super(AppConfig, self).__init__()
        self.DBURL = 'mongodb://localhost'
    DB = 'test'
    COLLECTION = 'test'
    HOLD_TIME = 1
    SUCURI_HOLD_TIME = 1
    HIGH_VALUE_HOLD_TIME = 1

    REDIS = 'localhost'
    CAN_FLOOD = False

    SHOPPER_API_URL = 'test_shopper_api'
    ZEUS_CLIENT_CERT = 'zeus_test_cert'
    ZEUS_CLIENT_KEY = 'zeus_test_key'

    CMAP_API_CERT = 'api.crt'
    CMAP_API_KEY = 'api.key'
    DIABLOUSER = 'diablouser'
    DIABLOPASS = 'diablopass'
    PLESKUSER = 'pleskuser'
    PLESKPASS = 'pleskpass'
    VPS4USER = 'vps4user'
    VPS4PASS = 'vps4pass'

    DOMAIN_SERVICE = 'domainservice-rest.abuse-api-dev.svc.cluster.local:8080'

    SLACK_URL = 'test-url'
    SLACK_CHANNEL = 'test-channel'
    NOTIFICATION_LOCK_TIME = 60

    SSO_URL = ''
    MIMIR_URL = ''
    CRMALERT_URL = ''
    ENTITLEMENT_URL = 'localhost/'
    SUBSCRIPTIONS_URL = 'localhost/'

    VPS4_URLS = OrderedDict([('IAD2', ''),
                             ('SIN2', ''),
                             ('AMS3', '')])


config_by_name = {'dev': DevelopmentAppConfig, 'prod': ProductionAppConfig, 'ote': OTEAppConfig, 'unit-test': UnitTestConfig, 'test': TestAppConfig}
