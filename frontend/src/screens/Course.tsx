import { useEffect, useState } from "react";
import { api, COURSE_ID, type Progress } from "../api";
import { Card, ErrorNote, Loading, Ltr } from "../components/common";
import { navigate, useLoad } from "../context";
import { pick, useI18n } from "../i18n";

function statusLabel(t: ReturnType<typeof useI18n>["t"], status: Progress["status"] | undefined) {
  if (status === "completed") return t("statusCompleted");
  if (status === "started") return t("statusStarted");
  return t("statusNotStarted");
}

export function CourseScreen({ lessonId }: { lessonId: string | null }) {
  return lessonId ? <LessonDetailView lessonId={lessonId} /> : <Outline />;
}

function Outline() {
  const { t, lang } = useI18n();
  const [data, error, reload] = useLoad(() => Promise.all([api.course(COURSE_ID), api.progress()]), []);
  if (error) return <ErrorNote error={error} onRetry={reload} />;
  if (!data) return <Loading />;
  const [course, progress] = data;
  const byLesson = new Map(progress.map((p) => [p.lesson_id, p.status]));
  return (
    <div className="page">
      <header className="page-head">
        <h1>{t("courseTitle")}</h1>
        <p className="muted">
          {pick(course.title, lang)} · {t("version")} <Ltr>{course.version}</Ltr>
        </p>
      </header>
      <div className="outline">
        {course.weeks.map((week) => (
          <Card key={week.week} title={`${t("weekN", { n: week.week })}: ${pick(week.title, lang)}`}>
            <ol className="lesson-list">
              {week.lessons.map((lesson) => (
                <li key={lesson.lesson_id}>
                  <a href={`#/course/${lesson.lesson_id}`} className="lesson-link">
                    <Ltr>{lesson.lesson_id}</Ltr>
                    <span className="lesson-title">{pick(lesson.title, lang)}</span>
                  </a>
                  <span className="lesson-tags">
                    <span className={`tag ${lesson.has_lab ? "tag-ok" : ""}`}>
                      {lesson.has_lab ? t("hasLab") : t("noLabYet")}
                    </span>
                    <span className="tag">{statusLabel(t, byLesson.get(lesson.lesson_id))}</span>
                  </span>
                </li>
              ))}
            </ol>
          </Card>
        ))}
      </div>
    </div>
  );
}

const SPEEDS = [0.75, 1, 1.25, 1.5, 2];

function LocalVideo() {
  const { t } = useI18n();
  const [url, setUrl] = useState<string | null>(null);
  const [speed, setSpeed] = useState(1);
  const [video, setVideo] = useState<HTMLVideoElement | null>(null);

  useEffect(() => () => {
    if (url) URL.revokeObjectURL(url);
  }, [url]);
  useEffect(() => {
    if (!video) return;
    // A new source resets playbackRate to defaultPlaybackRate, so set both.
    video.defaultPlaybackRate = speed;
    video.playbackRate = speed;
  }, [video, speed, url]);

  return (
    <Card title={t("recordedLesson")}>
      <p className="muted small">{t("localVideoNote")}</p>
      <div className="row">
        <label className="file-label">
          {t("chooseVideo")}
          <input
            type="file"
            accept="video/mp4"
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) setUrl(URL.createObjectURL(file));
            }}
          />
        </label>
        <label>
          {t("playbackSpeed")}{" "}
          <select value={speed} onChange={(e) => setSpeed(Number(e.target.value))}>
            {SPEEDS.map((s) => (
              <option key={s} value={s}>
                {s}×
              </option>
            ))}
          </select>
        </label>
      </div>
      {url ? (
        <video ref={setVideo} src={url} controls className="video" />
      ) : (
        <p className="placeholder">{t("noVideo")}</p>
      )}
    </Card>
  );
}

