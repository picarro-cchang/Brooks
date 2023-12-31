#   -*- coding: utf-8 -*-
"""
This file is based on the integration test plugin shipped with PyBuilder
1. New task "run_integration_testing" is defined, and this task doesn't depend on task package 
    defined in python.core plugin.
2. Use "-O" switch when running python files.
3. Test environment needs to inherit from process environment.
"""

import multiprocessing
import os
import sys

try:
    from queue import Empty
except ImportError:
    from Queue import Empty

from pybuilder.core import init, use_plugin, task, description
from pybuilder.utils import discover_files_matching, execute_command, Timer, read_file
from pybuilder.terminal import print_text_line, print_file_content, print_text
from pybuilder.plugins.python.test_plugin_helper import ReportsProcessor
from pybuilder.terminal import styled_text, fg, GREEN, MAGENTA, GREY

use_plugin("python.core")


@init
def initialize_integrationtest_plugin(project):
    project.set_property_if_unset("dir_source_integrationtest_python", "src/integrationtest/python")
    project.set_property_if_unset("integrationtest_file_glob", "*_tests.py")
    project.set_property_if_unset("integrationtest_file_suffix", None)  # deprecated, use integrationtest_file_glob.
    project.set_property_if_unset("integrationtest_additional_environment", {})
    # Need "DISPLAY" and other properties from process environment
    project.set_property_if_unset("integrationtest_inherit_environment", True)
    project.set_property_if_unset("integrationtest_always_verbose", False)


@task
@description("Runs integration tests based on Python's unittest module")
def run_integration_testing(project, logger):
    if not project.get_property("integrationtest_parallel"):
        reports, total_time = run_integration_tests_sequentially(project, logger)
    else:
        reports, total_time = run_integration_tests_in_parallel(project, logger)

    reports_processor = ReportsProcessor(project, logger)
    reports_processor.process_reports(reports, total_time)
    reports_processor.report_to_ci_server(project)
    reports_processor.write_report_and_ensure_all_tests_passed()


def run_integration_tests_sequentially(project, logger):
    logger.debug("Running integration tests sequentially")
    reports_dir = prepare_reports_directory(project)

    report_items = []

    total_time = Timer.start()

    for test in discover_integration_tests_for_project(project, logger):
        report_item = run_single_test(logger, project, reports_dir, test)
        report_items.append(report_item)

    total_time.stop()

    return report_items, total_time


def run_integration_tests_in_parallel(project, logger):
    logger.info("Running integration tests in parallel")
    tests = multiprocessing.Queue()
    reports = ConsumingQueue()
    reports_dir = prepare_reports_directory(project)
    cpu_scaling_factor = project.get_property('integrationtest_cpu_scaling_factor', 4)
    cpu_count = multiprocessing.cpu_count()
    worker_pool_size = cpu_count * cpu_scaling_factor
    logger.debug("Running integration tests in parallel with {0} processes ({1} cpus found)".format(worker_pool_size, cpu_count))

    total_time = Timer.start()
    # fail OSX has no sem_getvalue() implementation so no queue size
    total_tests_count = 0
    for test in discover_integration_tests_for_project(project, logger):
        tests.put(test)
        total_tests_count += 1
    progress = TaskPoolProgress(total_tests_count, worker_pool_size)

    def pick_and_run_tests_then_report(tests, reports, reports_dir, logger, project):
        while True:
            try:
                test = tests.get_nowait()
                report_item = run_single_test(logger, project, reports_dir, test, not progress.can_be_displayed)
                reports.put(report_item)
            except Empty:
                break
            except Exception as e:
                logger.error("Failed to run test %r : %s" % (test, str(e)))
                failed_report = {"test": test, "test_file": test, "time": 0, "success": False, "exception": str(e)}
                reports.put(failed_report)
                continue

    pool = []
    for i in range(worker_pool_size):
        p = multiprocessing.Process(target=pick_and_run_tests_then_report, args=(tests, reports, reports_dir, logger, project))
        pool.append(p)
        p.start()

    import time
    while not progress.is_finished:
        reports.consume_available_items()
        finished_tests_count = reports.size
        progress.update(finished_tests_count)
        progress.render_to_terminal()
        time.sleep(1)

    progress.mark_as_finished()

    total_time.stop()

    return reports.items, total_time


def discover_integration_tests(source_path, suffix=".py"):
    return discover_files_matching(source_path, "*{0}".format(suffix))


def discover_integration_tests_matching(source_path, file_glob):
    return discover_files_matching(source_path, file_glob)


def discover_integration_tests_for_project(project, logger=None):
    integrationtest_source_dir = project.expand_path("$dir_source_integrationtest_python")
    integrationtest_suffix = project.get_property("integrationtest_file_suffix")
    if integrationtest_suffix is not None:
        if logger is not None:
            logger.warn("integrationtest_file_suffix is deprecated, please use integrationtest_file_glob")
        project.set_property("integrationtest_file_glob", "*{0}".format(integrationtest_suffix))
    integrationtest_glob = project.expand("$integrationtest_file_glob")
    return discover_files_matching(integrationtest_source_dir, integrationtest_glob)


def add_additional_environment_keys(env, project):
    additional_environment = project.get_property("integrationtest_additional_environment", {})
    if not isinstance(additional_environment, dict):
        raise ValueError("Additional environment %r is not a map." % additional_environment)
    for key in additional_environment:
        env[key] = additional_environment[key]


