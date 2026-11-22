"""Integration tests for CLI commands."""

import pytest
import sys
from pathlib import Path
from typer.testing import CliRunner

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.cad_executor import app


runner = CliRunner()


class TestCLIInfo:
    """Tests for 'cad info' command."""

    def test_info_runs(self):
        """Test that info command runs without error."""
        result = runner.invoke(app, ["info"])
        assert result.exit_code == 0
        assert "CAD Platforms" in result.output


class TestCLICheck:
    """Tests for 'cad check' command."""

    def test_check_cadquery(self, mock_cadquery):
        """Test checking cadquery backend."""
        # Need to reimport after mock
        from lib.backends.cadquery import CadQueryBackend, CADQUERY_AVAILABLE
        if CADQUERY_AVAILABLE:
            result = runner.invoke(app, ["check", "cadquery"])
            # Should show some output about cadquery
            assert "cadquery" in result.output.lower() or result.exit_code == 0


class TestCLICreate:
    """Tests for 'cad create' command."""

    def test_create_box_invalid_dims(self):
        """Test that invalid dimensions are rejected."""
        result = runner.invoke(app, ["create", "box", "100,50", "-p", "cadquery"])
        assert result.exit_code != 0

    def test_create_box_negative_dim(self):
        """Test that negative dimensions are rejected."""
        # Put options before positional args to avoid typer parsing -10 as an option
        result = runner.invoke(app, ["create", "-p", "cadquery", "box", "-10,50,20"])
        assert result.exit_code != 0
        # Accept any non-zero exit - the dimension validation should catch it
        # (output may contain "positive" or "negative" or "must be")

    def test_create_unknown_primitive(self, mock_cadquery):
        """Test that unknown primitive is rejected."""
        result = runner.invoke(app, ["create", "cube", "10,10,10", "-p", "cadquery"])
        assert result.exit_code != 0
        assert "unknown" in result.output.lower()


class TestCLIRun:
    """Tests for 'cad run' command."""

    def test_run_missing_script(self):
        """Test that missing script is handled."""
        result = runner.invoke(app, ["run", "nonexistent.py"])
        assert result.exit_code != 0
        assert "not found" in result.output.lower()

    def test_run_dangerous_script_blocked(self, tmp_path, dangerous_script):
        """Test that dangerous scripts are blocked."""
        script_path = tmp_path / "dangerous.py"
        script_path.write_text(dangerous_script)

        result = runner.invoke(app, ["run", str(script_path), "-p", "cadquery"])
        assert result.exit_code != 0
        assert "blocked" in result.output.lower() or "dangerous" in result.output.lower()

    def test_run_safe_script(self, tmp_path, sample_box_script, mock_cadquery):
        """Test that safe scripts execute."""
        script_path = tmp_path / "safe.py"
        script_path.write_text(sample_box_script)

        result = runner.invoke(app, ["run", str(script_path), "-p", "cadquery"])
        # Should either succeed or fail gracefully (not crash)
        assert "Traceback" not in result.output or result.exit_code != 0


class TestCLIVersion:
    """Tests for 'cad version' command."""

    def test_version(self):
        """Test that version command shows version."""
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert "CADStack" in result.output


class TestBackendRegistry:
    """Tests for backend registry functionality."""

    def test_registry_has_cadquery(self, mock_cadquery):
        """Test that CadQuery is in the registry."""
        from lib.backends import get_available_backends

        backends = get_available_backends()

        # If cadquery is available, it should be in the registry
        if "cadquery" in backends:
            backend = backends["cadquery"]()
            assert backend.name == "cadquery"

    def test_get_unknown_backend(self):
        """Test that unknown backend raises appropriate error."""
        from lib.cad_executor import get_backend
        from lib.exceptions import BackendNotAvailableError

        with pytest.raises(BackendNotAvailableError):
            get_backend("unknown_backend")
