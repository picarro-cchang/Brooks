#   -*- coding: utf-8 -*-
"""
This file is modified from the integration test plugin shipped with PyBuilder
Reason for creating this file is that unittest plugin cannot run GUI tests
(stuck at qWait without error msg).
"""

import os
import sys

try:
    from queue import Empty
except ImportError:
    from Queue import Empty


from pybuilder.core import init, use_plugin, task, description, after
from pybuilder.utils import discover_files_matching, execute_command, Timer, read_file
from pybuilder.terminal import print_text_line, print_file_content, print_text
from pybuilder.plugins.python.test_plugin_helper import ReportsProcessor
from pybuilder.terminal import styled_text, fg, GREEN, MAGENTA, GREY

use_plugin("python.core")

@init
def initialize_functionaltest_plugin(project):
    project.set_property_if_unset(
        "dir_source_functionaltest_python", "src/unittest/python")
    project.set_property_if_unset("functionaltest_file_glob", "*_uitests.py")
    project.set_property_if_unset("functionaltest_additional_environment", {})
    project.set_property_if_unset("functionaltest_inherit_environment", True)
    project.set_property_if_unset("functionaltest_always_verbose", False)


@after("run_unit_tests")
def run_functional_tests(project, logger):
    reports, total_time = run_functional_tests_sequentially(
        project, logger)

    reports_processor = ReportsProcessor(project, logger)
    reports_processor.process_reports(reports, total_time)
    reports_processor.report_to_ci_server(project)
    reports_processor.write_report_and_ensure_all_tests_passed()

def run_functional_tests_sequentially(project, logger):
    logger.debug("Running functional tests")
    reports_dir = prepare_reports_directory(project)

    report_items = []

    total_time = Timer.start()

    for test in discover_functional_tests_for_project(project, logger):
        report_item = run_single_test(logger, project, reports_dir, test)
        report_items.append(report_item)

    total_time.stop()

    return report_items, total_time


def discover_functional_tests(source_path, suffix=".py"):
    return discover_files_matching(source_path, "*{0}".format(suffix))


def discover_functional_tests_for_project(project, logger=None):
    functionaltest_source_dir = project.expand_path(
        "$dir_source_functionaltest_python")
    functionaltest_glob = project.expand("$functionaltest_file_glob")
    return discover_files_matching(functionaltest_source_dir, functionaltest_glob)


def add_additional_environment_keys(env, project):
    additional_environment = project.get_property(
        "functionaltest_additional_environment", {})
    if not isinstance(additional_environment, dict):
        raise ValueError("Additional environment %r is not a map." %
                         additional_environment)
    for key in additional_environment:
        env[key] = additional_environment[key]


def inherit_environment(env, project):
    if project.get_property("functionaltest_inherit_environment", False):
        for key in os.environ:
            if key not in env:
                env[key] = os.environ[key]


def prepare_environment(project):
    env = {
        "PYTHONPATH": os.pathsep.join((
            project.expand_path("$dir_source_main_python"),
            project.expand_path("$dir_source_functionaltest_python")))
    }

    inherit_environment(env, project)

    add_additional_environment_keys(env, project)

    return env


def prepare_reports_directory(project):
    reports_dir = project.expand_path("$dir_reports/functionaltests")
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)
    return reports_dir


def run_single_test(logger, project, reports_dir, test, output_test_names=True):
    additional_functionaltest_commandline_text = project.get_property("functionaltest_additional_commandline", "")

    if additional_functionaltest_commandline_text:
        additional_functionaltest_commandline = tuple(additional_functionaltest_commandline_text.split(" "))
    else:
        additional_functionaltest_commandline = ()

    name, _ = os.path.splitext(os.path.basename(test))

    if output_test_names:
        logger.info("Running functional test %s", name)

    env = prepare_environment(project)
    test_time = Timer.start()
    # use -O switch below since only pyo files are in sandbox
    command_and_arguments = (sys.executable, "-O", test)
    command_and_arguments += additional_functionaltest_commandline

    report_file_name = os.path.join(reports_dir, name)
    error_file_name = report_file_name + ".err"
    return_code = execute_command(
        command_and_arguments, report_file_name, env, error_file_name=error_file_name)
    test_time.stop()
    report_item = {
        "test": name,
        "test_file": test,
        "time": test_time.get_millis(),
        "success": True
    }
    if return_code != 0:
        logger.error("Functional test failed: %s", test)
        report_item["success"] = False

        if project.get_property("verbose") or project.get_property("functionaltest_always_verbose"):
            print_file_content(report_file_name)
            print_text_line()
            print_file_content(error_file_name)
            report_item['exception'] = ''.join(read_file(error_file_name)).replace('\'', '')
    elif project.get_property("functionaltest_always_verbose"):
        print_file_content(report_file_name)
        print_text_line()
        print_file_content(error_file_name)

    return report_item