def inherit_environment(env, project):
    if project.get_property("integrationtest_inherit_environment", False):
        for key in os.environ:
            if key not in env:
                env[key] = os.environ[key]


def prepare_environment(project):
    env = {
        "PYTHONPATH":
        os.pathsep.join((
            # Add sandbox into python searching path
            # Note that src/main/python is NOT in the environment of this process
            project.expand_path("$dir_dist"),
            project.expand_path("$dir_source_integrationtest_python")))
    }

    inherit_environment(env, project)

    add_additional_environment_keys(env, project)

    return env


def prepare_reports_directory(project):
    reports_dir = project.expand_path("$dir_reports/integrationtests")
    if not os.path.exists(reports_dir):
        os.mkdir(reports_dir)
    return reports_dir


def run_single_test(logger, project, reports_dir, test, output_test_names=True):
    additional_integrationtest_commandline_text = project.get_property("integrationtest_additional_commandline", "")

    if additional_integrationtest_commandline_text:
        additional_integrationtest_commandline = tuple(additional_integrationtest_commandline_text.split(" "))
    else:
        additional_integrationtest_commandline = ()

    name, _ = os.path.splitext(os.path.basename(test))

    if output_test_names:
        logger.info("Running integration test %s", name)

    env = prepare_environment(project)
    test_time = Timer.start()
    # use -O switch below since only pyo files are in sandbox
    command_and_arguments = (sys.executable, "-O", test)
    command_and_arguments += additional_integrationtest_commandline

    report_file_name = os.path.join(reports_dir, name)
    error_file_name = report_file_name + ".err"
    return_code = execute_command(command_and_arguments, report_file_name, env, error_file_name=error_file_name)
    test_time.stop()
    report_item = {"test": name, "test_file": test, "time": test_time.get_millis(), "success": True}
    if return_code != 0:
        logger.error("Integration test failed: %s", test)
        report_item["success"] = False

        if project.get_property("verbose") or project.get_property("integrationtest_always_verbose"):
            print_file_content(report_file_name)
            print_text_line()
            print_file_content(error_file_name)
            report_item['exception'] = ''.join(read_file(error_file_name)).replace('\'', '')
    elif project.get_property("integrationtest_always_verbose"):
        print_file_content(report_file_name)
        print_text_line()
        print_file_content(error_file_name)

    return report_item


class ConsumingQueue(object):
    def __init__(self):
        self._items = []
        self._queue = multiprocessing.Queue()

    def consume_available_items(self):
        try:
            while True:
                item = self.get_nowait()
                self._items.append(item)
        except Empty:
            pass

    def put(self, *args, **kwargs):
        return self._queue.put(*args, **kwargs)

    def get_nowait(self, *args, **kwargs):
        return self._queue.get_nowait(*args, **kwargs)

    @property
    def items(self):
        return self._items

    @property
    def size(self):
        return len(self.items)


class TaskPoolProgress(object):
    """
    Class that renders progress for a set of tasks run in parallel.
    The progress is based on
    * the amount of total tasks, which must be static
    * the amount of workers running in parallel.
    The bar can be updated with the amount of tasks that have been successfully
    executed and render its progress.
    """

    BACKSPACE = "\b"
    FINISHED_SYMBOL = "-"
    PENDING_SYMBOL = "/"
    WAITING_SYMBOL = "|"
    PACMAN_FORWARD = "ᗧ"
    NO_PACMAN = ""

    def __init__(self, total_tasks_count, workers_count):
        self.total_tasks_count = total_tasks_count
        self.finished_tasks_count = 0
        self.workers_count = workers_count
        self.last_render_length = 0

    def update(self, finished_tasks_count):
        self.finished_tasks_count = finished_tasks_count

    def render(self):
        pacman = self.pacman_symbol
        finished_tests_progress = styled_text(self.FINISHED_SYMBOL * self.finished_tasks_count, fg(GREEN))
        running_tasks_count = self.running_tasks_count
        running_tests_progress = styled_text(self.PENDING_SYMBOL * running_tasks_count, fg(MAGENTA))
        waiting_tasks_count = self.waiting_tasks_count
        waiting_tasks_progress = styled_text(self.WAITING_SYMBOL * waiting_tasks_count, fg(GREY))
        trailing_space = ' ' if not pacman else ''

        return "[%s%s%s%s]%s" % (finished_tests_progress, pacman, running_tests_progress, waiting_tasks_progress, trailing_space)

    def render_to_terminal(self):
        if self.can_be_displayed:
            text_to_render = self.render()
            characters_to_be_erased = self.last_render_length
            self.last_render_length = len(text_to_render)
            text_to_render = "%s%s" % (characters_to_be_erased * self.BACKSPACE, text_to_render)
            print_text(text_to_render, flush=True)

    def mark_as_finished(self):
        if self.can_be_displayed:
            print_text_line()

    @property
    def pacman_symbol(self):
        if self.is_finished:
            return self.NO_PACMAN
        else:
            return self.PACMAN_FORWARD

    @property
    def running_tasks_count(self):
        pending_tasks = (self.total_tasks_count - self.finished_tasks_count)
        if pending_tasks > self.workers_count:
            return self.workers_count
        return pending_tasks

    @property
    def waiting_tasks_count(self):
        return self.total_tasks_count - self.finished_tasks_count - self.running_tasks_count

    @property
    def is_finished(self):
        return self.finished_tasks_count == self.total_tasks_count

    @property
    def can_be_displayed(self):
        if sys.stdout.isatty():
            return True
        return False
