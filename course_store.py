from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


DATA_FILE = Path(__file__).with_name("ut-courses.json")
TIME_PATTERN = re.compile(
    r"^(?P<start>\d{1,2}:\d{2} [ap]\.m\.)-(?P<end>\d{1,2}:\d{2} [ap]\.m\.)$"
)


# Convert a single clock time string into minutes since midnight for easy filtering.
def parse_time_to_minutes(value: str | None) -> int | None:
    if not value:
        return None

    normalized = value.replace(".", "").upper()
    parsed = datetime.strptime(normalized, "%I:%M %p")
    return parsed.hour * 60 + parsed.minute


# Split a meeting time range into numeric start and end values.
def parse_hours_range(value: str | None) -> tuple[int | None, int | None]:
    if not value:
        return (None, None)

    match = TIME_PATTERN.match(value.strip())
    if not match:
        return (None, None)

    start = parse_time_to_minutes(match.group("start"))
    end = parse_time_to_minutes(match.group("end"))
    return (start, end)


# Derive the UT course level from the first digit in the course number.
def derive_course_level(number: str | None) -> int | None:
    if not number:
        return None

    match = re.search(r"(\d)", number)
    return int(match.group(1)) if match else None


# Normalize department codes so queries like "CS" match raw values like "C S".
def normalize_department_code(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", "", value).upper()


# Flatten description content into a single searchable string.
def normalize_description(value: Any) -> str:
    if isinstance(value, list):
        return " ".join(str(item).strip() for item in value if str(item).strip())
    if value is None:
        return ""
    return str(value).strip()


# Extract instructor full names into a simple list for search and display.
def normalize_instructors(value: Any) -> list[str]:
    names: list[str] = []
    if not isinstance(value, list):
        return names

    for instructor in value:
        if not isinstance(instructor, dict):
            continue
        full_name = str(instructor.get("fullName") or "").strip()
        if full_name:
            names.append(full_name)
    return names


# Normalize schedule rows and build a compact human-readable summary string.
def normalize_schedule(value: Any) -> tuple[list[dict[str, Any]], str]:
    normalized: list[dict[str, Any]] = []
    summaries: list[str] = []

    if not isinstance(value, list):
        return (normalized, "")

    for meeting in value:
        if not isinstance(meeting, dict):
            continue

        days = str(meeting.get("days") or "").strip()
        hours = str(meeting.get("hours") or "").strip()
        location = str(meeting.get("location") or "").strip()
        start_minutes, end_minutes = parse_hours_range(hours)

        normalized_meeting = {
            "days": days,
            "hours": hours,
            "location": location,
            "startMinutes": start_minutes,
            "endMinutes": end_minutes,
        }
        normalized.append(normalized_meeting)

        parts = [part for part in [days, hours, location] if part]
        if parts:
            summaries.append(" ".join(parts))

    return (normalized, " | ".join(summaries))


@dataclass(slots=True)
class CourseStore:
    courses: list[dict[str, Any]]
    by_id: dict[int, dict[str, Any]]
    by_department: dict[str, list[dict[str, Any]]]
    by_instructor: dict[str, list[dict[str, Any]]]
    departments: list[str]
    semester_summary: dict[str, Any]

    @classmethod
    def from_file(cls, path: Path) -> "CourseStore":
        with path.open("r", encoding="utf-8") as handle:
            raw_courses = json.load(handle)

        if not isinstance(raw_courses, list):
            raise ValueError("Expected ut-courses.json to contain a list of courses.")

        courses: list[dict[str, Any]] = []
        by_id: dict[int, dict[str, Any]] = {}
        by_department: dict[str, list[dict[str, Any]]] = {}
        by_instructor: dict[str, list[dict[str, Any]]] = {}
        departments: set[str] = set()
        semester_counts: dict[str, int] = {}

        for raw in raw_courses:
            if not isinstance(raw, dict):
                continue

            unique_id = int(raw["uniqueId"])
            department = str(raw.get("department") or "").strip()
            department_key = normalize_department_code(department)
            number = str(raw.get("number") or "").strip()
            instructors = normalize_instructors(raw.get("instructors"))
            normalized_schedule, schedule_summary = normalize_schedule(raw.get("schedule"))
            description = normalize_description(raw.get("description"))
            semester = raw.get("semester") if isinstance(raw.get("semester"), dict) else {}

            course = {
                "uniqueId": unique_id,
                "fullName": str(raw.get("fullName") or "").strip(),
                "courseName": str(raw.get("courseName") or "").strip(),
                "department": department,
                "departmentKey": department_key,
                "number": number,
                "creditHours": raw.get("creditHours"),
                "status": str(raw.get("status") or "").strip(),
                "instructionMode": str(raw.get("instructionMode") or "").strip(),
                "instructors": instructors,
                "schedule": normalized_schedule,
                "scheduleSummary": schedule_summary,
                "description": description,
                "url": str(raw.get("url") or "").strip(),
                "semester": {
                    "code": semester.get("code"),
                    "season": semester.get("season"),
                    "year": semester.get("year"),
                },
                "courseLevel": derive_course_level(number),
                "flags": raw.get("flags") if isinstance(raw.get("flags"), list) else [],
                "core": raw.get("core") if isinstance(raw.get("core"), list) else [],
                "isReserved": bool(raw.get("isReserved", False)),
                "scrapedAt": raw.get("scrapedAt"),
            }
            course["keywordText"] = " ".join(
                part.lower()
                for part in [course["fullName"], course["courseName"], course["description"]]
                if part
            )
            course["instructorSearch"] = " ".join(name.lower() for name in instructors)

            courses.append(course)
            by_id[unique_id] = course

            if department_key:
                departments.add(department)
                by_department.setdefault(department_key, []).append(course)

            for name in instructors:
                instructor_key = name.lower()
                by_instructor.setdefault(instructor_key, []).append(course)

            semester_key = json.dumps(course["semester"], sort_keys=True)
            semester_counts[semester_key] = semester_counts.get(semester_key, 0) + 1

        top_semester = {}
        if semester_counts:
            most_common_key = max(semester_counts, key=semester_counts.get)
            top_semester = json.loads(most_common_key)

        return cls(
            courses=courses,
            by_id=by_id,
            by_department=by_department,
            by_instructor=by_instructor,
            departments=sorted(departments),
            semester_summary=top_semester,
        )

    def search_courses(
        self,
        department: str | None = None,
        keyword: str | None = None,
        status: str | None = None,
        instruction_mode: str | None = None,
        course_level: int | None = None,
        days: str | None = None,
        limit: int | None = 10,
        return_all: bool = False,
    ) -> list[dict[str, Any]]:
        department_value = normalize_department_code(department)
        courses = self.by_department.get(department_value, self.courses) if department else self.courses

        keyword_value = keyword.lower().strip() if keyword else None
        status_value = status.lower().strip() if status else None
        instruction_mode_value = instruction_mode.lower().strip() if instruction_mode else None
        days_value = days.upper().strip() if days else None
        effective_limit = None if return_all or limit is None else max(1, limit)

        results: list[dict[str, Any]] = []
        for course in courses:
            if department_value and course["departmentKey"] != department_value:
                continue
            if keyword_value and keyword_value not in course["keywordText"]:
                continue
            if status_value and course["status"].lower() != status_value:
                continue
            if instruction_mode_value and course["instructionMode"].lower() != instruction_mode_value:
                continue
            if course_level is not None and course["courseLevel"] != course_level:
                continue
            if days_value and not any(meeting["days"].upper() == days_value for meeting in course["schedule"]):
                continue

            results.append(self.to_search_result(course))
            if effective_limit is not None and len(results) >= effective_limit:
                break

        return results

    def get_course_details(self, unique_id: int) -> dict[str, Any]:
        course = self.by_id.get(unique_id)
        if course is None:
            raise KeyError(f"Course with uniqueId={unique_id} was not found.")
        return course

    @staticmethod
    def to_search_result(course: dict[str, Any]) -> dict[str, Any]:
        return {
            "uniqueId": course["uniqueId"],
            "fullName": course["fullName"],
            "department": course["department"],
            "number": course["number"],
            "creditHours": course["creditHours"],
            "status": course["status"],
            "instructionMode": course["instructionMode"],
            "instructors": course["instructors"],
            "scheduleSummary": course["scheduleSummary"],
            "url": course["url"],
        }

    def dataset_info(self) -> dict[str, Any]:
        return {
            "courseCount": len(self.courses),
            "semester": self.semester_summary,
            "supportedFilters": [
                "department",
                "keyword",
                "status",
                "instruction_mode",
                "course_level",
                "days",
                "limit",
                "return_all",
            ],
            "searchResultFields": [
                "uniqueId",
                "fullName",
                "department",
                "number",
                "creditHours",
                "status",
                "instructionMode",
                "instructors",
                "scheduleSummary",
                "url",
            ],
            "recordFields": [
                "uniqueId",
                "fullName",
                "courseName",
                "department",
                "number",
                "creditHours",
                "status",
                "instructionMode",
                "instructors",
                "schedule",
                "description",
                "semester",
                "courseLevel",
                "url",
                "flags",
                "core",
                "isReserved",
                "scrapedAt",
            ],
        }


store = CourseStore.from_file(DATA_FILE)
