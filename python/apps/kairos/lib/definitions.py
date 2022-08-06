source = {
        'source': 'str'
        }

find = {
        "find": {
            "obligatory": {
                'enabled': 'bool',
                'endpoint': 'str'
                },
            'optional': {
                'generalFaceDectDbFile':    'str',
                'checkBlackList':           'bool',
                'blacklistDbFile':          'str',
                'checkWhiteList':           'bool',
                'whitelistDbFile':          'str',
                'ignorePreviousDb':         'bool',
                'saveFacesDb':              'bool'
                }
            },
        }

blacklist = {
        "blackList": {
            'obligatory': {
                'enabled':  'bool',
                'endpoint': 'str'
                },
            'optional': {
                'dbName':   'str'
                }
            }
        }

whitelist = {
        "whiteList": {
            'obligatory': {
                'enabled':  'bool',
                'endpoint': 'str'
                },
            'optional': {
                'dbName':   'str'
                }
            }
        }

recurrence = {
        "recurrence": {
            'obligatory': {
                'enabled':  'bool',
                'endpoint': 'str'
                },
            'optional': {
                'generalFaceDectDbFile':    'str',
                'checkBlackList':           'bool',
                'blacklistDbFile':          'str',
                'checkWhiteList':           'bool',
                'whitelistDbFile':          'str'
                }
            }
        }

ageGender = {
        "ageAndGender": {
            'obligatory': {
                'enabled':  'bool',
                'endpoint': 'str'
                },
            'optional': {
                'generalFaceDectDbFile':    'str',
                'ignorePreviousDb':         'bool',
                'saveFacesDb':              'bool'
                }
            }
        }