function LessonDetailView({ lessonId }: { lessonId: string }) {
  const { t, lang } = useI18n();
  const [data, error, reload] = useLoad(
    () => Promise.all([api.lesson(COURSE_ID, lessonId), api.course(COURSE_ID), api.progress()]),
    [lessonId],
  );
  const [busy, setBusy] = useState(false);
  const [progressError, setProgressError] = useState<unknown>(null);
  if (error) return <ErrorNote error={error} onRetry={reload} />;
  if (!data) return <Loading />;
  const [lesson, course, progress] = data;
  const status = progress.find((p) => p.lesson_id === lessonId)?.status;
  const hasLab = course.weeks.flatMap((w) => w.lessons).find((l) => l.lesson_id === lessonId)?.has_lab;

  const mark = async (next: "started" | "completed") => {
    setBusy(true);
    setProgressError(null);
    try {
      await api.setProgress(COURSE_ID, lessonId, next);
      reload();
    } catch (err) {
      setProgressError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="page">
      <p>
        <a href="#/course">← {t("backToCourse")}</a>
      </p>
      <header className="page-head">
        <h1>
          <Ltr>{lesson.lesson_id}</Ltr> {pick(lesson.title, lang)}
        </h1>
        <p className="muted">
          {t("weekN", { n: lesson.week })} · {t("lessonVersion")} <Ltr>{lesson.version}</Ltr> ·{" "}
          {lesson.reviewed_at ? t("reviewedOn", { date: lesson.reviewed_at }) : <span className="tag tag-warn">{t("notReviewed")}</span>}{" "}
          · {statusLabel(t, status)}
        </p>
      </header>

      <div className="row wrap">
        <button type="button" className="btn" disabled={busy} onClick={() => void mark("started")}>
          {t("markStarted")}
        </button>
        <button type="button" className="btn" disabled={busy} onClick={() => void mark("completed")}>
          {t("markCompleted")}
        </button>
        {hasLab && (
          <button type="button" className="btn btn-primary" onClick={() => navigate("live", lessonId)}>
            {t("tryInLiveRoom")}
          </button>
        )}
      </div>
      <ErrorNote error={progressError} />

      <div className="grid-2">
        <Card title={t("lessonOutcome")}>
          {lesson.recipe && <p className="lead">{pick(lesson.recipe.outcome, lang)}</p>}
          <p className="small muted">{t("englishSourceNote")}</p>
          <dl className="facts" lang="en" dir="ltr">
            <dt>Outcome</dt>
            <dd>{lesson.outcome}</dd>
            <dt>Lab</dt>
            <dd>{lesson.lab}</dd>
            <dt>Deliverable</dt>
            <dd>{lesson.deliverable}</dd>
            <dt>Acceptance</dt>
            <dd>{lesson.acceptance}</dd>
          </dl>
        </Card>
        <LocalVideo />
      </div>

      {lesson.recipe && (
        <>
          <Card title={t("lessonPlan")}>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th scope="col">{t("timelineTime")}</th>
                    <th scope="col">{t("timelineOnScreen")}</th>
                    <th scope="col">{t("timelineEvidence")}</th>
                  </tr>
                </thead>
                <tbody>
                  {lesson.recipe.timeline.map((row) => (
                    <tr key={row.start}>
                      <td>
                        <Ltr>
                          {row.start}–{row.end}
                        </Ltr>
                      </td>
                      <td lang="en" dir="ltr">
                        {row.on_screen}
                      </td>
                      <td lang="en" dir="ltr">
                        {row.evidence}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
          <Card title={t("rubric")}>
            <p className="small muted">{t("rubricNote")}</p>
            <ul className="plain-list">
              {lesson.recipe.rubric.criteria.map((c) => (
                <li key={c.criterion_id}>{pick(c.label, lang)}</li>
              ))}
            </ul>
          </Card>
        </>
      )}

      {lesson.sections.length > 0 && (
        <Card title={t("lessonSections")}>
          <ol className="sections" lang="ar" dir="rtl">
            {lesson.sections.map((s) => (
              <li key={s.passage_id} id={s.section_id}>
                <h3>
                  {s.title} <span className="small muted"><Ltr>#{s.section_id}</Ltr></span>
                </h3>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
        </Card>
      )}
    </div>
  );
}
