import re


def sanitize_url(url):
    return re.sub(r'^http', 'hxxp', url)


def _get_domain_query(dict_to_search):
    return dict_to_search.get('data', {}).get('domainQuery', {})


def get_shopper_id_from_dict(dict_to_search):
    #  The shopperid field currently appears in two places.
    #    1: data->domainQuery->host->shopperId
    #    2: data->domainQuery->shopperInfo->shopperId
    #  BUT SINCE THIS IS DMV, WE ONLY CARE ABOUT THE 2ND LOCATION
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get('shopperInfo', {}).get('shopperId')
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
                    # Check for an address containing the string 'abuse'
                    if any(x in address.lower() for x in ['abuse', 'noc']):
                        host_abuse_email.append(address)
                # If no address containing 'abuse' was found, then just grab the first address
                if not host_abuse_email and hosting_abuse_list:
                    host_abuse_email.append(hosting_abuse_list[0])
            elif isinstance(hosting_abuse_list, basestring):
                host_abuse_email.append(hosting_abuse_list)
    return host_abuse_email


def get_host_brand_from_dict(dict_to_search):
    #  The brand field currently appears in...
    #    1: data->domainQuery->host->brand
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get('host', {}).get('brand')
    return None


def get_host_shopper_id_from_dict(dict_to_search):
    #  The host shopperId field currently appears in...
    #    1: data->domainQuery->host->shopperId
    if isinstance(dict_to_search, dict):
        return _get_domain_query(dict_to_search).get('host', {}).get('shopperId')
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


def get_list_of_ids_to_notify(data):
    # If the domain is associated with a parent/child API reseller
    #  account, then email both the parent and child account
    account_number_list = []
    parent_child_list = get_parent_child_shopper_ids_from_dict(data)
    if not parent_child_list:
        shopper_id = get_shopper_id_from_dict(data)
        if shopper_id:
            account_number_list.append(shopper_id)
    else:
        account_number_list = parent_child_list
    return account_number_list
