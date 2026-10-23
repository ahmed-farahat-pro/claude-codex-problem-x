import { useEffect, useId, useRef, useState, type MutableRefObject } from "react";
import type { ActionResult, Draft, DraftChecks, LabView, PromptChecks } from "../api";
import { useI18n, type StringKey } from "../i18n";
import { DraftChecksView } from "./Checks";
import { Ltr, Time } from "./common";

export type CheckSet = { draft_checks: DraftChecks; prompt_checks: PromptChecks };
type RunTool = (tool: string, args?: Record<string, unknown>) => Promise<ActionResult | null>;

const FIELDS: { name: "brief" | "audience" | "tone" | "prompt"; tool: string; label: StringKey; rows: number }[] = [
  { name: "brief", tool: "set_brief", label: "fieldBrief", rows: 3 },
  { name: "audience", tool: "set_audience", label: "fieldAudience", rows: 1 },
  { name: "tone", tool: "set_tone", label: "fieldTone", rows: 1 },
  { name: "prompt", tool: "set_prompt", label: "fieldPrompt", rows: 6 },
];
type FieldName = (typeof FIELDS)[number]["name"];

export function LabPanel({
  lab,
  editable,
  busy,
  ended,
  checks,
  runTool,
  flushRef,
}: {
  lab: LabView;
  editable: boolean;
  busy: boolean;
  ended: boolean;
  checks: Record<string, CheckSet>;
  runTool: RunTool;
  /** Lets the room apply pending field edits before it sends a message. */
  flushRef: MutableRefObject<(() => Promise<boolean>) | null>;
}) {
  const { t } = useI18n();
  const uid = useId();
  const server: Record<FieldName, string> = {
    brief: lab.brief ?? "",
    audience: lab.audience ?? "",
    tone: lab.tone ?? "",
    prompt: lab.prompt ?? "",
  };
  const [values, setValues] = useState<Record<FieldName, string>>(server);
  const [dirty, setDirty] = useState<Set<FieldName>>(new Set());
  const [instruction, setInstruction] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const flushing = useRef<Promise<boolean> | null>(null);
  const latest = useRef({ values, dirty, server });
  latest.current = { values, dirty, server };

  // Follow the server for every field the learner is not editing.
  useEffect(() => {
    setValues((current) => {
      const next = { ...current };
      for (const f of FIELDS) if (!editable || !latest.current.dirty.has(f.name)) next[f.name] = server[f.name];
      return next;
    });
    if (!editable) setDirty(new Set());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [lab.state_version, editable]);

  const drafts: Draft[] = lab.drafts ?? [];
  const current = drafts.find((d) => d.draft_id === selected) ?? drafts[drafts.length - 1];
  useEffect(() => {
    if (drafts.length) setSelected(drafts[drafts.length - 1].draft_id);
  }, [drafts.length]); // newest draft becomes the selection when one is added

  /** Apply every edited field, in order. Resolves false if any edit failed. */
  const flush = (): Promise<boolean> => {
    flushing.current ??= (async () => {
      let ok = true;
      for (const f of FIELDS) {
        const { values: v, dirty: d, server: s } = latest.current;
        if (!d.has(f.name)) continue;
        if (v[f.name] === s[f.name]) {
          setDirty((prev) => new Set([...prev].filter((x) => x !== f.name)));
          continue;
        }
        const result = await runTool(f.tool, { text: v[f.name] });
        if (result?.status === "succeeded") {
          setDirty((prev) => new Set([...prev].filter((x) => x !== f.name)));
        } else {
          ok = false;
        }
      }
      return ok;
    })().finally(() => {
      flushing.current = null;
    });
    return flushing.current;
  };

  flushRef.current = flush;

  // Buttons are not disabled while a request is in flight: a blur-triggered save would otherwise disable a
  // button between mousedown and click and swallow the click. Every action is epoch-checked on the server.
  const canEdit = editable && !ended;
  const ready = lab.status === "ready";

  const generate = async () => {
    if (await flush()) await runTool("generate_draft");
  };
  const revise = async () => {
    if (!instruction.trim() || !current) return;
    if (!(await flush())) return;
    const result = await runTool("revise_draft", { instruction: instruction.trim(), draft_id: current.draft_id });
    if (result?.status === "succeeded") setInstruction("");
  };
  const reset = async () => {
    if (window.confirm(t("resetConfirm"))) {
      setDirty(new Set());
      await runTool("reset_lab");
    }
  };

  if (!ready) {
    return (
      <section className="panel lab" data-panel="lab" aria-labelledby="lab-title">
        <h2 id="lab-title" className="panel-title">
          {t("labTitle")}
        </h2>
        <p className="placeholder">
          {lab.status === "disposed" ? (
            <>
              {t("labDisposed")} <a href="#/work">{t("navWork")}</a>
            </>
          ) : (
            <Ltr>lab: {lab.status}</Ltr>
          )}
        </p>
      </section>
    );
  }

  return (
    <section className="panel lab" data-panel="lab" aria-labelledby="lab-title" aria-busy={busy}>
      <div className="panel-head">
        <h2 id="lab-title" className="panel-title">
          {t("labTitle")} <span className="muted">/ {t("labScreen")}</span>
        </h2>
        <span className="muted small">
          {t("labVersion")} <Ltr>v{lab.state_version}</Ltr> · <Ltr>{lab.fixture_id}</Ltr>
        </span>
      </div>
      <p className="business">
        <span className="muted">{t("businessName")}:</span> <strong dir="auto">{lab.business_name}</strong>
      </p>
      {!editable && !ended && <p className="hint">{t("readOnlyHint")}</p>}

      <div className="fields">
        {FIELDS.map((f) => (
          <div key={f.name} className={`field ${dirty.has(f.name) ? "field-dirty" : ""}`}>
            <label className="field-label" htmlFor={`${uid}-${f.name}`}>
              {t(f.label)}
            </label>
            <textarea
              id={`${uid}-${f.name}`}
              dir="auto"
              rows={f.rows}
              value={values[f.name]}
              readOnly={!canEdit}
              aria-readonly={!canEdit}
              onChange={(e) => {
                const text = e.target.value;
                setValues((v) => ({ ...v, [f.name]: text }));
                setDirty((d) => new Set(d).add(f.name));
              }}
              onBlur={() => {
                if (canEdit && latest.current.dirty.has(f.name)) void flush();
              }}
            />
          </div>
        ))}
      </div>

      <div className="row wrap lab-actions">
        <button type="button" className="btn" disabled={!canEdit || dirty.size === 0} onClick={() => void flush()}>
          {t("apply")}
        </button>
        <button type="button" className="btn btn-primary" disabled={!canEdit || !values.prompt.trim()} onClick={() => void generate()}>
          {t("generateDraft")}
        </button>
        <button type="button" className="btn btn-danger-soft" disabled={!canEdit} onClick={() => void reset()}>
          {t("resetLab")}
        </button>
      </div>

      <h3 className="drafts-title">{t("drafts")}</h3>
      {drafts.length === 0 ? (
        <p className="muted">{t("noDrafts")}</p>
      ) : (
        <>
          <div className="draft-tabs" role="group" aria-label={t("drafts")}>
            {drafts.map((d) => (
              <button
                key={d.draft_id}
                type="button"
                className={`chip ${current?.draft_id === d.draft_id ? "chip-active" : ""}`}
                aria-pressed={current?.draft_id === d.draft_id}
                onClick={() => setSelected(d.draft_id)}
              >
                {t("draftN", { n: d.number })} · {d.created_by === "learner" ? t("byLearner") : t("byTutor")}
              </button>
            ))}
          </div>
          {current && (
            <article className="draft">
              <p className="draft-meta muted small">
                {t("model")}: <Ltr>{current.model}</Ltr> · <Time iso={current.created_at} />
                {current.instruction && (
                  <>
                    {" "}
                    · {t("reviseInstruction")}: «{current.instruction}»
                  </>
                )}
              </p>
              <div className="draft-text" dir="auto">
                {current.text}
              </div>
              {checks[current.draft_id] ? (
                <DraftChecksView draft={checks[current.draft_id].draft_checks} prompt={checks[current.draft_id].prompt_checks} />
              ) : (
                <button
                  type="button"
                  className="btn btn-small"
                  disabled={ended}
                  onClick={() => void runTool("read_output", { draft_id: current.draft_id })}
                >
                  {t("runChecks")}
                </button>
              )}
              <div className="row wrap">
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={ended}
                  onClick={() => void runTool("save_draft", { draft_id: current.draft_id })}
                >
                  {t("saveWork")}
                </button>
              </div>
              <div className="revise">
                <div className="field">
                  <label className="field-label" htmlFor={`${uid}-instruction`}>
                    {t("reviseInstruction")}
                  </label>
                  <input
                    id={`${uid}-instruction`}
                    dir="auto"
                    type="text"
                    value={instruction}
                    placeholder={t("revisePlaceholder")}
                    readOnly={!canEdit}
                    onChange={(e) => setInstruction(e.target.value)}
                    maxLength={500}
                  />
                </div>
                <button type="button" className="btn" disabled={!canEdit || !instruction.trim()} onClick={() => void revise()}>
                  {t("revise")}
                </button>
              </div>
            </article>
          )}
        </>
      )}
    </section>
  );
}
