# support document created to provide additional resources to Care Agents
support_doc = "See http://x.co/dcuwhat2do for more info."

# SHOPLOCKED CRM notes for Admin Locked accounts
INTENTIONALLY_MALICIOUS_ADMINLOCK = "Account locked for abuse. Do not unlock the account. {}".format(support_doc)
SHOPPER_COMPROMISE_ADMINLOCK = "Shopper Account Possibly Compromised. Assist customer with changing password(s) and unlocking account. {}".format(support_doc)

note_mappings = {
    'hosted': {
        'customerWarning': {
            'crm': "Warning sent to customer for {{guid}}. {{type}} content reported at {{location}} {}".format
            (support_doc)
        },
        'contentRemoved': {
            'crm': "{{type}} content removed and/or disabled from hosting {{guid}} at {{location}} {}".format
            (support_doc)
        },
        'repeatOffender': {
            'crm': "Hosting {{guid}} suspended for excessive repeat occurences. {{type}} content reported at {{location}} {}".format(support_doc)
        },
        'suspension': {
            'crm': "Hosting {{guid}} suspended. {{type}} content still present at {{location}} {}".format(support_doc)
        },
        'intentionallyMalicious': {
            'crm': "Hosting {{guid}} suspended for intentional {{type}} at {{location}} {}".format(support_doc),
            'shoplocked': INTENTIONALLY_MALICIOUS_ADMINLOCK
        },
        'shopperCompromise': {
            'crm': "Hosting {{guid}} suspended for {{type}} at {{location}} as a result of possible shopper account compromise {}".format(support_doc),
            'shoplocked': SHOPPER_COMPROMISE_ADMINLOCK
        },
        'extensiveCompromise': {
            'crm': "Hosting {{guid}} suspended due to extensive compromise. {{type}} content reported at {{location}} {}".format(support_doc)
        },
        'ncmecSubmitted': {
            'mimir': "{type} report submitted to NCMEC for hosting {guid}"
        }
    },
    'registered': {
        'customerWarning': {
            'crm': "Warning sent to customer for {{domain}}. {{type}} content reported at {{location}} {}".format
            (support_doc)
        },
        'suspension': {
            'crm': "{{domain}} suspended. {{type}} content still present at {{location}} {}".format(support_doc)
        },
        'intentionallyMalicious': {
            'crm': "{{domain}} suspended for intentional {{type}} at {{location}} {}".format(support_doc),
            'shoplocked': INTENTIONALLY_MALICIOUS_ADMINLOCK
        },
        'shopperCompromise': {
            'crm': "{{domain}} suspended for {{type}} at {{location}} as a result of possible shopper account compromise {}".format(support_doc),
            'shoplocked': SHOPPER_COMPROMISE_ADMINLOCK
        }
    },
    'journal': {
        'customerWarning': "Customer should remove abusive content associated with incident.",
        'intentionallyMalicious': "Customer engaged in suspected intentionally malicious behavior.",
        'shopperCompromise': "Customer account has possibly been compromised.",
        'suspension': "Customer failed to resolve incident within provided time period.",
        'repeatOffender': "Customer has received excessive repeat occurrences of malicious content reports.",
        'extensiveCompromise': "Customer's hosting is permanently suspended due to extensive compromise."
    }
}

alert_mappings = {
    'hosted': {
        'contentRemoved': "{type} content removed and/or disabled from hosting {domain}. See CRM notes and x.co/dcuwhat2do for more info.",
        'suspend': "Hosting {domain} suspended for {type} content. See CRM notes and x.co/dcuwhat2do for more info."
    },
    'registered': {
        'suspend': "{domain} suspended for {type} content. See CRM notes and x.co/dcuwhat2do for more info."
    }
}
