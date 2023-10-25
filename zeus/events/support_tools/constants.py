# support document created to provide additional resources to Care Agents
support_doc = 'See http://secure.godaddy/dcuwhat2do for proper handling. Please see your direct leadership for any problems accessing this page.'
no_reinstate = '* DO NOT REINSTATE *'
no_unlock_reinstate = '* DO NOT UNLOCK OR REINSTATE *'

# SHOPLOCKED CRM notes for Admin Locked accounts
INTENTIONALLY_MALICIOUS_ADMINLOCK = f'Account locked for Abuse. {no_unlock_reinstate} {support_doc}'
SHOPPER_COMPROMISE_ADMINLOCK = f'Account locked for potential Shopper Compromise. Assist customer with changing password(s), unlocking & securing account. {support_doc}'
SHOPPER_COMPROMISE_SCRAMBLE = f'Login credentials scrambled due to potential Shopper Compromise. Assist customer with changing password(s), unlocking & securing account. {support_doc}'

note_mappings = {
    'hosted': {
        'customerWarning': {
            'crm': f'Warning sent to customer for {{guid}}. {{type}} content reported at {{location}} {support_doc}'
        },
        'contentRemoved': {
            'crm': f'{{type}} content removed and/or disabled from hosting {{guid}} at {{location}} {support_doc}'
        },
        'repeatOffender': {
            'crm': f'Hosting {{guid}} suspended for Excessive Repeat Occurrences. {{type}} content reported at {{location}} {support_doc}'
        },
        'suspension': {
            'crm': f'Hosting {{guid}} suspended. {{type}} Content Still Active After Warning at {{location}} {support_doc}',
            'csam': {
                'mimir': 'Hosted domain {domain} suspended',
                'crm': f'Hosting {{guid}} permanently suspended. Child Abuse material found {no_unlock_reinstate} Any questions and or comments regarding this action reach out to childabuse@'
            }
        },
        'intentionallyMalicious': {
            'crm': f'Hosting {{guid}} permanently suspended for INTENTIONAL {{type}} {no_unlock_reinstate} {support_doc}',
            'shoplocked': INTENTIONALLY_MALICIOUS_ADMINLOCK
        },
        'shopperCompromise': {
            'crm': f'Hosting {{guid}} suspended for {{type}} at {{location}} as a result of possible Shopper Account Compromise {support_doc}',
            'shoplocked_lock': SHOPPER_COMPROMISE_ADMINLOCK,
            'shoplocked_scramble': SHOPPER_COMPROMISE_SCRAMBLE
        },
        'extensiveCompromise': {
            'crm': f'Hosting {{guid}} permanently suspended due to Extensive Compromise. {no_reinstate} {support_doc}'
        },
        'ncmecSubmitted': {
            'mimir': 'Report submitted to NCMEC for hosted domain {domain}'
        }
    },
    'registered': {
        'customerWarning': {
            'crm': f'Warning sent to customer for {{domain}}. {{type}} content reported at {{location}} {support_doc}'
        },
        'suspension': {
            'crm': f'{{domain}} suspended. {{type}} Content Still Active After Warning at {{location}} {support_doc}',
            'csam': {
                'crm': f'{{domain}} permanently suspended. Child Abuse material found {no_unlock_reinstate} Any questions and or comments regarding this action reach out to childabuse@'
            }
        },
        'repeatOffender': {
            'crm': f'{{domain}} suspended for Excessive Repeat Occurrences. {no_reinstate} {support_doc}'
        },
        'intentionallyMalicious': {
            'crm': f'{{domain}} permanently suspended for INTENTIONAL {{type}} {no_unlock_reinstate} {support_doc}',
            'shoplocked': INTENTIONALLY_MALICIOUS_ADMINLOCK
        },
        'shopperCompromise': {
            'crm': f'{{domain}} suspended for {{type}} at {{location}} as a result of possible Shopper Compromise {support_doc}',
            'shoplocked_lock': SHOPPER_COMPROMISE_ADMINLOCK,
            'shoplocked_scramble': SHOPPER_COMPROMISE_SCRAMBLE
        }
    }
}

alert_mappings = {
    'hosted': {
        'contentRemoved': '{type} content removed and/or disabled from hosting {domain}. See CRM notes and secure.godaddy/dcuwhat2do for proper handling.',
        'suspend': 'Hosting {domain} suspended for {type} content. See CRM notes and secure.godaddy/dcuwhat2do for proper handling.'
    },
    'registered': {
        'suspend': '{domain} suspended for {type} content. See CRM notes and secure.godaddy/dcuwhat2do for proper handling.'
    }
}
