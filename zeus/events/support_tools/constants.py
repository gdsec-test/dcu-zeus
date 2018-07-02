# NETVIO defined here for readability
CONTENT_REMOVED = '{ticket_id} - {guid} was found to have {type} content at {location}.\n' \
                  'The following files/directories have been removed:\n{content_removed}'
SUSPENSION = '{ticket_id} - {guid} has been suspended by DCU-Eng; ' \
             '{type} content at {location}'
INTENTIONALLY_MALICIOUS = '{ticket_id}: hosting {guid} suspended for intentional ' \
                          '{type} at {location}'

CUSTOMER_WARNING = '{ticket_id} - {guid} has {type} content at {location}, the customer has ' \
                   'been given a 24hr warning to remove any and all malicious content or their services ' \
                   'will be suspended.'

note_mappings = {
    'hosted': {
        'customerWarning': {
            'netvio': CUSTOMER_WARNING,
            'crm': 'Warning sent to customer for {guid}. {type} content reported at {location}',
        },
        'contentRemoved': {
            'netvio': CONTENT_REMOVED,
            'crm': '{type} content removed from hosting {guid} at {location}',
        },
        'suspension': {
            'netvio': SUSPENSION,
            'crm': 'Hosting {guid} suspended. {type} content still present at {location}'
        },
        'intentionallyMalicious': {
            'netvio': INTENTIONALLY_MALICIOUS,
            'crm': 'Hosting {guid} suspended for intentional {type} at {location}'
        }
    },
    'registered': {
        'customerWarning': {
            'crm': 'Warning sent to customer for {domain}. {type} content reported at {location}'
        },
        'suspension': {
            'crm': '{domain} suspended. {type} content still present at {location}'
        },
        'intentionallyMalicious': {
            'crm': '{domain} suspended for intentional {type} at {location}'
        }
    }
}
