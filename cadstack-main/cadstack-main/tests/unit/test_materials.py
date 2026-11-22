"""Tests for materials module."""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.materials import (
    get_material,
    list_materials,
    search_materials,
    calculate_mass,
    show_material_info,
    estimate_mass_string,
    MATERIALS,
)


class TestMaterialsDatabase:
    """Tests for materials database."""

    def test_list_materials_returns_list(self):
        """Test that list_materials returns a sorted list."""
        materials = list_materials()
        assert isinstance(materials, list)
        assert len(materials) > 0
        assert materials == sorted(materials)  # Should be sorted

    def test_list_materials_has_common_materials(self):
        """Test that common engineering materials are present."""
        materials = list_materials()
        assert "aluminum_6061" in materials
        assert "steel_1018" in materials
        assert "abs_plastic" in materials

    def test_get_material_existing(self):
        """Test getting an existing material."""
        material = get_material("aluminum_6061")
        assert material is not None
        assert material.name == "aluminum_6061"
        assert material.density > 0
        assert material.color is not None

    def test_get_material_nonexistent(self):
        """Test getting a non-existent material returns None."""
        material = get_material("nonexistent_material")
        assert material is None

    def test_get_material_case_insensitive(self):
        """Test that material lookup is case-insensitive."""
        material = get_material("ALUMINUM_6061")
        assert material is not None
        assert material.name == "aluminum_6061"

    def test_get_material_aliases(self):
        """Test that common aliases work."""
        # "aluminum" should map to "aluminum_6061"
        material = get_material("aluminum")
        assert material is not None
        assert "aluminum" in material.name

        # "steel" should map to "steel_1018"
        material = get_material("steel")
        assert material is not None
        assert "steel" in material.name


class TestSearchMaterials:
    """Tests for material search."""

    def test_search_by_name(self):
        """Test searching by material name."""
        results = search_materials("aluminum")
        assert len(results) > 0
        for material in results:
            assert "aluminum" in material.name.lower()

    def test_search_by_description(self):
        """Test searching by material description."""
        results = search_materials("stainless")
        assert len(results) > 0

    def test_search_no_results(self):
        """Test search with no results."""
        results = search_materials("nonexistent_xyz")
        assert len(results) == 0


class TestMassCalculation:
    """Tests for mass calculation."""

    def test_calculate_mass_valid(self):
        """Test mass calculation with valid inputs."""
        # Aluminum 6061 density is ~2.7 g/cm³
        # 100 cm³ = 100,000 mm³
        volume_mm3 = 100000  # 100 cm³
        mass = calculate_mass(volume_mm3, "aluminum_6061")
        assert mass is not None
        # 100 cm³ * 2.7 g/cm³ = 270 g
        assert abs(mass - 270) < 5  # Allow some tolerance

    def test_calculate_mass_invalid_material(self):
        """Test mass calculation with invalid material."""
        volume_mm3 = 100000
        mass = calculate_mass(volume_mm3, "invalid_material")
        assert mass is None

    def test_calculate_mass_zero_volume(self):
        """Test mass calculation with zero volume."""
        mass = calculate_mass(0, "aluminum_6061")
        assert mass == 0


class TestMaterialInfo:
    """Tests for info string functions."""

    def test_show_material_info_existing(self):
        """Test info string for existing material."""
        info = show_material_info("aluminum_6061")
        assert "aluminum_6061" in info
        assert "2.7" in info  # Density (may be 2.7 or 2.70)
        assert "g/cm" in info

    def test_show_material_info_nonexistent(self):
        """Test info string for non-existent material."""
        info = show_material_info("nonexistent")
        assert "not found" in info.lower()

    def test_estimate_mass_string_valid(self):
        """Test mass estimate string."""
        result = estimate_mass_string(100000, "aluminum_6061")  # 100 cm³
        assert "g" in result

    def test_estimate_mass_string_kg(self):
        """Test mass estimate string for large mass."""
        # 1 liter = 1,000,000 mm³ of steel ≈ 7.87 kg
        result = estimate_mass_string(1000000, "steel_1018")
        assert "kg" in result


class TestMaterialProperties:
    """Tests for material properties."""

    def test_material_has_density(self):
        """Test that all materials have density."""
        for name, material in MATERIALS.items():
            assert hasattr(material, "density")
            assert material.density > 0, f"{name} has invalid density"

    def test_material_has_color(self):
        """Test that all materials have color."""
        for name, material in MATERIALS.items():
            assert hasattr(material, "color")
            assert material.color is not None, f"{name} has no color"

    def test_steel_density_higher_than_aluminum(self):
        """Test that steel is denser than aluminum."""
        steel = get_material("steel_1018")
        aluminum = get_material("aluminum_6061")
        if steel and aluminum:
            assert steel.density > aluminum.density

    def test_plastic_density_lower_than_metal(self):
        """Test that plastics are less dense than metals."""
        abs_mat = get_material("abs_plastic")
        steel = get_material("steel_1018")
        if abs_mat and steel:
            assert abs_mat.density < steel.density
