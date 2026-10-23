# Course content packages

Each course is a folder of small versioned files (PRD section 19). The backend loads them on startup and
validates references between them.

```
ai-for-everyone/
  course.json                 course brief, release manifest, 4 weeks, 20 lessons
  lessons/L03.recipe.json     lesson recipe: fixture, allowed tools, rubric, timeline, next practice
  lab-templates/*.json        lab template: version, fixtures, limits, network and credentials policy
  fixtures/*.json             synthetic business briefs and template-draft sentences
  rubrics/*.json              prompt-checklist (rule-based) and capstone (weighted, needs review)
  passages/L03.ar.json        approved Arabic passages used for retrieval and source links
  eval/L03-questions.json     10-question grounding set (answerable, vague, outside the course)
```

Status: only L03 ("Write a clear prompt", the eight-minute demo lesson) has a runnable recipe. The L03 passages
are drafts (`review_status: draft`, `reviewed_at: null`) and must be reviewed by the founder before learners
rely on them. Lesson outcomes for the other 19 lessons are copied in English from PRD v2.

To add a lesson lab: write `lessons/LXX.recipe.json`, point the lesson in `course.json` at it with `"recipe"`,
add its fixtures, rubric and passages, then run `cd backend && .venv/bin/pytest`.
