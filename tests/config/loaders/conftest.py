"""Loader call fixtures"""

import re
import typing as t
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from cjunct import exceptions

# Get all sample files list
XML_SAMPLES_DIR: Path = Path(__file__).parent / "samples" / "xml"
XML_SAMPLES: t.List[Path] = [item for item in XML_SAMPLES_DIR.iterdir() if item.is_file()]

# Prepare regex patterns for exception pragma search
PRAGMA_MATCHER_TEMPLATE: str = r"^\s*<!--\s+{}:\s*(.*?)\s*-->\s*$"
PRAGMA_EXCEPTION_TYPE_PATTERN: t.Pattern = re.compile(PRAGMA_MATCHER_TEMPLATE.format("exception"))
PRAGMA_EXCEPTION_MATCH_PATTERN: t.Pattern = re.compile(PRAGMA_MATCHER_TEMPLATE.format("match"))


@pytest.fixture(params=XML_SAMPLES, ids=[item.stem for item in XML_SAMPLES])
def xml_config(
    request: SubRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> t.Tuple[Path, t.Optional[t.Type[Exception]], t.Optional[str]]:
    """Return sample config file path with (maybe) exception handling instructions"""
    file_path: Path = request.param
    # Find exception instructions
    expected_exception_type: t.Optional[t.Type[Exception]] = None
    expected_exception_match: t.Optional[str] = None
    with file_path.open(encoding="utf-8") as f:
        for line in f:
            for match in PRAGMA_EXCEPTION_TYPE_PATTERN.finditer(line):
                expected_exception_type = getattr(exceptions, match.group(1))
                break
            for match in PRAGMA_EXCEPTION_MATCH_PATTERN.finditer(line):
                expected_exception_match = match.group(1)
                break

    monkeypatch.chdir(file_path.parent)
    return file_path, expected_exception_type, expected_exception_match
