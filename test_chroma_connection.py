from pathlib import Path


SPEC_DIR = Path(__file__).parent / "specs"
EXPECTED_FILES = [
	"constitution.md",
	"plan.md",
	"specification.md",
	"tasks.md",
]


def test_specs_files_exist_and_nonempty():
	assert SPEC_DIR.exists() and SPEC_DIR.is_dir(), f"Missing specs directory: {SPEC_DIR}"
	for name in EXPECTED_FILES:
		p = SPEC_DIR / name
		assert p.exists(), f"Missing spec file: {p}"
		assert p.stat().st_size > 0, f"Spec file is empty: {p}"

