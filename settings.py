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

    NES_URL = 'https://subscriptions-shim-ext.cp.api.test.godaddy.com/v2/customers/{}/suspendByEntitlementId'

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
        self.DB_PASS = urllib.parse.quote(os.getenv('DB_PASS', 'password'))
        self.DBURL = 'mongodb://{}:{}@{}/{}'.format(self.DB_USER, self.DB_PASS, self.DB_HOST, self.DB)

        self.DB_KELVIN_PASS = urllib.parse.quote(os.getenv('DB_KELVIN_PASS', 'password'))
        self.DB_KELVIN_URL = 'mongodb://{}:{}@{}/{}'.format(self.DB_KELVIN_USER, self.DB_KELVIN_PASS, self.DB_HOST, self.DB_KELVIN)

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

    SSO_URL = 'https://sso.gdcorp.tools'
    MIMIR_URL = 'https://mimir.cset.int.gdcorp.tools'
    SHOPLOCKED_URL = 'https://shoplocked.cset.int.gdcorp.tools'
    CRMALERT_URL = 'https://crm-alert.cset.int.gdcorp.tools'

    # TODO: LKM - verify this is the correct URL for prod
    NES_URL = 'https://subscriptions-shim-ext.cp.api.godaddy.com/v2/customers/{}/suspendByEntitlementId'

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

    SSO_URL = 'https://sso.ote-gdcorp.tools'
    MIMIR_URL = 'https://mimir.cset.int.ote-gdcorp.tools'
    CRMALERT_URL = 'https://crm-alert.cset.int.ote-gdcorp.tools'

    # TODO: LKM - verify this is the correct URL for ote
    NES_URL = 'https://subscriptions-shim-ext.cp.api.ote.godaddy.com/v2/customers/{}/suspendByEntitlementId'

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

    SSO_URL = 'https://sso.dev-gdcorp.tools'
    MIMIR_URL = 'https://mimir.cset.int.dev-gdcorp.tools'
    SHOPLOCKED_URL = 'http://localhost:8080/shoplocked'
    CRMALERT_URL = 'https://crm-alert.cset.int.dev-gdcorp.tools'

    # TODO: LKM - verify this is the correct URL for ote
    NES_URL = 'https://subscriptions-shim-ext.cp.api.dp.godaddy.com/v2/customers/{}/suspendByEntitlementId'

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

    NES_URL = 'https://subscriptions-shim-ext.cp.api.test.godaddy.com/v2/customers/{}/suspendByEntitlementId'

    SSO_URL = 'https://sso.test-gdcorp.tools'
    MIMIR_URL = 'https://mimir.cset.int.test-gdcorp.tools'
    SHOPLOCKED_URL = 'https://shoplocked.cset.int.test-gdcorp.tools'
    CRMALERT_URL = 'https://crm-alert.cset.int.test-gdcorp.tools'

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

    DOMAIN_SERVICE = 'domainservice-rest.abuse-api-dev.svc.cluster.local:8080'

    SLACK_URL = 'test-url'
    SLACK_CHANNEL = 'test-channel'
    NOTIFICATION_LOCK_TIME = 60

    SSO_URL = ''
    MIMIR_URL = ''
    CRMALERT_URL = ''


config_by_name = {'dev': DevelopmentAppConfig, 'prod': ProductionAppConfig, 'ote': OTEAppConfig, 'unit-test': UnitTestConfig, 'test': TestAppConfig}
