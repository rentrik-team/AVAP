import uuid
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.core.enums import ExecutionStatus, ScannerType
from app.core.exceptions import ParserException
from app.parsers.models import AssessmentPackage
from app.parsers.parser_manager import ParserManager
from app.scanners.scan_artifact import ScanArtifact


def test_parser_manager_unsuccessful_artifact():
    manager = ParserManager()

    # Execution failed
    artifact = ScanArtifact(
        scan_id=uuid.uuid4(),
        scanner_type=ScannerType.NMAP,
        execution_status=ExecutionStatus.FAILED,
        output_path=Path("nonexistent.xml"),
    )
    with pytest.raises(ParserException) as exc:
        manager.parse_artifact(artifact)
    assert "Cannot parse unsuccessful scan artifact" in str(exc.value)


def test_parser_manager_missing_output_path():
    manager = ParserManager()

    # Output path is None
    artifact = ScanArtifact(
        scan_id=uuid.uuid4(),
        scanner_type=ScannerType.NMAP,
        execution_status=ExecutionStatus.SUCCESS,
        output_path=None,
    )
    with pytest.raises(ParserException) as exc:
        manager.parse_artifact(artifact)
    assert "does not specify an output path" in str(exc.value)


def test_parser_manager_missing_file():
    manager = ParserManager()

    # File does not exist on disk
    artifact = ScanArtifact(
        scan_id=uuid.uuid4(),
        scanner_type=ScannerType.NMAP,
        execution_status=ExecutionStatus.SUCCESS,
        output_path=Path("this_file_does_not_exist_anywhere.xml"),
    )
    with pytest.raises(ParserException) as exc:
        manager.parse_artifact(artifact)
    assert "output file does not exist" in str(exc.value)


def test_parser_manager_coordination():
    # Mock Factory and Parser; use a real AssessmentPackage since it is a
    # Pydantic model whose fields are not visible to MagicMock(spec=...)
    # introspection (dir() does not list pydantic v2 model fields).
    mock_factory = MagicMock()
    mock_parser = MagicMock()
    mock_package = AssessmentPackage(
        scan_id=uuid.uuid4(), scanner_type=ScannerType.NMAP
    )

    mock_factory.get_parser.return_value = mock_parser
    mock_parser.parse.return_value = mock_package

    # Make a dummy output path and mock exists()
    mock_path = MagicMock(spec=Path)
    mock_path.exists.return_value = True

    artifact = ScanArtifact(
        scan_id=uuid.uuid4(),
        scanner_type=ScannerType.NMAP,
        execution_status=ExecutionStatus.SUCCESS,
        output_path=mock_path,
    )

    manager = ParserManager(factory=mock_factory)
    result = manager.parse_artifact(artifact)

    assert result is mock_package
    mock_factory.get_parser.assert_called_once_with(ScannerType.NMAP)
    mock_parser.parse.assert_called_once_with(artifact)
