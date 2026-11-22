"""Unit tests for assembly module."""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.assembly import (
    Assembly,
    Constraint,
    ConstraintType,
    FeatureReference,
    FeatureType,
    PartInstance,
    AssemblyConstraintError,
    AssemblyResult,
    create_assembly,
)


class TestFeatureReference:
    """Tests for FeatureReference."""

    def test_feature_reference_creation(self):
        """Test creating a feature reference."""
        ref = FeatureReference(
            part_name="bracket",
            feature_type=FeatureType.FACE,
            feature_name="top_face"
        )
        assert ref.part_name == "bracket"
        assert ref.feature_type == FeatureType.FACE
        assert ref.feature_name == "top_face"

    def test_feature_reference_str(self):
        """Test string representation."""
        ref = FeatureReference("part", FeatureType.EDGE, "edge1")
        assert str(ref) == "part.edge1"


class TestConstraint:
    """Tests for Constraint."""

    def test_constraint_creation(self):
        """Test creating a constraint."""
        f1 = FeatureReference("part1", FeatureType.FACE, "face1")
        f2 = FeatureReference("part2", FeatureType.FACE, "face2")
        c = Constraint(ConstraintType.MATE, f1, f2, offset=5.0)
        assert c.constraint_type == ConstraintType.MATE
        assert c.offset == 5.0

    def test_constraint_str(self):
        """Test string representation."""
        f1 = FeatureReference("p1", FeatureType.FACE, "f1")
        f2 = FeatureReference("p2", FeatureType.FACE, "f2")
        c = Constraint(ConstraintType.ALIGN, f1, f2)
        assert "align" in str(c).lower()
        assert "p1.f1" in str(c)
        assert "p2.f2" in str(c)


class TestPartInstance:
    """Tests for PartInstance."""

    def test_part_instance_creation(self):
        """Test creating a part instance."""
        part = PartInstance(
            name="bracket",
            part_type="custom",
            position=(10.0, 20.0, 30.0),
            rotation=(0.0, 90.0, 0.0),
            fixed=True
        )
        assert part.name == "bracket"
        assert part.position == (10.0, 20.0, 30.0)
        assert part.fixed is True

    def test_part_instance_defaults(self):
        """Test default values."""
        part = PartInstance(name="screw", part_type="screw_metric")
        assert part.position == (0.0, 0.0, 0.0)
        assert part.rotation == (0.0, 0.0, 0.0)
        assert part.fixed is False
        assert part.metadata == {}


class TestAssembly:
    """Tests for Assembly class."""

    def test_assembly_creation(self):
        """Test creating an assembly."""
        asm = Assembly("test_assembly")
        assert asm.name == "test_assembly"
        assert asm.part_count == 0
        assert asm.constraint_count == 0

    def test_add_part(self):
        """Test adding a part."""
        asm = Assembly("test")
        asm.add_part("bracket", "custom", fixed=True)
        assert asm.part_count == 1
        assert asm.get_part("bracket") is not None

    def test_add_part_chaining(self):
        """Test that add_part returns self for chaining."""
        asm = Assembly("test")
        result = asm.add_part("p1", "type1")
        assert result is asm

    def test_add_duplicate_part_raises(self):
        """Test that duplicate part names raise error."""
        asm = Assembly("test")
        asm.add_part("part1", "type1")
        with pytest.raises(AssemblyConstraintError):
            asm.add_part("part1", "type2")

    def test_add_constraint(self):
        """Test adding a constraint."""
        asm = Assembly("test")
        asm.add_part("p1", "type1", fixed=True)
        asm.add_part("p2", "type2")
        asm.add_constraint(
            ConstraintType.MATE,
            FeatureReference("p1", FeatureType.FACE, "f1"),
            FeatureReference("p2", FeatureType.FACE, "f2")
        )
        assert asm.constraint_count == 1

    def test_add_constraint_missing_part_raises(self):
        """Test that constraint with missing part raises error."""
        asm = Assembly("test")
        asm.add_part("p1", "type1")
        with pytest.raises(AssemblyConstraintError):
            asm.add_constraint(
                ConstraintType.MATE,
                FeatureReference("p1", FeatureType.FACE, "f1"),
                FeatureReference("nonexistent", FeatureType.FACE, "f2")
            )

    def test_mate_convenience(self):
        """Test mate convenience method."""
        asm = Assembly("test")
        asm.add_part("p1", "type1", fixed=True)
        asm.add_part("p2", "type2")
        asm.mate("p1", "face1", "p2", "face2", offset=10.0)
        assert asm.constraint_count == 1
        constraints = asm.list_constraints()
        assert "mate" in constraints[0].lower()

    def test_align_convenience(self):
        """Test align convenience method."""
        asm = Assembly("test")
        asm.add_part("p1", "type1", fixed=True)
        asm.add_part("p2", "type2")
        asm.align("p1", "face1", "p2", "face2")
        assert asm.constraint_count == 1

    def test_distance_convenience(self):
        """Test distance convenience method."""
        asm = Assembly("test")
        asm.add_part("p1", "type1", fixed=True)
        asm.add_part("p2", "type2")
        asm.distance("p1", "face1", "p2", "face2", distance=50.0)
        assert asm.constraint_count == 1

    def test_angle_convenience(self):
        """Test angle convenience method."""
        asm = Assembly("test")
        asm.add_part("p1", "type1", fixed=True)
        asm.add_part("p2", "type2")
        asm.angle("p1", "face1", "p2", "face2", angle_degrees=45.0)
        assert asm.constraint_count == 1


