"""Loads versioned course packages from content/<course_id>/ (PRD section 19)."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ContentError(RuntimeError):
    pass


@dataclass(frozen=True)
class Fixture:
    fixture_id: str
    version: str
    data: dict[str, Any]

    def business_name(self, lang: str) -> str:
        return self.data["business_name"].get(lang) or self.data["business_name"]["ar"]

    def brief(self, lang: str) -> str:
        return self.data["brief"].get(lang) or self.data["brief"]["ar"]

    @property
    def allowed_numbers(self) -> list[str]:
        return self.data.get("allowed_numbers", [])

    @property
    def context_markers(self) -> list[str]:
        return self.data.get("context_markers", [])

    @property
    def suggested(self) -> dict[str, str]:
        return self.data.get("suggested", {})

    @property
    def prompts(self) -> dict[str, str]:
        return self.data.get("prompts", {})

    @property
    def template(self) -> dict[str, Any]:
        return self.data["template_draft"]


@dataclass
class Course:
    course_id: str
    version: str
    data: dict[str, Any]
    lessons: dict[str, dict[str, Any]]
    recipes: dict[str, dict[str, Any]] = field(default_factory=dict)
    fixtures: dict[str, Fixture] = field(default_factory=dict)
    rubrics: dict[str, dict[str, Any]] = field(default_factory=dict)
    lab_templates: dict[str, dict[str, Any]] = field(default_factory=dict)
    passages: list[dict[str, Any]] = field(default_factory=list)
    eval_sets: dict[str, dict[str, Any]] = field(default_factory=dict)

    def lesson(self, lesson_id: str) -> dict[str, Any] | None:
        return self.lessons.get(lesson_id)

    def recipe(self, lesson_id: str) -> dict[str, Any] | None:
        return self.recipes.get(lesson_id)


def _read(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContentError(f"Cannot read {path}: {exc}") from exc


def _load_course(course_dir: Path) -> Course:
    data = _read(course_dir / "course.json")
    course = Course(
        course_id=data["course_id"],
        version=data["version"],
        data=data,
        lessons={lesson["lesson_id"]: lesson for lesson in data["lessons"]},
    )
    for path in sorted((course_dir / "fixtures").glob("*.json")):
        raw = _read(path)
        course.fixtures[raw["fixture_id"]] = Fixture(raw["fixture_id"], raw["version"], raw)
    for path in sorted((course_dir / "rubrics").glob("*.json")):
        raw = _read(path)
        course.rubrics[raw["rubric_id"]] = raw
    for path in sorted((course_dir / "lab-templates").glob("*.json")):
        raw = _read(path)
        course.lab_templates[raw["template_id"]] = raw
    for path in sorted((course_dir / "eval").glob("*.json")):
        raw = _read(path)
        course.eval_sets[raw["lesson_id"]] = raw
    for path in sorted((course_dir / "passages").glob("*.json")):
        raw = _read(path)
        for item in raw["passages"]:
            course.passages.append(
                {
                    "passage_id": f"{raw['lesson_id']}-{item['section_id']}",
                    "course_id": course.course_id,
                    "lesson_id": raw["lesson_id"],
                    "section_id": item["section_id"],
                    "version": raw["version"],
                    "language": raw["language"],
                    "title": item["title"],
                    "text": item["text"],
                    "source_url": f"lesson://{course.course_id}/{raw['lesson_id']}#{item['section_id']}",
                    "reviewed_at": raw.get("reviewed_at"),
                }
            )
    for lesson in data["lessons"]:
        if "recipe" in lesson:
            recipe = _read(course_dir / lesson["recipe"])
            _validate_recipe(course, recipe)
            course.recipes[lesson["lesson_id"]] = recipe
    return course


def _validate_recipe(course: Course, recipe: dict[str, Any]) -> None:
    where = f"{course.course_id}/{recipe['lesson_id']}"
    if recipe["lab_template_id"] not in course.lab_templates:
        raise ContentError(f"{where}: unknown lab template {recipe['lab_template_id']}")
    for key in ("fixture_id", "practice_fixture_id"):
        if recipe.get(key) and recipe[key] not in course.fixtures:
            raise ContentError(f"{where}: unknown fixture {recipe[key]}")
    if recipe["rubric_id"] not in course.rubrics:
        raise ContentError(f"{where}: unknown rubric {recipe['rubric_id']}")


class ContentRegistry:
    def __init__(self, courses: dict[str, Course]):
        self.courses = courses

    @classmethod
    def load(cls, content_dir: Path) -> "ContentRegistry":
        if not content_dir.is_dir():
            raise ContentError(f"Content directory not found: {content_dir}")
        courses = {}
        for course_json in sorted(content_dir.glob("*/course.json")):
            course = _load_course(course_json.parent)
            courses[course.course_id] = course
        return cls(courses)

    def course(self, course_id: str) -> Course | None:
        return self.courses.get(course_id)

    def all_passages(self) -> list[dict[str, Any]]:
        return [p for course in self.courses.values() for p in course.passages]
