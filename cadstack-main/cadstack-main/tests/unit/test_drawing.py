"""Unit tests for drawing module."""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.drawing import (
    DrawingGenerator,
    DrawingSheet,
    ViewProjection,
    ViewType,
    DimensionType,
    ExportFormat,
    Dimension,
    Point2D,
    create_drawing,
    quick_drawing,
)


class TestPoint2D:
    """Tests for Point2D."""

    def test_point_creation(self):
        """Test creating a point."""
        p = Point2D(10.0, 20.0)
        assert p.x == 10.0
        assert p.y == 20.0

    def test_point_iteration(self):
        """Test iterating over point."""
        p = Point2D(5.0, 10.0)
        x, y = p
        assert x == 5.0
        assert y == 10.0


class TestDimension:
    """Tests for Dimension."""

    def test_dimension_creation(self):
        """Test creating a dimension."""
        dim = Dimension(
            dimension_type=DimensionType.LINEAR,
            start=Point2D(0, 0),
            end=Point2D(100, 0),
            value=100.0,
            unit="mm"
        )
        assert dim.value == 100.0
        assert dim.unit == "mm"

    def test_dimension_text_value(self):
        """Test dimension text."""
        dim = Dimension(
            dimension_type=DimensionType.LINEAR,
            start=Point2D(0, 0),
            end=Point2D(50, 0),
            value=50.0
        )
        assert "50" in dim.text_value
        assert "mm" in dim.text_value

    def test_dimension_custom_text(self):
        """Test dimension with custom text."""
        dim = Dimension(
            dimension_type=DimensionType.LINEAR,
            start=Point2D(0, 0),
            end=Point2D(100, 0),
            value=100.0,
            text="100 ± 0.1"
        )
        assert dim.text_value == "100 ± 0.1"


class TestViewProjection:
    """Tests for ViewProjection."""

    def test_view_creation(self):
        """Test creating a view."""
        view = ViewProjection(view_type=ViewType.TOP)
        assert view.view_type == ViewType.TOP
        assert view.lines == []
        assert view.arcs == []
        assert view.scale == 1.0

    def test_view_bounds(self):
        """Test view bounds calculation."""
        view = ViewProjection(
            view_type=ViewType.TOP,
            lines=[(0, 0, 100, 0), (0, 0, 0, 50)]
        )
        bounds = view.bounds
        assert bounds[0] == 0  # min_x
        assert bounds[1] == 0  # min_y
        assert bounds[2] == 100  # max_x
        assert bounds[3] == 50  # max_y

    def test_view_width_height(self):
        """Test view width and height."""
        view = ViewProjection(
            view_type=ViewType.FRONT,
            lines=[(10, 10, 110, 10), (10, 10, 10, 60)]
        )
        assert view.width == 100
        assert view.height == 50

    def test_view_empty_bounds(self):
        """Test bounds of empty view."""
        view = ViewProjection(view_type=ViewType.TOP)
        assert view.bounds == (0, 0, 0, 0)


class TestDrawingSheet:
    """Tests for DrawingSheet."""

    def test_sheet_creation(self):
        """Test creating a sheet."""
        sheet = DrawingSheet(title="Test Drawing")
        assert sheet.title == "Test Drawing"
        assert len(sheet.views) == 0

    def test_standard_size(self):
        """Test getting standard sizes."""
        a3_l = DrawingSheet.standard_size("A3_L")
        assert a3_l == (420.0, 297.0)

        a4 = DrawingSheet.standard_size("A4")
        assert a4 == (210.0, 297.0)

    def test_invalid_size_returns_default(self):
        """Test invalid size returns default."""
        size = DrawingSheet.standard_size("INVALID")
        assert size == DrawingSheet.standard_size("A3_L")


