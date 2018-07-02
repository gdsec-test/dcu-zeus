from redis import Redis
from zeus.persist.timeout import timeout


class Persist(object):
    # This class is used to create a Redis key, with a time to live, which is referred to
    # so that we don't spam shoppers for the same domain, when they have multiple registered
    # only abuse complaints submitted against a specific domain.  A shopper will only be
    # sent one abuse notification email, per domain, for any 24hr period

    def __init__(self, redis_host, lock_time):
        try:
            self.redis = Redis(redis_host)
            self.ttl = lock_time
        except Exception as e:
            raise RuntimeError('No Redis connection: {}'.format(e.message))

    @timeout()
    def _get_anti_spam_key(self, key):
        #  If a redis key exists for the domain, then we have sent an abuse email
        #  within the last 24hrs.  This was enacted so we dont `spam` shoppers.
        #  Since Redis connections can take quite some time to timeout, I am adding a
        #  timeout decorator, which must be suffixed with parenthesis to avoid:
        #  TypeError: decorator() takes exactly 1 argument (2 given)
        try:
            return self.redis.get(key)
        except Exception as e:
            raise RuntimeError('No Redis connection to get key: {}'.format(e.message))

    @timeout()
    def _set_anti_spam_key(self, key):
        try:
            self.redis.set(key, 1)
            self.redis.expire(key, self.ttl)
        except Exception as e:
            raise RuntimeError('No Redis connection to set key: {}'.format(e.message))

    def key_exists(self, domain):
        if self._get_anti_spam_key(domain):
            return True
        return False

    def set_key(self, domain):
        self._set_anti_spam_key(domain)

    ''' Domain specific time outs '''

    def can_shopper_email_be_sent(self, domain):
        if not self._get_anti_spam_key(domain):
            self._set_anti_spam_key(domain)
            return True
        return False

    def can_fraud_email_be_sent(self, domain):
        fraud_key = 'fraud_hold_{}'.format(domain)
        if not self._get_anti_spam_key(fraud_key):
            self._set_anti_spam_key(fraud_key)
            return True
        return False

    def can_suspend_hosting_product(self, guid):
        hosting_key = '{}_hosting_suspended'.format(guid)
        if not self._get_anti_spam_key(hosting_key):
            self._set_anti_spam_key(hosting_key)
            return True
        return False

    def can_suspend_domain(self, domain):
        domain_key = '{}_domain_suspended'.format(domain)
        if not self._get_anti_spam_key(domain_key):
            self._set_anti_spam_key(domain_key)
            return True
        return False

    def can_crm_be_notated(self, shopper_id):
        crm_key = '{}_notated_24hr_hold'.format(shopper_id)
        if not self._get_anti_spam_key(crm_key):
            self._set_anti_spam_key(crm_key)
            return True
        return False

    def can_slack_message_be_sent(self, key):
        if not self._get_anti_spam_key(key):
            self._set_anti_spam_key(key)
            return True
        return False
