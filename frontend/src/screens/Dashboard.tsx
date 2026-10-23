import { api, COURSE_ID } from "../api";
import { Card, ErrorNote, Loading, Ltr, Time } from "../components/common";
import { navigate, useApp, useLoad } from "../context";
import { pick, useI18n } from "../i18n";

export function Dashboard() {
  const { t, lang } = useI18n();
  const { me } = useApp();
  const [data, error, reload] = useLoad(
    () => Promise.all([api.course(COURSE_ID), api.progress(), api.enrollments(), api.artifacts()]),
    [],
  );
  if (error) return <ErrorNote error={error} onRetry={reload} />;
  if (!data) return <Loading />;
  const [course, progress, enrollments, artifacts] = data;

  const completed = new Set(progress.filter((p) => p.status === "completed").map((p) => p.lesson_id));
  const lessons = course.weeks.flatMap((w) => w.lessons);
  const next = lessons.find((l) => !completed.has(l.lesson_id)) ?? lessons[0];
  const enrollment = enrollments.find((e) => e.course_id === COURSE_ID);
  const minutes = enrollment ? Math.floor(enrollment.live_remaining_seconds / 60) : 0;

  return (
    <div className="page">
      <header className="page-head">
        <h1>{pick(course.title, lang)}</h1>
        <p className="muted">{t("welcome", { name: me.display_name })}</p>
      </header>

      <div className="grid-3">
        <Card title={t("courseProgress")}>
          <p className="stat">
            {t("lessonsCompleted", { done: completed.size, total: lessons.length })}
          </p>
          <progress max={lessons.length} value={completed.size} aria-label={t("courseProgress")} />
          {next && (
            <button type="button" className="btn btn-primary" onClick={() => navigate("course", next.lesson_id)}>
              {t("continueLesson")}: <Ltr>{next.lesson_id}</Ltr> {pick(next.title, lang)}
            </button>
          )}
        </Card>
        <Card title={t("liveMinutes")}>
          <p className="stat">{t("minutesValue", { min: minutes })}</p>
          <button type="button" className="btn" onClick={() => navigate("live", "L03")}>
            {t("openLiveRoom")}
          </button>
        </Card>
        <Card title={t("recentWork")}>
          {artifacts.length === 0 ? (
            <p className="muted">{t("noWorkYet")}</p>
          ) : (
            <ul className="plain-list">
              {artifacts.slice(0, 3).map((a) => (
                <li key={a.artifact_id}>
                  <a href={`#/work/${encodeURIComponent(a.artifact_id)}`} dir="auto">
                    {a.title}
                  </a>{" "}
                  <span className="muted small">
                    <Time iso={a.created_at} />
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <Card title={t("weeklyOutcomes")}>
        <ol className="weeks">
          {course.weeks.map((week) => {
            const done = week.lessons.filter((l) => completed.has(l.lesson_id)).length;
            return (
              <li key={week.week} className="week">
                <h3>
                  {t("weekN", { n: week.week })}: {pick(week.title, lang)}
                </h3>
                <p className="muted small">{t("portfolioResult")}</p>
                <p lang="en" dir="ltr" className="en-source">
                  {week.portfolio_result}
                </p>
                <p className="small muted">{t("lessonsCompleted", { done, total: week.lessons.length })}</p>
              </li>
            );
          })}
        </ol>
      </Card>

      {course.release.known_limitations.length > 0 && (
        <Card title={t("knownLimitations")}>
          <ul lang="en" dir="ltr" className="en-source">
            {course.release.known_limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  );
}
