"""Loader call fixtures"""

import re
import typing as t
from pathlib import Path

import pytest
from _pytest.fixtures import SubRequest

from cjunct import exceptions

# Get all sample files list
SAMPLES_DIR: Path = Path(__file__).parent / "samples"
SAMPLES: t.List[Path] = [item for item in SAMPLES_DIR.iterdir() if item.is_file()]

# Prepare regex patterns for exception pragma search
PRAGMA_MATCHER_TEMPLATES_MAP: t.Dict[str, str] = {
    ".xml": r"^\s*<!--\s+{}:\s*(.*?)\s*-->\s*$",
    ".yaml": r"^\s*#\s*{}:\s*(.*)$",
}


@pytest.fixture(params=SAMPLES, ids=[f"{item.suffix.replace('.', '')}-{item.stem}" for item in SAMPLES])
def sample_config(
    request: SubRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> t.Tuple[Path, t.Optional[t.Type[Exception]], t.Optional[str]]:
    """Return sample config file path with (maybe) exception handling instructions"""
    file_path: Path = request.param
    # Find exception instructions
    expected_exception_type: t.Optional[t.Type[Exception]] = None
    expected_exception_match: t.Optional[str] = None
    template: str = PRAGMA_MATCHER_TEMPLATES_MAP[file_path.suffix]
    xml_pragma_exception_type_pattern: t.Pattern = re.compile(template.format("exception"))
    xml_pragma_exception_match_pattern: t.Pattern = re.compile(template.format("match"))
    with file_path.open(encoding="utf-8") as f:
        for line in f:
            for match in xml_pragma_exception_type_pattern.finditer(line):
                expected_exception_type = getattr(exceptions, match.group(1))
                break
            for match in xml_pragma_exception_match_pattern.finditer(line):
                expected_exception_match = match.group(1)
                break
    monkeypatch.chdir(file_path.parent)
    return file_path, expected_exception_type, expected_exception_match
