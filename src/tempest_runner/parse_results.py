import argparse
import logging
import os
import sys
from pathlib import Path

from stestr.repository.abstract import AbstractRepository, AbstractTestRun
from stestr.repository.util import get_repo_open
from subunit.filters import filter_by_result
from testtools import StreamToExtendedDecorator

from tempest_runner.ctrf import models

logging.basicConfig(level=logging.INFO)

LOG = logging.getLogger(__name__)


def handle_subunit_stream(output):
    return StreamToExtendedDecorator(models.CTRFOutputResult(output))


def process_test_run(test_run: AbstractTestRun):
    subunit_stream = test_run.get_subunit_stream()

    output_file = Path("/tmp/ctrf-report.json")
    result = filter_by_result(
        result_factory=handle_subunit_stream,
        output_path=output_file,
        input_stream=subunit_stream,
        protocol_version=2,
        passthrough=False,
        forward=False,
        passthrough_subunit=False,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("stestr_path", type=str)

    args = parser.parse_args()

    # switch to dir where .stestr repo lives
    workspace_local_dir = Path(args.stestr_path)

    repo: AbstractRepository
    repo = get_repo_open(repo_url=workspace_local_dir)
    for run_id in repo.get_run_ids():
        test_run: AbstractTestRun
        test_run = repo.get_test_run(run_id)
        test_result = process_test_run(test_run)


if __name__ == "__main__":
    main()
