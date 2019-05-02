# TODO -
#   Allow any ethernet name in place of 'eno1' and 'enp3s0' dicts

netplan_schema = {
    'network': {
        'required': True,
        'type': 'dict',
        'schema': {
            'version': {
                'required': True,
                'type': 'number'
            },
            'renderer': {
                'required': True,
                'type': 'string'
            },
            'ethernets': {
                'required': True,
                'type': 'dict',
                'allow_unknown': True,
                'schema': {
                    'eno1': {
                        'required': True,
                        'type': 'dict',
                        'schema': {
                            'dhcp4': {
                                'required': True,
                                'type': 'boolean'
                            },
                            'dhcp6': {
                                'required': True,
                                'type': 'boolean'
                            },
                            'addresses': {
                                'required': False,
                                'type': 'list'
                            },
                            'gateway4': {
                                'required': False,
                                'type': 'string'
                            },
                            'nameservers': {
                                'required': False,
                                'type': 'dict',
                                'schema': {
                                    'addresses': {
                                        'required': False,
                                        'type': 'list'
                                    }
                                }
                            }
                        }
                    },
                    'enp3s0': {
                        'required': False,
                        'type': 'dict',
                        'schema': {
                            'dhcp4': {
                                'required': True,
                                'type': 'boolean'
                            },
                            'dhcp6': {
                                'required': True,
                                'type': 'boolean'
                            },
                            'addresses': {
                                'required': False,
                                'type': 'list'
                            },
                            'gateway4': {
                                'required': False,
                                'type': 'string'
                            },
                            'nameservers': {
                                'required': False,
                                'type': 'dict',
                                'schema': {
                                    'addresses': {
                                        'required': False,
                                        'type': 'list'
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}
