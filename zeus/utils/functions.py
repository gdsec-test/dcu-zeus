import re


def sanitize_url(url, replace_email='redacted@redacted.tld'):
    email_id_regex = re.compile(r'\b[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,63}\b', re.IGNORECASE | re.MULTILINE)
    redact_email = re.sub(email_id_regex, replace_email, url)
    return re.sub(r'^http', 'hxxp', redact_email)


def _get_domain_query(dict_to_search):
    return dict_to_search.get('data', {}).get('domainQuery', {})


def get_domain_id_from_dict(dict_to_search):
    #  The domainId field is located in...
    #    1: data->domainQuery->registrar->domainId
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get('registrar', {}).get('domainId')
    return None


def get_parent_child_shopper_ids_from_dict(dict_to_search):
    #  The parent/child API reseller fields currently appears in...
    #    1: data->domainQuery->apiReseller->parent
    #    2: data->domainQuery->apiReseller->child
    if isinstance(dict_to_search, dict):
        parent = _get_domain_query(dict_to_search).get('apiReseller', {}).get('parent')
        if not parent:
            return None
        child = _get_domain_query(dict_to_search).get('apiReseller', {}).get('child')
        return [parent, child]
    return None


def get_domain_create_date_from_dict(dict_to_search):
    #  The domainCreateDate field currently appears in...
    #    1: data->domainQuery->registrar->domainCreateDate
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get('registrar', {}).get('domainCreateDate')
    return None


def get_shopper_create_date_from_dict(dict_to_search):
    #  The shopperCreateDate field currently appears in...
    #    1: data->domainQuery->shopperInfo->shopperCreateDate
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get('shopperInfo', {}).get('shopperCreateDate')
    return None


def get_host_abuse_email_from_dict(dict_to_search):
    #  The hostingAbuseEmail field currently appears in...
    #    1: data->domainQuery->host->hostingAbuseEmail
    host_abuse_email = []
    if isinstance(dict_to_search, dict):
        hosting_abuse_list = _get_domain_query(dict_to_search).get('host', {}).get('hostingAbuseEmail')
        if hosting_abuse_list is not None:
            if isinstance(hosting_abuse_list, list):
                for address in hosting_abuse_list:
                    # When presented with a list of email addresses, we prefer to send to one
                    #  with the following substrings
                    if any(x in address.lower() for x in ['abuse', 'noc']):
                        host_abuse_email.append(address)
                # If no address containing those substrings was found, then just grab the first address
                if not host_abuse_email and hosting_abuse_list:
                    host_abuse_email.append(hosting_abuse_list[0])
            elif isinstance(hosting_abuse_list, str):
                host_abuse_email.append(hosting_abuse_list)
    return host_abuse_email


def get_host_brand_from_dict(dict_to_search):
    #  The brand field currently appears in...
    #    1: data->domainQuery->host->brand
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get('host', {}).get('brand')
    return None

def get_host_customer_id_from_dict(dict_to_search):
    # The host customerId field currently appears in
    #   1: data->domainQuery->host->customerId
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get("host", {}).get('customerId', None)
    return None

def get_hosting_created_date_from_dict(dict_to_search):
    #  The hosting createdDate field currently appears in...
    #    1: data->domainQuery->host->createdDate
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get('host', {}).get('createdDate')
    return None

def get_host_info_from_dict(dict_to_search):
    #  The hosting information currently appears in one place.
    #    1: data->domainQuery->host
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get('host', {})
    return {}


def get_ssl_subscriptions_from_dict(data):
    # Return the ssl subscription information associated with the account
    return _get_domain_query(data).get('sslSubscriptions', [])


def get_kelvin_domain_id_from_dict(dict_to_search):
    #  The domainId field is located in...
    #    1: domain->domainId
    if isinstance(dict_to_search, dict):
        return dict_to_search.get('domain', {}).get('domainId')
    return None


def get_sucuri_product_from_dict(dict_to_search):
    #  The sucuriProduct field currently appears in...
    #    1: data->domainQuery->securitySubscription->sucuriProduct
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get('securitySubscription', {}).get('sucuriProduct', [])
    return []


def get_high_value_domain_from_dict(data):
    #  The isDomainHighValue field currently appears in...
    #    1: data->domainQuery->isDomainHighValue
    if isinstance(data, dict):
        return _get_domain_query(data).get('isDomainHighValue')
    return None
