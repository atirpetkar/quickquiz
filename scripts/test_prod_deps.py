#!/usr/bin/env python3
"""
Test script to verify that the application works with production dependencies only.
This helps catch cases where dev-only packages are accidentally imported in production code.
"""

import os
import shlex
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result."""
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)  # nosec B603
    return result


def test_production_dependencies():
    """Test that the app works with only production dependencies."""

    # Get the project root directory
    project_root = Path(__file__).parent.parent

    print("🔍 Testing production dependencies...")
    print(f"📁 Project root: {project_root}")

    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📂 Using temp directory: {temp_dir}")

        # Create virtual environment
        print("🐍 Creating virtual environment...")
        venv_result = run_command(["python", "-m", "venv", f"{temp_dir}/test_venv"])
        if venv_result.returncode != 0:
            print(f"❌ Failed to create virtual environment: {venv_result.stderr}")
            return False

        # Determine activation script path
        if os.name == "nt":  # Windows
            python_exe = f"{temp_dir}/test_venv/Scripts/python"
        else:  # Unix/Linux/MacOS
            python_exe = f"{temp_dir}/test_venv/bin/python"

        # Install production dependencies
        print("📦 Installing production dependencies...")
        install_cmd = [
            python_exe,
            "-m",
            "pip",
            "install",
            "-r",
            str(project_root / "requirements.txt"),
        ]
        install_result = run_command(install_cmd)

        if install_result.returncode != 0:
            print(f"❌ Failed to install requirements: {install_result.stderr}")
            return False

        print("✅ Production dependencies installed successfully")

        # Test importing the main application
        print("🧪 Testing application imports...")

        # Add the src directory to Python path and test imports
        test_imports = [
            "import sys",
            f"sys.path.insert(0, '{project_root}/src')",
            "from quickquiz.core.config import settings",
            "print('✅ Core config imported successfully')",
            "from quickquiz.models.schemas import *",
            "print('✅ Schemas imported successfully')",
            # Add more critical imports as needed
        ]

        test_script = "; ".join(test_imports)
        import_result = run_command([python_exe, "-c", test_script])

        if import_result.returncode != 0:
            print("❌ Import test failed!")
            print(f"Error: {import_result.stderr}")
            print(f"Output: {import_result.stdout}")
            return False

        print("✅ All imports successful!")
        print(import_result.stdout)

        # Test that the FastAPI app can be created
        print("🚀 Testing FastAPI app creation...")
        app_test = [
            "import sys",
            f"sys.path.insert(0, '{project_root}/src')",
            "from quickquiz.api.main import app",
            "print('✅ FastAPI app created successfully')",
            "print('App imported without errors')",
        ]

        app_test_script = "; ".join(app_test)
        app_result = run_command([python_exe, "-c", app_test_script])

        if app_result.returncode != 0:
            print("❌ FastAPI app creation failed!")
            print(f"Error: {app_result.stderr}")
            return False

        print("✅ FastAPI app test passed!")
        print(app_result.stdout)

    return True


def main():
    """Main function."""
    print("🎯 QuickQuiz-GPT Production Dependency Test")
    print("=" * 50)

    success = test_production_dependencies()

    print("=" * 50)
    if success:
        print("🎉 All tests passed! Your app works with production dependencies only.")
        sys.exit(0)
    else:
        print("💥 Tests failed! You may have dev-only imports in production code.")
        print(
            "\n💡 Check your code for imports of packages that are only in requirements-dev.txt"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
