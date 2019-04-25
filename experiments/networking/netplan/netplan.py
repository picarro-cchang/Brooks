import yaml
import os
import cerberus
from pprint import pprint
from ipaddress import IPv4Interface
from host.experiments.networking.netplan.schema.schema import netplan_schema


def get_ip_with_network_bits(ip, netmask):
    """
    :param ip: Valid IP Address
    :param netmask: Valid Subnet Mask
    :return: IP Address with Network Bits, intended to be used in a netplan
             configuration file (yaml).
    """
    try:
        ip_address = IPv4Interface(ip + '/' + netmask)
        return ip_address
    except ValueError:
        raise


def print_network_configuration(configuration_obj=None, print_format='yaml'):
    """
    :param configuration_obj: Object returned from load_network_configuration()
    :param print_format: Format to print network configuration (yaml(default) or pprint)
    :return:None
    """
    if configuration_obj is not None:
        if print_format.lower() == 'yaml':
            print(yaml.dump(configuration_obj))
        else:
            pprint(configuration_obj)
    else:
        raise ValueError('No configuration_obj passed to '
                         'print_network_configuration function')


def load_network_configuration(configuration_file):
    """
    :param configuration_file: Path of netplan configuration file
    :return: Object of parsed netplan configuration file
    """
    if os.path.exists(configuration_file):
        try:
            with open(configuration_file, 'r') as f:
                configuration = yaml.safe_load(f)
                return configuration
        except PermissionError:
            raise
        except OSError:
            raise

    else:
        print('File does not exist: {}'.format(configuration_file))


def load_yaml_template(setting_type=None):
    """
    :param setting_type: Template to load (static or dhcp)
    :return: Python object of yaml template
    """
    if setting_type is not None:
        if setting_type.lower() == 'dhcp':
            template_file = './templates/dhcp-settings.yaml'
        else:
            template_file = './templates/static-settings.yaml'
        template_obj = load_network_configuration(template_file)
        return template_obj
    else:
        raise ValueError('No setting_type')


def print_yaml_template(template_obj=None, print_format='yaml'):
    print_network_configuration(template_obj, print_format)


if __name__ == '__main__':
    my_ip = get_ip_with_network_bits('192.168.0.0', '255.255.0.0')
    print(my_ip.network)
    my_configuration = load_network_configuration('./templates/static-settings.yaml')
    print_network_configuration(my_configuration, 'object')
    my_template = load_yaml_template('dhcp')
    for adapter in my_template['network']['ethernets']:
        print(my_template['network']['ethernets'][adapter])
        my_template['network']['ethernets'][adapter]['dhcp4'] = True
        print(my_template)
    print_yaml_template(my_template)
    my_validator = cerberus.Validator(netplan_schema)
    print(my_validator.validate(my_template, netplan_schema))
    if my_validator.errors:
        print(my_validator.errors)
