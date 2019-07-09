# support document created to provide additional resources to Care Agents
support_doc = "See http://x.co/dcuwhat2do for more info."

# SHOPLOCKED CRM notes for Admin Locked accounts
INTENTIONALLY_MALICIOUS_ADMINLOCK = "Account locked for abuse. Do not unlock the account. The customer can email the " \
                                    "Digital Crimes Unit at hostsec@, if they have questions."

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
        'extensiveCompromise': {
            'crm': "Hosting {{guid}} suspended due to extensive compromise. {{type}} content reported at {{location}} {}".format(support_doc)
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
        }
    },
    'journal': {
        'customerWarning': "Customer should remove abusive content associated with incident.",
        'intentionallyMalicious': "Customer engaged in suspected intentionally malicious behavior.",
        'suspension': "Customer failed to resolve incident within provided time period.",
        'repeatOffender': "Customer has received excessive repeat occurences of malicious content reports.",
        'extensiveCompromise': "Customer's hosting is permanently suspended due to extensive compromise."
    }
}
