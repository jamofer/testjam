from importlib import resources
from typing import get_args

from testjam.schemas import execution as backend_execution
from testjam_client import statuses


def test_result_statuses_match_the_api():
    assert set(get_args(statuses.ResultStatus)) == set(get_args(backend_execution.ResultStatus))


def test_execution_statuses_match_the_api():
    assert set(get_args(statuses.ExecutionStatus)) == set(get_args(backend_execution.ExecutionStatus))


def test_package_ships_type_information():
    assert resources.files("testjam_client").joinpath("py.typed").is_file()
