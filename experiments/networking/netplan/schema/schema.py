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
                'type': 'dict'
            }
        }
    }
}