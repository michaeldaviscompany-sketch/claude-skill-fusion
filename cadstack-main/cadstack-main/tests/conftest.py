"""Pytest configuration and fixtures for CADStack tests."""

import pytest
import sys
from pathlib import Path

# Add project root to path so imports work as: from lib.backends.cadquery import ...
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_cadquery(monkeypatch):
    """Mock cadquery module for tests without CAD software."""
    import types

    # Create mock cadquery module
    mock_cq = types.ModuleType("cadquery")

    class MockWorkplane:
        def __init__(self, plane="XY"):
            self._plane = plane
            self._operations = []
            self.name = "mock_object"  # Add name attribute

        def box(self, length, width, height):
            self._operations.append(("box", length, width, height))
            return self

        def circle(self, radius):
            self._operations.append(("circle", radius))
            return self

        def extrude(self, height):
            self._operations.append(("extrude", height))
            return self

        def sphere(self, radius):
            self._operations.append(("sphere", radius))
            return self

        def cone(self, radius1, radius2, height):
            self._operations.append(("cone", radius1, radius2, height))
            return self

        def torus(self, major_radius, minor_radius):
            self._operations.append(("torus", major_radius, minor_radius))
            return self

        def workplane(self, plane=None, offset=None):
            """Return self for chaining workplane operations."""
            return self

        def loft(self):
            """Loft operation."""
            self._operations.append(("loft",))
            return self

        def revolve(self, angleDegrees=360, axisStart=None, axisEnd=None):
            """Revolve operation."""
            self._operations.append(("revolve", angleDegrees))
            return self

        def hLine(self, distance):
            """Horizontal line."""
            self._operations.append(("hLine", distance))
            return self

        def vLine(self, distance):
            """Vertical line."""
            self._operations.append(("vLine", distance))
            return self

        def threePointArc(self, p1, p2, p3=None):
            """Three point arc."""
            self._operations.append(("threePointArc", p1, p2))
            return self

        def close(self):
            """Close the path."""
            self._operations.append(("close",))
            return self

        def center(self, x, y):
            """Move to center point."""
            self._operations.append(("center", x, y))
            return self

        def lineTo(self, x, y):
            """Line to point."""
            self._operations.append(("lineTo", x, y))
            return self

        def line(self, dx, dy):
            """Line by delta."""
            self._operations.append(("line", dx, dy))
            return self

        def union(self, other):
            self._operations.append(("union", other))
            return self

        def cut(self, other):
            self._operations.append(("cut", other))
            return self

        def intersect(self, other):
            self._operations.append(("intersect", other))
            return self

        def translate(self, offset):
            self._operations.append(("translate", offset))
            return self

        def rotate(self, axis, angle):
            self._operations.append(("rotate", axis, angle))
            return self

        def edges(self, selector=None):
            self._operations.append(("edges", selector))
            return self

        def fillet(self, radius):
            self._operations.append(("fillet", radius))
            return self

        def chamfer(self, distance):
            self._operations.append(("chamfer", distance))
            return self

        def val(self):
            class MockValue:
                class BoundingBox:
                    xmin = ymin = zmin = 0
                    xmax = 100
                    ymax = 50
                    zmax = 20
                def Volume(self):
                    return 100000.0  # mm³
                BoundingBox = BoundingBox()
            return MockValue()

    class MockExporters:
        @staticmethod
        def export(shape, filepath):
            # Just create an empty file
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)
            Path(filepath).write_text("mock export")

    mock_cq.Workplane = MockWorkplane
    mock_cq.exporters = MockExporters()

    # Install mock
    sys.modules["cadquery"] = mock_cq
    monkeypatch.setattr("lib.backends.cadquery.cq", mock_cq)
    monkeypatch.setattr("lib.backends.cadquery.CADQUERY_AVAILABLE", True)

    yield mock_cq

    # Cleanup
    if "cadquery" in sys.modules:
        del sys.modules["cadquery"]


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_box_script():
    """A simple CAD script that creates a box."""
    return '''
# Create a simple box
box = backend.create_box(100, 50, 20, "test_box")
print(f"Created box: {box.name}")
'''


@pytest.fixture
def dangerous_script():
    """A script with dangerous patterns that should be blocked."""
    return '''
import os
os.system("rm -rf /")
'''
