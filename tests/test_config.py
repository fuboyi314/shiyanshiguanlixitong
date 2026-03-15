import unittest

from utils.config import get_default_field_mappings, merge_user_field_mappings


class TestFieldMappings(unittest.TestCase):
    def test_get_default_returns_copy(self) -> None:
        mappings = get_default_field_mappings()
        mappings["theory"]["class_name"] = "X"

        fresh = get_default_field_mappings()
        self.assertEqual(fresh["theory"]["class_name"], "班级")

    def test_merge_user_mapping(self) -> None:
        merged = merge_user_field_mappings(
            {
                "task": {
                    "project_name": "实验名称",
                    "student_count": "学生数",
                },
                "unknown": {"field": "ignored"},
            }
        )

        self.assertEqual(merged["task"]["project_name"], "实验名称")
        self.assertEqual(merged["task"]["student_count"], "学生数")
        self.assertIn("theory", merged)


if __name__ == "__main__":
    unittest.main()
