# support document created to provide additional resources to Care Agents
support_doc = "See http://x.co/dcuwhat2do for proper handling."
no_reinstate = "* DO NOT REINSTATE *"
no_unlock_reinstate = "* DO NOT UNLOCK OR REINSTATE *"

# SHOPLOCKED CRM notes for Admin Locked accounts
INTENTIONALLY_MALICIOUS_ADMINLOCK = "Account locked for Abuse. {} {}".format(no_unlock_reinstate, support_doc)
SHOPPER_COMPROMISE_ADMINLOCK = "Account locked for potential Shopper Compromise. Assist customer with changing password(s), unlocking & securing account. {}".format(support_doc)

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
            'crm': "Hosting {{guid}} suspended for Excessive Repeat Occurrences. {{type}} content reported at {{location}} {}".format(support_doc)
        },
        'suspension': {
            'crm': "Hosting {{guid}} suspended. {{type}} Content Still Active After Warning at {{location}} {}".format(support_doc),
            'csam': {
                'mimir': "Hosted domain {domain} suspended",
                'crm': "Hosting {{guid}} permanently suspended. Child Abuse material found {} Any questions and or comments regarding this action reach out to childabuse@".format(no_unlock_reinstate)
            }
        },
        'intentionallyMalicious': {
            'crm': "Hosting {{guid}} permanently suspended for INTENTIONAL {{type}} {} {}".format(no_unlock_reinstate, support_doc),
            'shoplocked': INTENTIONALLY_MALICIOUS_ADMINLOCK
        },
        'shopperCompromise': {
            'crm': "Hosting {{guid}} suspended for {{type}} at {{location}} as a result of possible Shopper Account Compromise {}".format(support_doc),
            'shoplocked': SHOPPER_COMPROMISE_ADMINLOCK
        },
        'extensiveCompromise': {
            'crm': "Hosting {{guid}} permanently suspended due to Extensive Compromise. {} {}".format(no_reinstate, support_doc)
        },
        'ncmecSubmitted': {
            'mimir': "Report submitted to NCMEC for hosted domain {domain}"
        }
    },
    'registered': {
        'customerWarning': {
            'crm': "Warning sent to customer for {{domain}}. {{type}} content reported at {{location}} {}".format
            (support_doc)
        },
        'suspension': {
            'crm': "{{domain}} suspended. {{type}} Content Still Active After Warning at {{location}} {}".format(support_doc),
            'csam': {
                'crm': "{{domain}} permanently suspended. Child Abuse material found {} Any questions and or comments regarding this action reach out to childabuse@".format(no_unlock_reinstate)
            }
        },
        'repeatOffender': {
            'crm': "{{domain}} suspended for Excessive Repeat Occurrences. {} {}".format(no_reinstate, support_doc)
        },
        'intentionallyMalicious': {
            'crm': "{{domain}} permanently suspended for INTENTIONAL {{type}} {} {}".format(no_unlock_reinstate, support_doc),
            'shoplocked': INTENTIONALLY_MALICIOUS_ADMINLOCK
        },
        'shopperCompromise': {
            'crm': "{{domain}} suspended for {{type}} at {{location}} as a result of possible Shopper Compromise {}".format(support_doc),
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
        'contentRemoved': "{type} content removed and/or disabled from hosting {domain}. See CRM notes and x.co/dcuwhat2do for proper handling.",
        'suspend': "Hosting {domain} suspended for {type} content. See CRM notes and x.co/dcuwhat2do for proper handling."
    },
    'registered': {
        'suspend': "{domain} suspended for {type} content. See CRM notes and x.co/dcuwhat2do for proper handling."
    }
}
