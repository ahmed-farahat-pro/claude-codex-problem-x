import { useCallback, useEffect, useRef, useState } from "react";
import {
  api,
  ApiError,
  COURSE_ID,
  type ActionResult,
  type EndSummary,
  type SessionEvent,
  type SessionSnapshot,
} from "../api";
import { ErrorNote, Ltr, Time } from "../components/common";
import { LabPanel, type CheckSet } from "../components/LabPanel";
import { Transcript } from "../components/Transcript";
import { useI18n, tDynamic, type StringKey } from "../i18n";

const SESSION_KEY = "fourweeks.session";
const BUSY_POLL_MS = 1500;
const IDLE_POLL_MS = 5000;

type Busy = null | "start" | "message" | "action" | "control" | "end";
type Tab = "instructor" | "lab" | "transcript";

function storedSession(): string | null {
  try {
    return localStorage.getItem(SESSION_KEY);
  } catch {
    return null;
  }
}

function storeSession(id: string | null) {
  try {
    if (id) localStorage.setItem(SESSION_KEY, id);
    else localStorage.removeItem(SESSION_KEY);
  } catch {
    /* session id kept for this page only */
  }
}

function formatClock(seconds: number): string {
  const s = Math.max(0, Math.floor(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function checksFrom(result: ActionResult): [string, CheckSet] | null {
  const r = result.result as any;
  if (result.tool === "read_output" && result.status === "succeeded" && r?.draft?.draft_id) {
    return [r.draft.draft_id, { draft_checks: r.draft_checks, prompt_checks: r.prompt_checks }];
  }
  return null;
}

export function LiveRoom({ lessonId }: { lessonId: string }) {
  const { t } = useI18n();
  const [sessionId, setSessionId] = useState<string | null>(storedSession);
  const [snap, setSnap] = useState<SessionSnapshot | null>(null);
  const [fetchedAt, setFetchedAt] = useState(Date.now());
  const [now, setNow] = useState(Date.now());
  const [events, setEvents] = useState<SessionEvent[]>([]);
  const [busy, setBusy] = useState<Busy>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [conflict, setConflict] = useState<string | null>(null);
  const [endSummary, setEndSummary] = useState<EndSummary | null>(null);
  const [checks, setChecks] = useState<Record<string, CheckSet>>({});
  const [message, setMessage] = useState("");
  const [tab, setTab] = useState<Tab>("lab");
  const lastSeq = useRef(0);
  const flushLab = useRef<(() => Promise<boolean>) | null>(null);
  const sessionRef = useRef<string | null>(sessionId);
  sessionRef.current = sessionId;

  const refresh = useCallback(async () => {
    const id = sessionRef.current;
    if (!id) return;
    try {
      const state = await api.sessionState(id);
      if (sessionRef.current !== id) return;
      setSnap(state);
      setFetchedAt(Date.now());
      // Polls can overlap; only keep events newer than the last one already applied.
      const fresh = (await api.events(id, lastSeq.current)).filter((e) => e.seq > lastSeq.current);
      if (fresh.length && sessionRef.current === id) {
        lastSeq.current = fresh[fresh.length - 1].seq;
        setEvents((prev) => {
          const seen = new Set(prev.map((e) => e.seq));
          return [...prev, ...fresh.filter((e) => !seen.has(e.seq))];
        });
      }
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        storeSession(null);
        setSessionId(null);
        setSnap(null);
        return;
      }
      setError(err);
    }
  }, []);

  const openSession = useCallback(
    (id: string) => {
      storeSession(id);
      lastSeq.current = 0;
      setEvents([]);
      setChecks({});
      setEndSummary(null);
      setConflict(null);
      sessionRef.current = id;
      setSessionId(id);
      void refresh();
    },
    [refresh],
  );

  // Resume a stored session on load.
  useEffect(() => {
    if (sessionId) void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Poll faster while a request is in flight so thinking/acting states are visible.
  const active = !!snap && snap.state !== "ended";
  useEffect(() => {
    if (!sessionId || !active) return;
    const timer = window.setInterval(() => void refresh(), busy ? BUSY_POLL_MS : IDLE_POLL_MS);
    return () => window.clearInterval(timer);
  }, [sessionId, active, busy, refresh]);

  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  const guard = async <T,>(kind: Busy, work: () => Promise<T>): Promise<T | null> => {
    setBusy(kind);
    setError(null);
    try {
      return await work();
    } catch (err) {
      if (err instanceof ApiError && err.code === "stale_epoch") {
        setNotice(t("staleEpoch"));
      } else if (err instanceof ApiError && err.code === "session_ended") {
        setNotice(err.message);
      } else {
        setError(err);
      }
      return null;
    } finally {
      setBusy(null);
      await refresh();
    }
  };

  const start = async () => {
    setNotice(null);
    setBusy("start");
    setError(null);
    try {
      const created = await api.createSession(COURSE_ID, lessonId);
      openSession(created.session_id);
    } catch (err) {
      if (err instanceof ApiError && err.code === "session_active") setConflict(String(err.extra.session_id));
      else setError(err);
    } finally {
      setBusy(null);
    }
  };

  const endOther = async (id: string) => {
    setBusy("end");
    try {
      await api.end(id);
      setConflict(null);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(null);
    }
    await start();
  };

  const send = async (text: string) => {
    if (!snap || !text.trim()) return;
    setNotice(null);
    // The tutor reads the server-side lab, so apply any edits the learner has not applied yet.
    if (flushLab.current && !(await flushLab.current())) return;
    const result = await guard("message", async () => {
      const state = await api.sessionState(snap.session_id);
      return api.message(snap.session_id, text.trim(), state.epoch);
    });
    if (!result) return;
    setMessage("");
    if (result.status === "interrupted") setNotice(t("turnInterrupted"));
    const found = result.actions.map(checksFrom).filter((x): x is [string, CheckSet] => !!x);
    if (found.length) setChecks((c) => ({ ...c, ...Object.fromEntries(found) }));
  };

  const runTool = async (tool: string, args: Record<string, unknown> = {}): Promise<ActionResult | null> => {
    const id = sessionRef.current;
    if (!id) return null;
    setNotice(null);
    // Always read the newest epoch: a stop or control change may have happened since the last render.
    const result = await guard("action", async () => {
      const state = await api.sessionState(id);
      return api.action(id, tool, args, state.epoch);
    });
    if (!result) return null;
    if (result.status !== "succeeded") {
      setNotice(`${tool}: ${tDynamic(t, "status_", result.status)} — ${result.error_message ?? result.error_category ?? ""}`);
      return result;
    }
    const found = checksFrom(result);
    if (found) setChecks((c) => ({ ...c, [found[0]]: found[1] }));
    const draftId = (result.result as any)?.draft?.draft_id;
    if ((tool === "generate_draft" || tool === "revise_draft") && draftId) {
      // Observe the new draft right away so its checks are visible.
      const read = await guard("action", async () => {
        const state = await api.sessionState(id);
        return api.action(id, "read_output", { draft_id: draftId }, state.epoch);
      });
      const more = read && checksFrom(read);
      if (more) setChecks((c) => ({ ...c, [more[0]]: more[1] }));
    }
    return result;
  };

  const stop = async () => {
    if (!snap) return;
    try {
      await api.stop(snap.session_id);
      setNotice(t("stopped"));
    } catch (err) {
      setError(err);
    }
    await refresh();
  };

  const control = async (holder: "tutor" | "learner") => {
    if (!snap) return;
    const next = await guard("control", () => api.control(snap.session_id, holder));
    if (next) setSnap(next);
  };

  const end = async () => {
    if (!snap || !window.confirm(t("endConfirm"))) return;
    const summary = await guard("end", () => api.end(snap.session_id));
    if (summary) {
      setEndSummary(summary);
      storeSession(null);
    }
  };

  const newSession = () => {
    storeSession(null);
    sessionRef.current = null;
    setSessionId(null);
    setSnap(null);
    setEvents([]);
    setEndSummary(null);
    setNotice(null);
  };

  // ---------------------------------------------------------------- render

  if (!sessionId || !snap) {
    return (
      <div className="page">
        <header className="page-head">
          <h1>{t("liveTitle")}</h1>
          <p className="muted">{t("liveSubtitle")}</p>
        </header>
        <div className="card start-card">
          <p>{t("sessionIntro")}</p>
          {conflict ? (
            <div className="notice" role="status">
              <p>
                {t("sessionActiveNotice")} <Ltr>{conflict}</Ltr>
              </p>
              <div className="row wrap">
                <button type="button" className="btn btn-primary" onClick={() => openSession(conflict)}>
                  {t("resumeSession")}
                </button>
                <button type="button" className="btn" disabled={!!busy} onClick={() => void endOther(conflict)}>
                  {t("endSessionInstead")}
                </button>
              </div>
            </div>
          ) : (
            <button type="button" className="btn btn-primary btn-large" disabled={!!busy || (!!sessionId && !snap)} onClick={() => void start()}>
              {busy === "start" ? t("starting") : t("startSession")}
            </button>
          )}
          <ErrorNote error={error} />
        </div>
      </div>
    );
  }

  const ended = snap.state === "ended";
  const remaining = ended ? 0 : snap.remaining_seconds - (now - fetchedAt) / 1000;
  const learnerControl = snap.control === "learner";
  const turnRunning = busy === "message";
  const stateText = tDynamic(t, "state_", snap.state);
  const lastAnswer = [...events].reverse().find((e) => e.type === "answer");

  return (
    <div className="page live">
      <header className="page-head live-head">
        <div>
          <h1>{t("liveTitle")}</h1>
          <p className="muted">{t("liveSubtitle")}</p>
        </div>
        <div className="live-meta">
          <span className={`tag ${learnerControl ? "tag-ok" : ""}`}>{learnerControl ? t("controlLearner") : t("controlTutor")}</span>
          <span className="tag">
            {t("remaining")}: <Ltr>{formatClock(remaining)}</Ltr>
          </span>
          <span className="tag muted">
            <Ltr>
              {snap.lesson_id} · epoch {snap.epoch}
            </Ltr>
          </span>
        </div>
      </header>

      {/* Screen-reader announcements for state changes and the newest answer. */}
      <div className="sr-only" aria-live="polite">
        {t("liveAnnounce", { state: stateText })}
      </div>
      <div className="sr-only" aria-live="polite">
        {lastAnswer?.payload.text ?? ""}
      </div>

      {notice && (
        <div className="notice" role="status">
          {notice}
          <button type="button" className="btn btn-small btn-ghost" onClick={() => setNotice(null)}>
            {t("close")}
          </button>
        </div>
      )}
      <ErrorNote error={error} onRetry={() => void refresh()} />

      {ended && (
        <EndCard
          summary={endSummary}
          snap={snap}
          onNew={newSession}
        />
      )}

      <div className="tabs" role="tablist" aria-label={t("liveTitle")}>
        {(["instructor", "lab", "transcript"] as Tab[]).map((name) => (
          <button
            key={name}
            type="button"
            role="tab"
            aria-selected={tab === name}
            className={`tab ${tab === name ? "tab-active" : ""}`}
            onClick={() => setTab(name)}
          >
            {t(`tab${name[0].toUpperCase()}${name.slice(1)}` as StringKey)}
          </button>
        ))}
      </div>

      <div className={`live-grid tab-${tab}`}>
        <section className="panel instructor" data-panel="instructor" aria-labelledby="instructor-title">
          <h2 id="instructor-title" className="panel-title">
            {t("instructorTitle")}
          </h2>
          <div className={`avatar avatar-${snap.state}`} role="img" aria-label={t("instructorPlaceholder")}>
            <div className="avatar-shape" aria-hidden="true">
              <span className="avatar-head" />
              <span className="avatar-body" />
            </div>
          </div>
          <p className="small muted">{t("instructorPlaceholder")}</p>
          <p className="state-line">
            <span className="muted">{t("stateLabel")}:</span> <strong className={`state state-${snap.state}`}>{stateText}</strong>
          </p>
          <p className="small muted">{t("instructorNote")}</p>
        </section>

        <LabPanel
          lab={snap.lab}
          editable={learnerControl}
          busy={!!busy}
          ended={ended}
          checks={checks}
          runTool={runTool}
          flushRef={flushLab}
        />

        {!ended && (
          <div className="controls" role="group" aria-label={t("liveTitle")}>
            <button type="button" className="btn btn-stop" onClick={() => void stop()}>
              ■ {t("stop")}
            </button>
            {learnerControl ? (
              <button type="button" className="btn btn-control" disabled={turnRunning || busy === "control"} onClick={() => void control("tutor")}>
                {t("handBack")}
              </button>
            ) : (
              <button type="button" className="btn btn-control" disabled={busy === "control"} onClick={() => void control("learner")}>
                {t("takeControl")}
              </button>
            )}
            <button type="button" className="btn btn-end" disabled={!!busy} onClick={() => void end()}>
              {t("endSession")}
            </button>
          </div>
        )}

        <section className="panel transcript-panel" data-panel="transcript" aria-labelledby="transcript-title">
          <h2 id="transcript-title" className="panel-title">
            {t("transcript")}
          </h2>
          <p className="small muted">{t("transcriptNote")}</p>
          {!ended && (
            <>
              <form
                className="composer"
                onSubmit={(e) => {
                  e.preventDefault();
                  void send(message);
                }}
              >
                <div className="field">
                  <label className="field-label" htmlFor="tutor-message">
                    {t("messageLabel")}
                  </label>
                  <textarea
                    id="tutor-message"
                    dir="auto"
                    rows={2}
                    value={message}
                    maxLength={2000}
                    placeholder={t("messagePlaceholder")}
                    disabled={ended}
                    onChange={(e) => setMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        void send(message);
                      }
                    }}
                  />
                </div>
                <button type="submit" className="btn btn-primary" disabled={ended || !!busy || !message.trim()}>
                  {turnRunning ? stateText : t("send")}
                </button>
              </form>
              <div className="suggestions" aria-label={t("suggestions")}>
                {(["sugDemo", "sugWeak", "sugQuestion", "sugShorten"] as StringKey[]).map((key) => (
                  <button key={key} type="button" className="chip" disabled={ended || !!busy} onClick={() => void send(t(key))}>
                    {t(key)}
                  </button>
                ))}
              </div>
              <p className="small muted">{t("pushToTalkLater")}</p>
            </>
          )}
          <Transcript events={events} />
        </section>
      </div>
    </div>
  );
}

function EndCard({ summary, snap, onNew }: { summary: EndSummary | null; snap: SessionSnapshot; onNew: () => void }) {
  const { t } = useI18n();
  const usage = summary?.usage ?? { ...snap.usage, allowance_remaining_seconds: null as number | null };
  return (
    <section className="card end-card" aria-labelledby="end-title">
      <h2 id="end-title" className="card-title">
        {t("sessionEnded")}
      </h2>
      <dl className="facts facts-inline">
        <dt>{t("endReason")}</dt>
        <dd>
          <Ltr>{summary?.end_reason ?? snap.end_reason}</Ltr>
        </dd>
        <dt>{t("duration")}</dt>
        <dd>{t("seconds", { n: usage.duration_seconds ?? 0 })}</dd>
        <dt>{t("turns")}</dt>
        <dd>{usage.turns}</dd>
        <dt>{t("actions")}</dt>
        <dd>{usage.actions}</dd>
        <dt>{t("tokens")}</dt>
        <dd>
          <Ltr>
            {usage.model_input_tokens} / {usage.model_output_tokens}
          </Ltr>
        </dd>
        {usage.allowance_remaining_seconds != null && (
          <>
            <dt>{t("allowanceLeft")}</dt>
            <dd>{t("minutesValue", { min: Math.floor(usage.allowance_remaining_seconds / 60) })}</dd>
          </>
        )}
      </dl>
      {summary && (
        <>
          <h3>{t("memoryWritten")}</h3>
          {summary.memory_written.length === 0 ? (
            <p className="muted">{t("noMemoryWritten")}</p>
          ) : (
            <ul className="plain-list">
              {summary.memory_written.map((m) => (
                <li key={m.memory_id}>
                  <strong>{tDynamic(t, "mem_", m.kind)}:</strong> <span dir="auto">{m.text}</span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
      <p className="small muted">
        <Time iso={snap.ended_at} />
      </p>
      <button type="button" className="btn btn-primary" onClick={onNew}>
        {t("newSession")}
      </button>
    </section>
  );
}
