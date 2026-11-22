"""Tests for templates module."""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.templates import (
    get_template_env,
    list_templates,
    render_template,
    render_template_file,
    get_template_parameters,
    TEMPLATE_DIRS,
)
from lib.exceptions import TemplateNotFoundError, TemplateRenderError


class TestTemplateEnvironment:
    """Tests for template environment."""

    def test_get_template_env_returns_environment(self):
        """Test that get_template_env returns a Jinja2 Environment."""
        from jinja2 import Environment
        env = get_template_env()
        assert isinstance(env, Environment)

    def test_get_template_env_with_custom_dir(self, tmp_path):
        """Test template env with custom directory."""
        env = get_template_env(tmp_path)
        assert env is not None


class TestListTemplates:
    """Tests for listing templates."""

    def test_list_templates_returns_list(self):
        """Test that list_templates returns a list."""
        templates = list_templates()
        assert isinstance(templates, list)

    def test_list_templates_filtered_by_platform(self):
        """Test listing templates for a specific platform."""
        # Check if freecad templates exist
        templates = list_templates("freecad")
        assert isinstance(templates, list)
        # If templates exist, they should be from freecad subdir
        for t in templates:
            assert "freecad" in t or t.endswith(".py")

    def test_list_templates_sorted(self):
        """Test that templates are sorted."""
        templates = list_templates()
        assert templates == sorted(templates)

    def test_list_templates_unique(self):
        """Test that templates are unique."""
        templates = list_templates()
        assert len(templates) == len(set(templates))


class TestRenderTemplate:
    """Tests for template rendering."""

    def test_render_template_not_found(self):
        """Test rendering non-existent template."""
        with pytest.raises(TemplateNotFoundError):
            render_template("nonexistent_template.py", {})

    def test_render_template_file_not_found(self, tmp_path):
        """Test rendering non-existent template file."""
        nonexistent = tmp_path / "nonexistent.py"
        with pytest.raises(TemplateNotFoundError):
            render_template_file(nonexistent, {})

    def test_render_template_file_with_syntax_error(self, tmp_path):
        """Test rendering template with Jinja2 syntax error."""
        bad_template = tmp_path / "bad.py"
        bad_template.write_text("{% invalid syntax %}")

        with pytest.raises(TemplateRenderError):
            render_template_file(bad_template, {})

    def test_render_template_file_success(self, tmp_path):
        """Test successful template rendering."""
        template = tmp_path / "test.py"
        template.write_text("length = {{ length }}")

        result = render_template_file(template, {"length": 100})
        assert "length = 100" in result


class TestTemplateParameters:
    """Tests for template parameter extraction."""

    def test_get_template_parameters_nonexistent(self):
        """Test getting parameters from non-existent template."""
        params = get_template_parameters("nonexistent.py")
        assert params == {}

    def test_get_template_parameters_extracts_at_param(self, tmp_path):
        """Test extracting @param comments."""
        # Create a test template
        template_content = """# @param length=100 Length of the box
# @param width=50 Width of the box
length = {{ length }}
width = {{ width }}
"""
        template_file = tmp_path / "test_params.py"
        template_file.write_text(template_content)

        # Temporarily add to TEMPLATE_DIRS
        from lib import templates
        original_dirs = templates.TEMPLATE_DIRS.copy()
        templates.TEMPLATE_DIRS = [tmp_path]

        try:
            params = get_template_parameters("test_params.py")
            assert "length" in params
            assert params["length"] == 100
            assert "width" in params
            assert params["width"] == 50
        finally:
            templates.TEMPLATE_DIRS = original_dirs

    def test_get_template_parameters_extracts_default_filter(self, tmp_path):
        """Test extracting default filters."""
        template_content = """length = {{ length|default(100) }}
width = {{ width|default(50.5) }}
name = {{ name|default('box') }}
"""
        template_file = tmp_path / "test_defaults.py"
        template_file.write_text(template_content)

        from lib import templates
        original_dirs = templates.TEMPLATE_DIRS.copy()
        templates.TEMPLATE_DIRS = [tmp_path]

        try:
            params = get_template_parameters("test_defaults.py")
            assert params.get("length") == 100
            assert params.get("width") == 50.5
            assert params.get("name") == "box"
        finally:
            templates.TEMPLATE_DIRS = original_dirs


class TestTemplateDirs:
    """Tests for template directory configuration."""

    def test_template_dirs_exist(self):
        """Test that TEMPLATE_DIRS is configured."""
        assert isinstance(TEMPLATE_DIRS, list)
        assert len(TEMPLATE_DIRS) > 0

    def test_template_dirs_are_paths(self):
        """Test that TEMPLATE_DIRS contains Path objects."""
        for d in TEMPLATE_DIRS:
            assert isinstance(d, Path)
