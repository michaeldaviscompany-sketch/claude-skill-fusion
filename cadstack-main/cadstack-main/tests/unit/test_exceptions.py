"""Tests for CADStack exception hierarchy."""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.exceptions import (
    CADStackError,
    BackendNotAvailableError,
    InvalidDimensionError,
    ScriptValidationError,
    ExportFailedError,
    EmptyDocumentError,
    FeatureOpError,
    raise_for_dimension,
)


class TestCADStackError:
    """Tests for base CADStackError."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = CADStackError("Something went wrong")
        assert str(error) == "Something went wrong"
        assert error.message == "Something went wrong"
        assert error.hint is None

    def test_error_with_hint(self):
        """Test error with hint."""
        error = CADStackError("Something went wrong", hint="Try doing X instead")
        assert "Hint: Try doing X instead" in str(error)

    def test_error_to_dict(self):
        """Test serialization to dict."""
        error = CADStackError("Test error", hint="Test hint", details={"key": "value"})
        d = error.to_dict()
        assert d["type"] == "CADStackError"
        assert d["message"] == "Test error"
        assert d["hint"] == "Test hint"
        assert d["details"]["key"] == "value"


class TestBackendNotAvailableError:
    """Tests for BackendNotAvailableError."""

    def test_cadquery_hint(self):
        """Test that CadQuery error has install hint."""
        error = BackendNotAvailableError("cadquery")
        assert "pip install cadquery" in error.hint

    def test_freecad_hint(self):
        """Test that FreeCAD error mentions FreeCAD installation."""
        error = BackendNotAvailableError("freecad")
        assert "FreeCAD" in error.hint
        assert "Python path" in error.hint

    def test_custom_reason(self):
        """Test error with custom reason."""
        error = BackendNotAvailableError("autocad", "Windows only")
        assert "Windows only" in error.message


class TestInvalidDimensionError:
    """Tests for InvalidDimensionError."""

    def test_negative_dimension(self):
        """Test error for negative value."""
        error = InvalidDimensionError("length", -10, "value is negative")
        assert "length" in error.message
        assert "-10" in error.message
        assert "negative" in error.message

    def test_zero_dimension(self):
        """Test error for zero value."""
        error = InvalidDimensionError("radius", 0, "value is zero")
        assert "radius" in error.message
        assert "0" in error.message


class TestScriptValidationError:
    """Tests for ScriptValidationError."""

    def test_validation_with_warnings(self):
        """Test error with multiple warnings."""
        warnings = [
            "Dangerous pattern: os.system",
            "Dangerous pattern: subprocess",
        ]
        error = ScriptValidationError(warnings)
        assert error.warnings == warnings
        assert "dangerous patterns" in error.message.lower()


class TestExportFailedError:
    """Tests for ExportFailedError."""

    def test_permission_error(self):
        """Test error for permission denied."""
        error = ExportFailedError("step", "/root/file.step", "permission")
        assert "STEP" in error.message
        assert "/root/file.step" in error.message
        assert "permission" in error.hint.lower()

    def test_empty_document_error(self):
        """Test error for empty document."""
        error = ExportFailedError("stl", "output.stl", "empty")
        assert "empty" in error.hint.lower()


class TestRaiseForDimension:
    """Tests for raise_for_dimension utility."""

    def test_valid_dimension(self):
        """Test that valid dimensions don't raise."""
        # Should not raise
        raise_for_dimension("length", 10.0)

    def test_nan_raises(self):
        """Test that NaN raises."""
        import math
        with pytest.raises(InvalidDimensionError) as exc_info:
            raise_for_dimension("length", float('nan'))
        assert "NaN" in str(exc_info.value)

    def test_inf_raises(self):
        """Test that infinity raises."""
        with pytest.raises(InvalidDimensionError) as exc_info:
            raise_for_dimension("length", float('inf'))
        assert "infinite" in str(exc_info.value)

    def test_negative_raises(self):
        """Test that negative values raise."""
        with pytest.raises(InvalidDimensionError) as exc_info:
            raise_for_dimension("length", -10.0)
        assert "negative" in str(exc_info.value)

    def test_zero_raises_when_not_allowed(self):
        """Test that zero raises when not allowed."""
        with pytest.raises(InvalidDimensionError) as exc_info:
            raise_for_dimension("radius", 0.0, allow_zero=False)
        assert "zero" in str(exc_info.value)

    def test_zero_allowed(self):
        """Test that zero is allowed when specified."""
        # Should not raise
        raise_for_dimension("offset", 0.0, allow_zero=True)

    def test_exceeds_max(self):
        """Test that exceeding max raises."""
        with pytest.raises(InvalidDimensionError) as exc_info:
            raise_for_dimension("length", 200000.0, max_value=100000.0)
        assert "maximum" in str(exc_info.value)
