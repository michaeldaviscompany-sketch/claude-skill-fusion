"""Tests for CadQuery backend."""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestCadQueryBackend:
    """Tests for CadQuery backend functionality."""

    @pytest.fixture
    def backend(self, mock_cadquery):
        """Create a CadQuery backend instance with mocked cadquery."""
        from lib.backends.cadquery import CadQueryBackend
        return CadQueryBackend()

    # =========================================================================
    # Document Management
    # =========================================================================

    def test_create_document(self, backend):
        """Test document creation."""
        doc = backend.create_document("test_doc")
        assert doc.name == "test_doc"
        assert doc.objects == []

    def test_backend_info(self, backend):
        """Test backend info."""
        info = backend.get_info()
        assert info["name"] == "cadquery"
        assert info["supports_headless"] is True
        assert info["available"] is True
        assert "step" in info["supported_formats"]

    # =========================================================================
    # Primitive Creation
    # =========================================================================

    def test_create_box(self, backend):
        """Test box creation."""
        backend.create_document("test")
        box = backend.create_box(100, 50, 20, "test_box")
        assert box.name == "test_box"
        assert box.object_type == "Box"
        assert "test_box" in backend.list_objects()

    def test_create_cylinder(self, backend):
        """Test cylinder creation."""
        backend.create_document("test")
        cyl = backend.create_cylinder(10, 50, "test_cyl")
        assert cyl.name == "test_cyl"
        assert cyl.object_type == "Cylinder"

    def test_create_sphere(self, backend):
        """Test sphere creation."""
        backend.create_document("test")
        sphere = backend.create_sphere(25, "test_sphere")
        assert sphere.name == "test_sphere"
        assert sphere.object_type == "Sphere"

    def test_create_cone(self, backend):
        """Test cone creation."""
        backend.create_document("test")
        cone = backend.create_cone(20, 10, 30, "test_cone")
        assert cone.name == "test_cone"
        assert cone.object_type == "Cone"

    def test_create_torus(self, backend):
        """Test torus creation."""
        backend.create_document("test")
        torus = backend.create_torus(50, 10, "test_torus")
        assert torus.name == "test_torus"
        assert torus.object_type == "Torus"

    # =========================================================================
    # Name Uniqueness
    # =========================================================================

    def test_unique_names(self, backend):
        """Test that duplicate names get unique suffixes."""
        backend.create_document("test")
        box1 = backend.create_box(10, 10, 10, "box")
        box2 = backend.create_box(10, 10, 10, "box")
        box3 = backend.create_box(10, 10, 10, "box")

        assert box1.name == "box"
        assert box2.name == "box_2"
        assert box3.name == "box_3"

    # =========================================================================
    # Boolean Operations
    # =========================================================================

    def test_fuse(self, backend):
        """Test boolean union."""
        backend.create_document("test")
        box1 = backend.create_box(100, 100, 20, "box1")
        box2 = backend.create_box(50, 50, 20, "box2")
        fusion = backend.fuse(box1, box2, "fused")
        assert fusion.object_type == "Fusion"

    def test_cut(self, backend):
        """Test boolean difference."""
        backend.create_document("test")
        box = backend.create_box(100, 100, 20, "box")
        hole = backend.create_cylinder(5, 20, "hole")
        result = backend.cut(box, hole, "with_hole")
        assert result.object_type == "Cut"

    def test_intersect(self, backend):
        """Test boolean intersection."""
        backend.create_document("test")
        box1 = backend.create_box(100, 100, 20, "box1")
        box2 = backend.create_box(50, 50, 20, "box2")
        result = backend.intersect(box1, box2, "intersection")
        assert result.object_type == "Intersection"

    # =========================================================================
    # Transformations
    # =========================================================================

    def test_move(self, backend):
        """Test object movement."""
        backend.create_document("test")
        box = backend.create_box(10, 10, 10, "box")
        backend.move(box, 50, 25, 10)
        # Move should succeed without error

    def test_rotate(self, backend):
        """Test object rotation."""
        backend.create_document("test")
        box = backend.create_box(10, 10, 10, "box")
        backend.rotate(box, (0, 0, 1), 45)
        # Rotate should succeed without error

    # =========================================================================
    # Feature Operations
    # =========================================================================

    def test_fillet(self, backend):
        """Test fillet operation."""
        backend.create_document("test")
        box = backend.create_box(10, 10, 10, "box")
        filleted = backend.fillet(box, [], 2)
        assert "Fillet" in filleted.name

    def test_chamfer(self, backend):
        """Test chamfer operation."""
        backend.create_document("test")
        box = backend.create_box(10, 10, 10, "box")
        chamfered = backend.chamfer(box, [], 2)
        assert "Chamfer" in chamfered.name

    # =========================================================================
    # Export
    # =========================================================================

    def test_export_step(self, backend, temp_output_dir):
        """Test STEP export."""
        backend.create_document("test")
        backend.create_box(100, 50, 20, "box")

        output_path = temp_output_dir / "test.step"
        success = backend.export(backend._current_doc, output_path, "step")
        assert success is True

    def test_export_stl(self, backend, temp_output_dir):
        """Test STL export."""
        backend.create_document("test")
        backend.create_box(100, 50, 20, "box")

        output_path = temp_output_dir / "test.stl"
        success = backend.export(backend._current_doc, output_path, "stl")
        assert success is True

    def test_export_empty_document_raises(self, backend, temp_output_dir):
        """Test that exporting empty document raises error."""
        backend.create_document("test")

        from lib.exceptions import EmptyDocumentError
        output_path = temp_output_dir / "empty.step"
        with pytest.raises(EmptyDocumentError):
            backend.export(backend._current_doc, output_path, "step")

    # =========================================================================
    # Recompute
    # =========================================================================

    def test_recompute_no_op(self, backend):
        """Test that recompute is a no-op for CadQuery."""
        backend.create_document("test")
        # Should not raise
        backend.recompute(backend._current_doc)

    # =========================================================================
    # Utilities
    # =========================================================================

    def test_list_objects(self, backend):
        """Test listing objects."""
        backend.create_document("test")
        backend.create_box(10, 10, 10, "box1")
        backend.create_box(10, 10, 10, "box2")

        objects = backend.list_objects()
        assert "box1" in objects
        assert "box2" in objects

    def test_get_object(self, backend):
        """Test getting object by name."""
        backend.create_document("test")
        box = backend.create_box(10, 10, 10, "my_box")

        retrieved = backend.get_object("my_box")
        assert retrieved is not None
        assert retrieved.name == "my_box"

    def test_get_last_object(self, backend):
        """Test getting last created object."""
        backend.create_document("test")
        backend.create_box(10, 10, 10, "first")
        backend.create_box(10, 10, 10, "second")

        last = backend.get_last_object()
        assert last.name == "second"
