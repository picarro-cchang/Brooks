"""
    This file contains the class RT_policy_manager.
    Its purpose it so handle all manipulations with retention policies.
"""

from influxdb import InfluxDBClient
import common.duration_tools as dt
from back_end.lologger.lologger_client import LOLoggerClient


class RTPolicyManager(object):
    """
        Class to deal with retention policies.
    """
    def __init__(self, client=None, db_name=None, db_host_address="localhost", db_port=8086, logger=None, verbose=True):
        self.client = None
        if client is not None:
            self.client = client
        if db_name is not None:
            self.client = InfluxDBClient(host=db_host_address, port=db_port)
            self.client.switch_database(self.db_name)
            self.db_name = db_name
        if self.client is None:
            raise TypeError("Either client or db_name has to be supplied")

        # logger params
        if isinstance(logger, str):
            self.logger = LOLoggerClient(client_name=logger)
        elif isinstance(logger, LOLoggerClient):
            self.logger = logger
        else:
            self.logger = LOLoggerClient(client_name=self.__class__.__name__, verbose=verbose)

    def get_retention_policies_as_dict(self):
        return {i["name"]: i["duration"] for i in self.get_raw_retention_policies()}

    def get_raw_retention_policies(self):
        return self.client.get_list_retention_policies()

    def create_retention_policy(self, name, duration="INF"):
        """
            Method to create a retention policy.
            If retention policy with that name exists - it will alter it
        """
        if not dt.check_for_valid_literal_duration(duration):
            raise ValueError(f"Bad duration: {duration}")
        if self.check_if_policy_exists(name):
            # if policy already exists - just change it
            self.logger.debug(f"Retention policy {name} already exists")
            self.alter_retention_policy(name, duration)
        else:
            self.client.create_retention_policy(name=name, duration=duration, replication=1, shard_duration='0s')
            self.logger.debug(f"Retention policy {name} with duration {duration} has been created")
        return True

    def alter_retention_policy(self, name, duration):
        """Method to alter a retention policy."""
        if not self.check_if_policy_exists(name):
            self.logger.error(f"Tried to alter non existed retention policy f{name}")
            raise ValueError(f"Tried to alter non existed retention policy f{name}")

        if not dt.check_for_valid_literal_duration(duration):
            raise ValueError(f"Bad duration: {duration}")

        self.logger.debug(f"Altering retention_policies {name} to be {duration}")
        self.client.alter_retention_policy(name, duration=duration, shard_duration=self._calculate_shard_policy_duraion(duration))

    def check_if_policy_exists(self, policy):
        return policy in self.get_retention_policies_as_dict()

    def compare_and_fix(self, p_policies):
        """
            This method will compare passed retention policies to existed
            and if there is a difference - it will change existed policies
        """
        if not isinstance(p_policies, dict):
            raise TypeError(f"p_policies has to be a dictionary, got {type(p_policies)}")
        e_policies = self.get_retention_policies_as_dict()
        for policy in p_policies:
            if policy not in e_policies:
                # passed policy doesn't exist - so we gonna create it
                self.create_retention_policy(name=policy, duration=p_policies[policy])
            elif not (dt.generate_duration_in_seconds(e_policies[policy]) == dt.generate_duration_in_seconds(p_policies[policy])):
                self.logger.debug(f"policy {policy} found to be {e_policies[policy]}, fixing it to be {p_policies[policy]}")
                # passed policy doesn't match existed one - so we gonna alter existed
                self.alter_retention_policy(name=policy, duration=p_policies[policy])

    def _calculate_shard_policy_duraion(self, duration):
        """ Just get half of the duration"""
        return dt.generate_duration_literal(int(dt.generate_duration_in_seconds(duration, ms=False) / 2))

    def delete_all_retention_policies(self):
        """
            This method will delete all non default retention policies
        """
        # for dev only!!!!
        policies = self.get_raw_retention_policies()
        for policy in policies:
            if not policy["default"]:
                self.delete_retention_policy(policy["name"])

    def delete_retention_policy(self, name):
        """
            Delete retention policy with passed name.
            That will delete all the data, that belongs to this retention policy,
            so only use it if you are aware of what is the data do be dropped and you are sure.
        """
        self.logger.debug(f"Droping retention policy {name}")
        self.client.drop_retention_policy(name)

    def make_sure_policy_exists(self, policy):
        """
            If policy with a given name doesn't exist - make it with infinite duraion
        """
        if not self.check_if_policy_exists(policy):
            self.create_retention_policy(name=policy)
