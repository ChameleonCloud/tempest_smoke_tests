"""Implements portion of models from https://www.ctrf.io/docs/schema/overview."""

import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Iterable, List, Optional

from pydantic import BaseModel, ValidationError, field_validator
from testtools import TestByTestResult
from testtools.content import Content
from testtools.testcase import TestCase
from testtools.testresult.real import _details_to_str


class StatusEnum(str, Enum):
    passed = "passed"
    failed = "failed"
    skipped = "skipped"
    pending = "pending"
    other = "other"


class Test(BaseModel):
    name: str
    status: StatusEnum
    duration: int
    start: Optional[int] = None
    stop: Optional[int] = None
    suite: Optional[str] = None
    message: Optional[str] = None
    trace: Optional[str] = None
    line: Optional[int] = None
    rawStatus: Optional[str] = None
    tags: Optional[List[str]] = None
    type: Optional[str] = None
    filepath: Optional[str] = None
    retries: Optional[int] = None
    flaky: Optional[bool] = None
    extra: Optional[object] = None


class Summary(BaseModel):
    tests: int
    passed: int
    failed: int
    pending: int
    skipped: int
    other: int
    suites: Optional[int] = None
    start: Optional[int] = None
    stop: Optional[int] = None
    extra: Optional[object] = None


class Tool(BaseModel):
    name: str
    version: Optional[str] = None
    extra: Optional[object] = None


class Environment(BaseModel):
    reportName: Optional[str] = None
    buildName: Optional[str] = None
    buildNumber: Optional[str] = None
    buildUrl: Optional[str] = None


class Results(BaseModel):
    tool: Tool
    summary: Summary
    tests: List[Test]
    environment: Environment


class CTRFOutputResult(TestByTestResult):
    def __init__(self, stream, result_env: dict):
        super().__init__(self._on_test)
        self._write_row = lambda obj: stream.write(obj)

        ctrf_summary = Summary(
            tests=0,
            passed=0,
            failed=0,
            skipped=0,
            pending=0,
            other=0,
        )
        ctrf_environment = Environment(**result_env)
        ctrf_tool = Tool(name="tempest")
        ctrf_results = Results(
            tool=ctrf_tool, summary=ctrf_summary, tests=[], environment=ctrf_environment
        )

        self.ctrf_results = ctrf_results

    def addSuccess(self, test, details=None):
        super().addSuccess(test, details)
        self._status = "passed"
        self.ctrf_results.summary.passed += 1

    def addFailure(self, test, err=None, details=None):
        super().addFailure(test, err, details)
        self._status = "failed"
        self.ctrf_results.summary.failed += 1

    def addError(self, test, err=None, details=None):
        super().addError(test, err, details)
        self._status = "failed"
        self.ctrf_results.summary.failed += 1

    def addSkip(self, test, reason=None, details=None):
        super().addSkip(test, reason, details)
        self._status = "skipped"
        self.ctrf_results.summary.skipped += 1

    def content_as_text(self, item: Content | None) -> str | None:
        if isinstance(item, Content):
            return item.as_text()

    def _update_summary_times(self, start: int, stop: int):
        # ensure start and stop times are initialized
        if self.ctrf_results.summary.start is None:
            self.ctrf_results.summary.start = start
        if self.ctrf_results.summary.stop is None:
            self.ctrf_results.summary.stop = stop

        # set to earliest
        self.ctrf_results.summary.start = min(start, self.ctrf_results.summary.start)

        # set to latest
        self.ctrf_results.summary.stop = max(stop, self.ctrf_results.summary.stop)

    def _on_test(
        self,
        test: TestCase,
        status: str,
        start_time: datetime,
        stop_time: datetime,
        tags: List[str],
        details: dict[str, Content],
    ):
        """
        A callable that take a test case, a status (one of
            "success", "failure", "error", "skip", or "xfail"), a start time
            (a ``datetime`` with timezone), a stop time, an iterable of tags,
            and a details dict. Is called at the end of each test (i.e. on
            ``stopTest``) with the accumulated values for that test.
        """
        self.ctrf_results.summary.tests += 1

        if start_time and stop_time:
            # convert to integer millisecond count
            start_time_ms = int(start_time.timestamp() * 1000)
            stop_time_ms = int(stop_time.timestamp() * 1000)

            # update summary times
            self._update_summary_times(start=start_time_ms, stop=stop_time_ms)

            duration_ms = stop_time_ms - start_time_ms
        else:
            duration_ms = 0

        kwargs = {}
        reason_content = details.pop("reason", None)
        if reason_content:
            kwargs["message"] = reason_content.as_text().strip()

        traceback_content = details.pop("traceback", None)
        if traceback_content:
            kwargs["trace"] = traceback_content.as_text().strip()

        # extra_kwargs = {}
        # for key, value in details.items():
        #     extra_kwargs[key] = value.as_text().strip()

        ctrfTest = Test(
            name=test.id(),
            status=status,
            start=int(start_time.timestamp() * 1000),
            stop=int(stop_time.timestamp() * 1000),
            duration=int(duration_ms),
            tags=tags,
            **kwargs,
        )
        self.ctrf_results.tests.append(ctrfTest)

    def startTestRun(self):
        super().startTestRun()

    def stopTestRun(self):
        super().stopTestRun()
        result_dict = self.ctrf_results.model_dump(exclude_unset=True)
        output_dict = {"results": result_dict}
        self._write_row(json.dumps(output_dict, indent=2))
