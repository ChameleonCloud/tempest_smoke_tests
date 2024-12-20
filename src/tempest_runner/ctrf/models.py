"""Implements portion of models from https://www.ctrf.io/docs/schema/overview."""

import json
from datetime import datetime, timedelta
from typing import Iterable, List, Optional

from pydantic import BaseModel
from testtools import TestByTestResult
from testtools.content import Content
from testtools.testcase import TestCase


class Test(BaseModel):
    name: str
    status: str
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
    tests: int = 0
    passed: int = 0
    failed: int = 0
    pending: int = 0
    skipped: int = 0
    other: int = 0
    suites: Optional[int] = None
    start: int = 0
    stop: int = 0
    extra: Optional[object] = None


class Tool(BaseModel):
    name: str
    version: Optional[str] = None
    extra: Optional[object] = None


class Results(BaseModel):
    tool: Tool
    summary: Summary
    tests: List[Test]


class CTRFOutputResult(TestByTestResult):
    def __init__(self, stream):
        super().__init__(self._on_test)
        self._write_row = lambda obj: stream.write(obj)

        ctrf_summary = Summary()
        ctrf_tool = Tool(name="tempest")
        ctrf_results = Results(
            tool=ctrf_tool,
            summary=ctrf_summary,
            tests=[],
        )

        self.ctrf_results = ctrf_results

    def addSuccess(self, test, details=None):
        super().addSuccess(test, details)
        self.ctrf_results.summary.passed += 1

    def addFailure(self, test, err=None, details=None):
        super().addFailure(test, err, details)
        self.ctrf_results.summary.failed += 1

    def addError(self, test, err=None, details=None):
        super().addError(test, err, details)
        self.ctrf_results.summary.failed += 1

    def addSkip(self, test, reason=None, details=None):
        super().addSkip(test, reason, details)
        self.ctrf_results.summary.skipped += 1

    def content_as_text(self, item: Content | None) -> str | None:
        if isinstance(item, Content):
            return item.as_text()

    def _on_test(
        self,
        test: TestCase,
        status: str,
        start_time: datetime,
        stop_time: datetime,
        tags: List[str],
        details: dict,
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
            duration_timedelta = stop_time - start_time
            # convert to units of milliseconds
            duration_ms = duration_timedelta / timedelta(milliseconds=1)
        else:
            duration_ms = 0

        reason: Content | None = details.get("reason")
        reason_msg = None
        if reason:
            reason_msg = reason.as_text()

        reason_msg = self.content_as_text(details.get("reason"))

        ctrfTest = Test(
            name=test.id(),
            status=status,
            start=int(start_time.timestamp()),
            stop=int(stop_time.timestamp()),
            duration=int(duration_ms),
            tags=tags,
            message=reason_msg,
            # trace=details.get("traceback"),
        )
        self.ctrf_results.tests.append(ctrfTest)

    def startTestRun(self):
        super().startTestRun()

    def stopTestRun(self):
        super().stopTestRun()
        result_dict = self.ctrf_results.model_dump()
        output_dict = {"results": result_dict}
        self._write_row(json.dumps(output_dict, indent=2))
