import os
import os.path
import sys
from functools import wraps
from typing import List
from integrations_testing_framework import utils, intercepted_stdout


def write_stdout(file_uri: str):
    def decorator(func):

        @wraps(func)
        def inner():
            sys.stdout = intercepted_stdout
            sys.stdout.truncate(0)
            sys.stdout.seek(0)
            try:
                func()
                sys.stdout.seek(0)
                with open(file_uri, 'w') as file:
                    lines = sys.stdout.readlines()
                    if len(lines) == 0:
                        raise Exception("Stdout is empty")
                    file.writelines(lines)
            finally:
                sys.stdout.truncate(0)  # ensure stdout is cleared

        return inner

    return decorator


def assert_stdout_matches(file_uri: str):
    """
    A decorator that will temporary redirect the stdout to an in-memory file, and then assert whether
    the contents written to stdout match the contents of the supplied matching file.
    """

    if not os.path.isfile(file_uri):
        raise FileNotFoundError(f'File does not exist: {file_uri}')

    def decorator(func):
        @wraps(func)
        def inner():
            sys.stdout = intercepted_stdout
            sys.stdout.truncate(0)
            sys.stdout.seek(0)
            try:
                func()
                sys.stdout.seek(0)
                with open(file_uri, 'r') as file:
                    utils.assert_matching_file_contents(file, sys.stdout)
            finally:
                sys.stdout.truncate(0)  # ensure stdout is cleared

        return inner

    return decorator


def with_sys_args(args: List[str]):
    """
    This decorator sets the supplied arguments to the sys.argv variable, executes the wrapped function and resets to the original sys.argv value.
    """

    def decorator(func):
        @wraps(func)
        def inner():
            original_args = sys.argv
            try:
                sys.argv = original_args[:1]
                sys.argv.extend(args)
                func()
            finally:
                sys.argv = original_args

        return inner

    return decorator
