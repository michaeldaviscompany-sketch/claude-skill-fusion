"""Tests for script validation."""

import pytest
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from lib.utils.helpers import CADScriptValidator


class TestCADScriptValidator:
    """Tests for CADScriptValidator."""

    # =========================================================================
    # Dangerous Pattern Detection
    # =========================================================================

    def test_detect_os_system(self):
        """Test detection of os.system()."""
        script = 'os.system("ls")'
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("os.system" in e for e in errors)

    def test_detect_subprocess(self):
        """Test detection of subprocess calls."""
        script = 'subprocess.run(["ls"])'
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("subprocess" in e for e in errors)

    def test_detect_eval(self):
        """Test detection of eval()."""
        script = 'eval("1 + 1")'
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("eval" in e.lower() for e in errors)

    def test_detect_exec(self):
        """Test detection of exec()."""
        script = 'exec("x = 1")'
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("exec" in e.lower() for e in errors)

    def test_detect_importlib(self):
        """Test detection of importlib."""
        script = 'importlib.import_module("os")'
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("importlib" in e for e in errors)

    def test_detect_open_write(self):
        """Test detection of open() in write mode."""
        script = 'open("file.txt", "w")'
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("write" in e.lower() for e in errors)

    def test_detect_shutil_rmtree(self):
        """Test detection of shutil.rmtree."""
        script = 'shutil.rmtree("/tmp")'
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("shutil" in e for e in errors)

    def test_detect_socket(self):
        """Test detection of socket usage."""
        script = 'socket.connect(("localhost", 8080))'
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("socket" in e for e in errors)

    def test_detect_builtins_access(self):
        """Test detection of __builtins__ access."""
        script = '__builtins__["eval"]("1+1")'
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("builtins" in e.lower() for e in errors)

    def test_detect_globals_call(self):
        """Test detection of globals() call."""
        script = 'g = globals()'
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("globals" in e.lower() for e in errors)

    # =========================================================================
    # Safe Scripts
    # =========================================================================

    def test_safe_box_script(self):
        """Test that a simple box script passes."""
        script = '''
# Create a simple box
box = backend.create_box(100, 50, 20, "test_box")
'''
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert is_safe
        assert len(errors) == 0

    def test_safe_math_operations(self):
        """Test that math operations are allowed."""
        script = '''
import math
radius = 10
area = math.pi * radius ** 2
'''
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert is_safe

    def test_safe_cad_operations(self):
        """Test that CAD operations are allowed."""
        script = '''
# Create a box with a hole
box = backend.create_box(100, 100, 20, "plate")
hole = backend.create_cylinder(5, 20, "hole")
result = backend.cut(box, hole, "plate_with_hole")
'''
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert is_safe

    # =========================================================================
    # AST Analysis
    # =========================================================================

    def test_ast_detects_hidden_import(self):
        """Test that AST catches imports hidden from regex."""
        script = '''
import os
path = os.path.join("a", "b")
'''
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("import" in e.lower() for e in errors)

    def test_ast_detects_blocked_module(self):
        """Test that AST blocks specific modules."""
        for module in ["os", "subprocess", "shutil", "socket", "pickle"]:
            script = f'import {module}'
            is_safe, errors = CADScriptValidator.validate_strict(script)
            assert not is_safe, f"Should block import of {module}"

    def test_syntax_error_in_script(self):
        """Test handling of syntax errors."""
        script = 'def broken('  # Incomplete function definition
        is_safe, errors = CADScriptValidator.validate_strict(script)
        assert not is_safe
        assert any("syntax" in e.lower() for e in errors)

    # =========================================================================
    # Legacy Validation (warns only)
    # =========================================================================

    def test_legacy_returns_warnings(self):
        """Test that legacy validate returns warnings, not errors."""
        script = 'os.system("ls")'
        is_safe, warnings = CADScriptValidator.validate(script)
        assert not is_safe
        assert len(warnings) > 0
        assert "dangerous" in warnings[0].lower()
