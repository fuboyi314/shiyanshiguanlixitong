import importlib.util
import tempfile
import unittest
from pathlib import Path

PANDAS_AVAILABLE = importlib.util.find_spec("pandas") is not None


@unittest.skipUnless(PANDAS_AVAILABLE, "pandas is required for sample-data tests")
class TestSampleDataGenerator(unittest.TestCase):
    def test_main_generates_three_excel_files(self) -> None:
        import sample_data.generate_sample_data as generator

        temp_dir = Path(tempfile.mkdtemp(prefix="sample-data-test-"))
        original_output = generator.OUTPUT_DIR
        generator.OUTPUT_DIR = temp_dir
        try:
            generator.main()
        finally:
            generator.OUTPUT_DIR = original_output

        self.assertTrue((temp_dir / "theory_schedule.xlsx").exists())
        self.assertTrue((temp_dir / "labs.xlsx").exists())
        self.assertTrue((temp_dir / "lab_tasks.xlsx").exists())


if __name__ == "__main__":
    unittest.main()