class TestAssemblySolve:
    """Tests for assembly solving."""

    def test_solve_no_fixed_parts_warning(self):
        """Test that solving without fixed parts warns."""
        asm = Assembly("test")
        asm.add_part("p1", "type1")
        result = asm.solve()
        assert result.success is True
        assert any("fixed" in w.lower() for w in result.warnings)

    def test_solve_returns_positions(self):
        """Test that solve returns positions."""
        asm = Assembly("test")
        asm.add_part("p1", "type1", position=(10, 20, 30), fixed=True)
        asm.add_part("p2", "type2", position=(0, 0, 0))
        result = asm.solve()
        assert result.success is True
        assert "p1" in result.positions
        assert "p2" in result.positions
        assert result.positions["p1"] == (10, 20, 30)

    def test_solve_applies_constraints(self):
        """Test that solve applies constraints."""
        asm = Assembly("test")
        asm.add_part("p1", "type1", position=(0, 0, 0), fixed=True)
        asm.add_part("p2", "type2", position=(100, 100, 100))
        asm.add_constraint(
            ConstraintType.MATE,
            FeatureReference("p1", FeatureType.FACE, "f1"),
            FeatureReference("p2", FeatureType.FACE, "f2"),
            offset=50.0
        )
        result = asm.solve()
        assert result.success is True
        # Part2 should be moved closer to part1


class TestAssemblyMethods:
    """Tests for other assembly methods."""

    def test_list_parts(self):
        """Test listing parts."""
        asm = Assembly("test")
        asm.add_part("p1", "t1")
        asm.add_part("p2", "t2")
        parts = asm.list_parts()
        assert "p1" in parts
        assert "p2" in parts

    def test_list_constraints(self):
        """Test listing constraints."""
        asm = Assembly("test")
        asm.add_part("p1", "t1", fixed=True)
        asm.add_part("p2", "t2")
        asm.mate("p1", "f1", "p2", "f2")
        constraints = asm.list_constraints()
        assert len(constraints) == 1

    def test_clear(self):
        """Test clearing assembly."""
        asm = Assembly("test")
        asm.add_part("p1", "t1")
        asm.add_part("p2", "t2")
        asm.mate("p1", "f1", "p2", "f2")
        asm.clear()
        assert asm.part_count == 0
        assert asm.constraint_count == 0

    def test_to_dict(self):
        """Test exporting to dictionary."""
        asm = Assembly("test")
        asm.add_part("p1", "type1", fixed=True)
        d = asm.to_dict()
        assert d["name"] == "test"
        assert len(d["parts"]) == 1
        assert len(d["constraints"]) == 0


class TestCreateAssembly:
    """Tests for create_assembly convenience function."""

    def test_create_assembly(self):
        """Test creating assembly via convenience function."""
        asm = create_assembly("my_assembly")
        assert asm.name == "my_assembly"
        assert isinstance(asm, Assembly)


class TestAssemblyResult:
    """Tests for AssemblyResult."""

    def test_result_defaults(self):
        """Test result defaults."""
        result = AssemblyResult(success=True)
        assert result.positions == {}
        assert result.rotations == {}
        assert result.warnings == []
        assert result.errors == []


class TestConstraintTypes:
    """Tests for all constraint types."""

    def test_all_constraint_types_exist(self):
        """Test all constraint types are defined."""
        expected = ["mate", "align", "angle", "distance", "coincident", "parallel", "perpendicular", "tangent"]
        for ct in expected:
            assert hasattr(ConstraintType, ct.upper())