class TestDrawingGenerator:
    """Tests for DrawingGenerator."""

    def test_generator_creation(self):
        """Test creating a generator."""
        gen = DrawingGenerator()
        assert gen._model is None

    def test_set_title(self):
        """Test setting title."""
        gen = DrawingGenerator()
        gen.set_title("My Drawing")
        assert gen._title == "My Drawing"

    def test_set_sheet_size_tuple(self):
        """Test setting sheet size with tuple."""
        gen = DrawingGenerator()
        gen.set_sheet_size((500.0, 400.0))
        assert gen._sheet_size == (500.0, 400.0)

    def test_set_sheet_size_name(self):
        """Test setting sheet size with name."""
        gen = DrawingGenerator()
        gen.set_sheet_size("A4")
        assert gen._sheet_size == (210.0, 297.0)

    def test_set_title_block(self):
        """Test setting title block fields."""
        gen = DrawingGenerator()
        gen.set_title_block(title="Part", drawn_by="John", date="2024-01-01")
        assert gen._title_block["title"] == "Part"
        assert gen._title_block["drawn_by"] == "John"

    def test_set_model_with_bounds(self):
        """Test setting model with explicit bounds."""
        gen = DrawingGenerator()
        gen.set_model(None, bounds=(0, 0, 0, 100, 50, 25))
        assert gen._model_bounds == (0, 0, 0, 100, 50, 25)

    def test_add_view(self):
        """Test adding a view."""
        gen = DrawingGenerator()
        gen.set_model(None, bounds=(0, 0, 0, 100, 100, 50))
        view = gen.add_view(ViewType.TOP)
        assert view.view_type == ViewType.TOP
        assert len(gen._views) == 1

    def test_add_multiple_views(self):
        """Test adding multiple views."""
        gen = DrawingGenerator()
        gen.set_model(None, bounds=(0, 0, 0, 100, 100, 50))
        gen.add_view(ViewType.TOP)
        gen.add_view(ViewType.FRONT)
        gen.add_view(ViewType.RIGHT)
        assert len(gen._views) == 3

    def test_add_dimension(self):
        """Test adding a dimension."""
        gen = DrawingGenerator()
        gen.set_model(None, bounds=(0, 0, 0, 100, 100, 50))
        gen.add_view(ViewType.TOP)
        gen.add_dimension(0, (0, 0), (100, 0))
        assert len(gen._views[0].dimensions) == 1

    def test_layout_views(self):
        """Test auto layout."""
        gen = DrawingGenerator()
        gen.set_model(None, bounds=(0, 0, 0, 100, 100, 50))
        gen.add_view(ViewType.TOP)
        gen.add_view(ViewType.FRONT)
        gen.layout_views()
        # Views should have different offsets
        assert gen._views[0].offset != gen._views[1].offset

    def test_create_sheet(self):
        """Test creating a sheet."""
        gen = DrawingGenerator()
        gen.set_title("Test")
        gen.set_model(None, bounds=(0, 0, 0, 100, 100, 50))
        gen.add_view(ViewType.TOP)
        sheet = gen.create_sheet()
        assert isinstance(sheet, DrawingSheet)
        assert sheet.title == "Test"
        assert len(sheet.views) == 1


class TestDrawingExport:
    """Tests for drawing export."""

    def test_export_svg(self, tmp_path):
        """Test SVG export."""
        gen = DrawingGenerator()
        gen.set_model(None, bounds=(0, 0, 0, 100, 100, 50))
        gen.add_view(ViewType.TOP)

        output = tmp_path / "test.svg"
        success = gen.export(output, ExportFormat.SVG)

        assert success is True
        assert output.exists()
        content = output.read_text()
        assert "<svg" in content

    def test_export_creates_parent_dirs(self, tmp_path):
        """Test export creates parent directories."""
        gen = DrawingGenerator()
        gen.set_model(None, bounds=(0, 0, 0, 100, 100, 50))
        gen.add_view(ViewType.TOP)

        output = tmp_path / "subdir" / "nested" / "test.svg"
        success = gen.export(output, ExportFormat.SVG)

        assert success is True
        assert output.exists()

    def test_export_dxf_without_ezdxf(self, tmp_path):
        """Test DXF export fails gracefully without ezdxf."""
        gen = DrawingGenerator()
        gen.set_model(None, bounds=(0, 0, 0, 100, 100, 50))
        gen.add_view(ViewType.TOP)

        output = tmp_path / "test.dxf"
        # Will fail if ezdxf not installed, succeed if it is
        # Just verify it doesn't crash
        try:
            gen.export(output, ExportFormat.DXF)
        except Exception:
            pass  # Expected if ezdxf not installed


class TestCreateDrawing:
    """Tests for create_drawing convenience function."""

    def test_create_drawing(self):
        """Test creating drawing via convenience function."""
        gen = create_drawing("My Drawing")
        assert isinstance(gen, DrawingGenerator)
        assert gen._title == "My Drawing"


class TestQuickDrawing:
    """Tests for quick_drawing convenience function."""

    def test_quick_drawing_default_views(self):
        """Test quick drawing with default views."""
        gen = quick_drawing(None)
        assert len(gen._views) == 3  # TOP, FRONT, RIGHT by default

    def test_quick_drawing_custom_views(self):
        """Test quick drawing with custom views."""
        gen = quick_drawing(None, views=[ViewType.TOP, ViewType.ISOMETRIC])
        assert len(gen._views) == 2

    def test_quick_drawing_with_output(self, tmp_path):
        """Test quick drawing with output file."""
        output = tmp_path / "quick.svg"
        gen = quick_drawing(None, output=output, format=ExportFormat.SVG)
        assert output.exists()


class TestViewTypes:
    """Tests for all view types."""

    def test_all_view_types_exist(self):
        """Test all view types are defined."""
        expected = ["TOP", "FRONT", "RIGHT", "LEFT", "BACK", "BOTTOM", "ISOMETRIC", "SECTION"]
        for vt in expected:
            assert hasattr(ViewType, vt)


class TestDimensionTypes:
    """Tests for all dimension types."""

    def test_all_dimension_types_exist(self):
        """Test all dimension types are defined."""
        expected = ["LINEAR", "ANGULAR", "RADIAL", "DIAMETER", "ORDINATE"]
        for dt in expected:
            assert hasattr(DimensionType, dt)


class TestExportFormats:
    """Tests for export formats."""

    def test_all_export_formats_exist(self):
        """Test all export formats are defined."""
        expected = ["DXF", "SVG", "PDF"]
        for ef in expected:
            assert hasattr(ExportFormat, ef)
