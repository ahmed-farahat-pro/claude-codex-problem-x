import { useState } from "react";
import { api, type Submission } from "../api";
import { DraftChecksView } from "../components/Checks";
import { Card, ErrorNote, Loading, Ltr, Mark, Time } from "../components/common";
import { navigate, useLoad } from "../context";
import { pick, tDynamic, useI18n } from "../i18n";

export function MyWork({ artifactId }: { artifactId: string | null }) {
  const { t } = useI18n();
  const [list, error, reload] = useLoad(() => api.artifacts(), []);
  if (error) return <ErrorNote error={error} onRetry={reload} />;
  if (!list) return <Loading />;
  return (
    <div className="page">
      <header className="page-head">
        <h1>{t("workTitle")}</h1>
      </header>
      <div className="work-layout">
        <Card title={t("artifactList")} className="work-list">
          {list.length === 0 ? (
            <p className="muted">{t("noWorkYet")}</p>
          ) : (
            <ul className="plain-list">
              {list.map((a) => (
                <li key={a.artifact_id}>
                  <button
                    type="button"
                    className={`list-button ${a.artifact_id === artifactId ? "active" : ""}`}
                    aria-current={a.artifact_id === artifactId ? "true" : undefined}
                    onClick={() => navigate("work", a.artifact_id)}
                  >
                    <span dir="auto">{a.title}</span>
                    <span className="muted small">
                      <Ltr>{a.lesson_id}</Ltr> · <Time iso={a.created_at} />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </Card>
        {artifactId ? <ArtifactView key={artifactId} artifactId={artifactId} /> : <p className="muted">{t("selectArtifact")}</p>}
      </div>
    </div>
  );
}

function ArtifactView({ artifactId }: { artifactId: string }) {
  const { t } = useI18n();
  const [data, error, reload] = useLoad(() => Promise.all([api.artifact(artifactId), api.submissions()]), [artifactId]);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<unknown>(null);
  if (error) return <ErrorNote error={error} onRetry={reload} />;
  if (!data) return <Loading />;
  const [artifact, allSubmissions] = data;
  const submissions = allSubmissions.filter((s) => s.artifact_id === artifactId);
  const c = artifact.content;

  const doExport = async () => {
    setActionError(null);
    try {
      const blob = await api.exportArtifact(artifactId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${artifactId}.md`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setActionError(err);
    }
  };

  const submit = async () => {
    setBusy(true);
    setActionError(null);
    try {
      await api.submit(artifactId);
      reload();
    } catch (err) {
      setActionError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="work-detail">
      <Card title={artifact.title}>
        <div className="row wrap">
          <button type="button" className="btn" onClick={() => void doExport()}>
            {t("export")}
          </button>
          <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void submit()}>
            {t("submitChecks")}
          </button>
        </div>
        <ErrorNote error={actionError} />
        <h3>{t("promptUsed")}</h3>
        <div className="draft-text" dir="auto">
          {c.prompt}
        </div>
        <h3>{t("draftText")}</h3>
        <div className="draft-text" dir="auto">
          {c.draft_text}
        </div>
        <DraftChecksView draft={c.checks.draft_checks} prompt={c.checks.prompt_checks} />
        <h3>{t("metadata")}</h3>
        <dl className="facts facts-inline">
          <dt>{t("model")}</dt>
          <dd>
            <Ltr>{c.model}</Ltr>
          </dd>
          <dt>{t("fixture")}</dt>
          <dd>
            <Ltr>
              {c.fixture_id} v{c.fixture_version}
            </Ltr>
          </dd>
          <dt>{t("savedAt")}</dt>
          <dd>
            <Time iso={artifact.created_at} />
          </dd>
          <dt>id</dt>
          <dd>
            <Ltr>{artifact.artifact_id}</Ltr>
          </dd>
          <dt>sha256</dt>
          <dd>
            <Ltr>{artifact.content_hash.slice(0, 16)}…</Ltr>
          </dd>
        </dl>
      </Card>
      {submissions.length > 0 && (
        <Card title={t("previousSubmissions")}>
          {submissions.map((s) => (
            <SubmissionView key={s.submission_id} submission={s} onChange={reload} />
          ))}
        </Card>
      )}
    </div>
  );
}

function SubmissionView({ submission, onChange }: { submission: Submission; onChange: () => void }) {
  const { t, lang } = useI18n();
  const [reason, setReason] = useState("");
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const appeal = async () => {
    setError(null);
    try {
      await api.appeal(submission.submission_id, reason.trim());
      setOpen(false);
      onChange();
    } catch (err) {
      setError(err);
    }
  };
  return (
    <article className="submission">
      <h3>
        {t("submissionResult")}: {tDynamic(t, "sub_", submission.status)}{" "}
        <span className="tag">{tDynamic(t, "review_", submission.review_status)}</span>
      </h3>
      <p className="muted small">
        <Time iso={submission.created_at} /> · <Ltr>{submission.rubric_id} v{submission.rubric_version}</Ltr>
      </p>
      <ul className="check-list">
        {submission.results.map((r) => (
          <li key={r.criterion_id}>
            <Mark ok={r.passed} label={pick(r.label, lang)} />{" "}
            <span className="muted small" lang="en" dir="ltr">
              ({r.evidence})
            </span>
          </li>
        ))}
      </ul>
      {submission.appeal_reason && (
        <p className="muted" dir="auto">
          «{submission.appeal_reason}»
        </p>
      )}
      {submission.review_status !== "appeal_requested" &&
        (open ? (
          <div className="appeal">
            <label className="field">
              <span className="field-label">{t("appealReason")}</span>
              <textarea dir="auto" rows={2} value={reason} maxLength={1000} onChange={(e) => setReason(e.target.value)} />
            </label>
            <button type="button" className="btn" disabled={reason.trim().length < 3} onClick={() => void appeal()}>
              {t("sendAppeal")}
            </button>
          </div>
        ) : (
          <button type="button" className="btn btn-small btn-ghost" onClick={() => setOpen(true)}>
            {t("appeal")}
          </button>
        ))}
      <ErrorNote error={error} />
    </article>
  );
}
