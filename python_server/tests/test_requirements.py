import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PYTHON_SERVER_DIR = REPO_ROOT / "python_server"


def declared_requirement_names():
    names = set()
    requirements_path = PYTHON_SERVER_DIR / "requirements.txt"

    for line in requirements_path.read_text().splitlines():
        requirement = line.split("#", 1)[0].strip()
        if not requirement or requirement.startswith("-"):
            continue

        name = re.split(r"[<>=~!;\[]", requirement, maxsplit=1)[0].strip().lower()
        if name:
            names.add(name)

    return names


class RequirementsTests(unittest.TestCase):
    def test_uvicorn_docs_runner_reference_is_declared_runtime_dependency(self):
        uvicorn_reference_paths = [
            REPO_ROOT / "README.md",
            PYTHON_SERVER_DIR / "run.ps1",
            PYTHON_SERVER_DIR / "run.sh",
        ]

        files_invoking_uvicorn = [
            path
            for path in uvicorn_reference_paths
            if "uvicorn" in path.read_text().lower()
        ]

        self.assertTrue(files_invoking_uvicorn, "Expected docs or run scripts to invoke uvicorn")
        self.assertIn("uvicorn", declared_requirement_names())


if __name__ == "__main__":
    unittest.main()
