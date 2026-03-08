import json
import unittest

from course_store import (
    CourseStore,
    DATA_FILE,
    derive_course_level,
    normalize_department_code,
    parse_hours_range,
    store,
)


class NormalizationTests(unittest.TestCase):
    def test_loads_courses_and_indexes(self) -> None:
        local_store = CourseStore.from_file(DATA_FILE)
        self.assertGreater(len(local_store.courses), 3000)
        self.assertIn(370, local_store.by_id)
        self.assertIn("ARI", local_store.by_department)

    def test_course_level_derivation(self) -> None:
        self.assertEqual(derive_course_level("320K"), 3)
        self.assertEqual(derive_course_level("119S"), 1)
        self.assertIsNone(derive_course_level(None))

    def test_department_normalization(self) -> None:
        self.assertEqual(normalize_department_code("C S"), "CS")
        self.assertEqual(normalize_department_code(" cs "), "CS")

    def test_schedule_parsing(self) -> None:
        self.assertEqual(parse_hours_range("8:00 a.m.-12:30 p.m."), (480, 750))

        multi_meeting = store.get_course_details(375)
        self.assertEqual(len(multi_meeting["schedule"]), 2)
        self.assertEqual(multi_meeting["schedule"][0]["days"], "TTH")


class ToolBehaviorTests(unittest.TestCase):
    def test_search_courses_department_and_status(self) -> None:
        results = store.search_courses(department="CS", status="OPEN", limit=5)
        self.assertGreater(len(results), 0)
        self.assertTrue(all(normalize_department_code(item["department"]) == "CS" for item in results))
        self.assertTrue(all(item["status"] == "OPEN" for item in results))

    def test_search_courses_days(self) -> None:
        results = store.search_courses(days="TTH", limit=10)
        self.assertGreater(len(results), 0)
        self.assertTrue(all("TTH" in item["scheduleSummary"] for item in results))

    def test_search_courses_can_return_all_matches(self) -> None:
        limited_results = store.search_courses(department="CS", status="OPEN", limit=5)
        all_results = store.search_courses(department="CS", status="OPEN", return_all=True)
        self.assertGreater(len(all_results), len(limited_results))

    def test_search_courses_keyword(self) -> None:
        results = store.search_courses(keyword="design", limit=10)
        self.assertGreater(len(results), 0)
        serialized = json.dumps(results).lower()
        self.assertIn("design", serialized)

    def test_get_course_details(self) -> None:
        details = store.get_course_details(370)
        self.assertEqual(details["uniqueId"], 370)
        self.assertEqual(details["department"], "ARI")

    def test_get_course_details_not_found(self) -> None:
        with self.assertRaises(KeyError):
            store.get_course_details(99999999)


if __name__ == "__main__":
    unittest.main()
