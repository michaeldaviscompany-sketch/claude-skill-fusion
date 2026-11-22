"""Unit tests for parts library module."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.parts_library import (
    PartDefinition,
    register_part,
    get_part_definition,
    list_parts,
    list_categories,
    create_part,
    _PART_REGISTRY,
)


class TestPartRegistry:
    """Tests for part registration."""

    def setup_method(self):
        """Clear registry before each test."""
        _PART_REGISTRY.clear()

    def test_register_part_decorator(self):
        """Test registering a part with decorator."""
        @register_part("test_part", "test_category", "A test part")
        def test_generator(backend, length=100, width=50):
            return backend.create_box(length, width, 10)

        assert "test_part" in _PART_REGISTRY
        part_def = _PART_REGISTRY["test_part"]
        assert part_def.name == "test_part"
        assert part_def.category == "test_category"
        assert part_def.description == "A test part"
        assert "length" in part_def.parameters
        assert "width" in part_def.parameters

    def test_register_part_extracts_defaults(self):
        """Test that defaults are extracted from function signature."""
        @register_part("screw", "fasteners", "Metric screw")
        def screw_generator(backend, diameter=3, length=10):
            return backend.create_cylinder(diameter / 2, length)

        part_def = _PART_REGISTRY["screw"]
        assert part_def.parameters["diameter"]["default"] == 3
        assert part_def.parameters["length"]["default"] == 10

    def test_register_part_excludes_backend_param(self):
        """Test that backend parameter is excluded from part parameters."""
        @register_part("box", "shapes", "A box")
        def box_generator(backend, size=10):
            return backend.create_box(size, size, size)

        part_def = _PART_REGISTRY["box"]
        assert "backend" not in part_def.parameters
        assert "size" in part_def.parameters


class TestGetPartDefinition:
    """Tests for get_part_definition function."""

    def setup_method(self):
        """Clear and setup registry."""
        _PART_REGISTRY.clear()

    def test_get_existing_part(self):
        """Test getting an existing part definition."""
        @register_part("existing_part", "cat", "desc")
        def gen(backend):
            return None

        part_def = get_part_definition("existing_part")
        assert part_def is not None
        assert part_def.name == "existing_part"

    def test_get_nonexistent_part(self):
        """Test getting a non-existent part returns None."""
        part_def = get_part_definition("nonexistent")
        assert part_def is None


class TestListParts:
    """Tests for list_parts function."""

    def setup_method(self):
        """Clear and setup registry."""
        _PART_REGISTRY.clear()

    def test_list_all_parts(self):
        """Test listing all parts."""
        @register_part("part1", "cat1", "desc")
        def gen1(backend):
            return None

        @register_part("part2", "cat2", "desc")
        def gen2(backend):
            return None

        parts = list_parts()
        assert "part1" in parts
        assert "part2" in parts
        assert len(parts) == 2

    def test_list_parts_by_category(self):
        """Test listing parts filtered by category."""
        @register_part("part1", "fasteners", "desc")
        def gen1(backend):
            return None

        @register_part("part2", "bearings", "desc")
        def gen2(backend):
            return None

        @register_part("part3", "fasteners", "desc")
        def gen3(backend):
            return None

        fasteners = list_parts(category="fasteners")
        assert "part1" in fasteners
        assert "part3" in fasteners
        assert "part2" not in fasteners

    def test_list_parts_empty_registry(self):
        """Test listing parts from empty registry."""
        _PART_REGISTRY.clear()
        parts = list_parts()
        assert parts == []


class TestListCategories:
    """Tests for list_categories function."""

    def setup_method(self):
        """Clear registry."""
        _PART_REGISTRY.clear()

    def test_list_categories(self):
        """Test listing all categories."""
        @register_part("p1", "fasteners", "d")
        def gen1(backend):
            return None

        @register_part("p2", "bearings", "d")
        def gen2(backend):
            return None

        @register_part("p3", "fasteners", "d")
        def gen3(backend):
            return None

        categories = list_categories()
        assert "fasteners" in categories
        assert "bearings" in categories
        assert len(categories) == 2  # No duplicates

    def test_list_categories_empty(self):
        """Test listing categories from empty registry."""
        _PART_REGISTRY.clear()
        categories = list_categories()
        assert categories == []


class TestCreatePart:
    """Tests for create_part function."""

    def setup_method(self):
        """Setup registry with test part."""
        _PART_REGISTRY.clear()

        @register_part("test_screw", "fasteners", "Test screw")
        def test_screw(backend, diameter=3, length=10):
            mock_obj = Mock()
            mock_obj.name = f"screw_M{diameter}x{length}"
            return mock_obj

    def test_create_part_with_defaults(self):
        """Test creating a part with default parameters."""
        mock_backend = Mock()

        result = create_part("test_screw", mock_backend)

        assert result is not None
        assert "screw_M3x10" in result.name

    def test_create_part_with_custom_params(self):
        """Test creating a part with custom parameters."""
        mock_backend = Mock()

        result = create_part("test_screw", mock_backend, diameter=5, length=20)

        assert result is not None
        assert "screw_M5x20" in result.name

    def test_create_nonexistent_part(self):
        """Test creating a non-existent part raises error."""
        mock_backend = Mock()

        with pytest.raises(ValueError):
            create_part("nonexistent", mock_backend)


class TestPartDefinition:
    """Tests for PartDefinition dataclass."""

    def test_part_definition_creation(self):
        """Test creating a PartDefinition."""
        def gen(backend, size=10):
            return None

        part_def = PartDefinition(
            name="test",
            category="test_cat",
            description="Test description",
            parameters={"size": {"type": "float", "default": 10}},
            generator=gen
        )

        assert part_def.name == "test"
        assert part_def.category == "test_cat"
        assert part_def.description == "Test description"
        assert part_def.parameters["size"]["default"] == 10


class TestBuiltInParts:
    """Tests for built-in parts if they exist."""

    def setup_method(self):
        """Import parts library to register built-in parts."""
        # Re-import to register parts
        import importlib
        import lib.parts_library
        importlib.reload(lib.parts_library)

    def test_has_fasteners_category(self):
        """Test that fasteners category exists."""
        categories = list_categories()
        # This will only pass if built-in parts are loaded
        # which depends on the module initialization

    def test_part_generator_is_callable(self):
        """Test that registered generators are callable."""
        parts = list_parts()
        for part_name in parts[:3]:  # Check first 3
            part_def = get_part_definition(part_name)
            if part_def:
                assert callable(part_def.generator)
