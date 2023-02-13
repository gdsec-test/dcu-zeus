from redis import Redis

from zeus.persist.timeout import timeout


class Throttle(object):
    # This class is used to create a Redis key, with a time to live, which is referred to
    # so that we don't spam shoppers for the same domain, when they have multiple registered
    # only abuse complaints submitted against a specific domain.  A shopper will only be
    # sent one abuse notification email, per domain, for any 24hr period

    def __init__(self, redis_host, lock_time):
        try:
            self.redis = Redis(redis_host)
            self.ttl = lock_time
        except Exception as e:
            raise RuntimeError(f'No Redis connection: {e}')

    @timeout()
    def _get_anti_spam_key(self, key: str) -> bool:
        #  If a redis key exists for the key (domain, shopper id, reporter email, or guid), then we have sent an abuse
        #  email within the last 24hrs.  This was enacted so we don't `spam` shoppers. Since Redis connections can take
        #  quite some time to timeout, I am adding a timeout decorator, which must be suffixed with parenthesis to
        #  avoid: TypeError: decorator() takes exactly 1 argument (2 given)
        try:
            return self.redis.get(key)
        except Exception as e:
            raise RuntimeError(f'No Redis connection to get key: {e}')

    @timeout()
    def _set_anti_spam_key(self, key: str) -> None:
        try:
            self.redis.set(key, 1)
            self.redis.expire(key, self.ttl)
        except Exception as e:
            raise RuntimeError(f'No Redis connection to set key: {e}')

    def key_exists(self, domain: str) -> bool:
        return self._get_anti_spam_key(domain)

    def set_key(self, domain: str) -> None:
        self._set_anti_spam_key(domain)

    ''' Domain specific time outs '''

    def can_shopper_email_be_sent(self, domain: str) -> bool:
        if not self._get_anti_spam_key(domain):
            self._set_anti_spam_key(domain)
            return True
        return False

    def can_ssl_revocation_email_be_sent(self, domain: str) -> bool:
        ssl_cert_key = f'ssl_revocation_{domain}'
        if not self._get_anti_spam_key(ssl_cert_key):
            self._set_anti_spam_key(ssl_cert_key)
            return True
        return False

    def can_suspend_domain(self, domain: str) -> bool:
        domain_key = f'{domain}_domain_suspended'
        if not self._get_anti_spam_key(domain_key):
            self._set_anti_spam_key(domain_key)
            return True
        return False

    ''' GUID specific time outs '''

    def can_suspend_hosting_product(self, guid: str) -> bool:
        hosting_key = f'{guid}_hosting_suspended'
        if not self._get_anti_spam_key(hosting_key):
            self._set_anti_spam_key(hosting_key)
            return True
        return False

    ''' Slack specific time outs '''

    def can_slack_message_be_sent(self, key: str) -> bool:
        if not self._get_anti_spam_key(key):
            self._set_anti_spam_key(key)
            return True
        return False

    ''' Shopper ID specific time outs '''

    def can_crm_be_notated(self, key: str) -> bool:
        crm_key = f'{key}_notated_24hr_hold'
        if not self._get_anti_spam_key(crm_key):
            self._set_anti_spam_key(crm_key)
            return True
        return False

    # Changed from domain to shopper id. By domain generates too many messages to the fraud team.
    def can_fraud_email_be_sent(self, shopper_id: str) -> bool:
        fraud_key = f'fraud_hold_{shopper_id}'
        if not self._get_anti_spam_key(fraud_key):
            self._set_anti_spam_key(fraud_key)
            return True
        return False

    ''' Non shopper specific time outs '''

    def can_reporter_acknowledge_email_be_sent(self, reporter_email: str) -> bool:
        crm_key = f'{reporter_email}_acknowledge_email'
        if not self._get_anti_spam_key(crm_key):
            self._set_anti_spam_key(crm_key)
            return True
        return False
