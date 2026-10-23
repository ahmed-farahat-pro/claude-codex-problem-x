import type { SessionEvent } from "../api";
import { useI18n, tDynamic } from "../i18n";
import { Ltr, Mark } from "./common";

type ActionPayload = {
  action_id: string;
  tool: string;
  actor: "learner" | "tutor";
  status: string;
  observed_state_version: number | null;
  error_category: string | null;
  duration_ms: number;
};

type AnswerPayload = {
  kind: string;
  text: string | null;
  sources: { passage_id: string; lesson_id: string; section_id: string; title: string }[];
  error_category: string | null;
};

type Item =
  | { kind: "turn"; key: string; text: string; actions: ActionPayload[]; answer?: AnswerPayload; interrupted?: boolean }
  | { kind: "system"; key: string; text: string }
  | { kind: "learner_action"; key: string; action: ActionPayload };

export function buildTranscript(events: SessionEvent[], t: ReturnType<typeof useI18n>["t"]): Item[] {
  const items: Item[] = [];
  const turns = new Map<string, Extract<Item, { kind: "turn" }>>();
  for (const ev of events) {
    const turn = ev.turn_id ? turns.get(ev.turn_id) : undefined;
    switch (ev.type) {
      case "turn.started": {
        const item = { kind: "turn" as const, key: `t-${ev.turn_id}`, text: String(ev.payload.text ?? ""), actions: [] };
        turns.set(ev.turn_id!, item);
        items.push(item);
        break;
      }
      case "action":
        if (turn) turn.actions.push(ev.payload as ActionPayload);
        else items.push({ kind: "learner_action", key: `a-${ev.seq}`, action: ev.payload as ActionPayload });
        break;
      case "answer":
        if (turn) turn.answer = ev.payload as AnswerPayload;
        break;
      case "turn.interrupted":
        if (turn) turn.interrupted = true;
        break;
      case "stop":
        items.push({ kind: "system", key: `s-${ev.seq}`, text: t("sys_stop", { epoch: ev.epoch }) });
        break;
      case "control":
        items.push({
          kind: "system",
          key: `s-${ev.seq}`,
          text: ev.payload.holder === "learner" ? t("sys_control_learner") : t("sys_control_tutor"),
        });
        break;
      case "lab.ready":
        items.push({ kind: "system", key: `s-${ev.seq}`, text: t("sys_lab_ready") });
        break;
      case "session.ended":
        items.push({ kind: "system", key: `s-${ev.seq}`, text: t("sys_ended", { reason: String(ev.payload.reason) }) });
        break;
    }
  }
  return items;
}

function ActionLine({ action }: { action: ActionPayload }) {
  const { t } = useI18n();
  return (
    <span className="action-line">
      <Mark
        ok={action.status === "succeeded"}
        label={
          <>
            <Ltr>{action.tool}</Ltr> — {tDynamic(t, "status_", action.status)}
            {action.error_category && (
              <>
                {" "}
                (<Ltr>{action.error_category}</Ltr>)
              </>
            )}
            {action.observed_state_version != null && (
              <span className="muted small">
                {" "}
                · <Ltr>v{action.observed_state_version}</Ltr>
              </span>
            )}
          </>
        }
      />
    </span>
  );
}

export function Transcript({ events }: { events: SessionEvent[] }) {
  const { t } = useI18n();
  const items = buildTranscript(events, t);
  return (
    <ol className="transcript">
      {items.map((item) => {
        if (item.kind === "system") {
          return (
            <li key={item.key} className="t-system">
              {item.text}
            </li>
          );
        }
        if (item.kind === "learner_action") {
          return (
            <li key={item.key} className="t-system">
              {t("yourAction")}: <ActionLine action={item.action} />
            </li>
          );
        }
        const answer = item.answer;
        return (
          <li key={item.key} className="t-turn">
            <div className="bubble bubble-learner">
              <span className="who">{t("you")}</span>
              <p dir="auto">{item.text}</p>
            </div>
            <div className="bubble bubble-tutor">
              <span className="who">
                {t("tutor")}
                {answer && answer.kind !== "answer" && (
                  <span className="tag tag-warn">{tDynamic(t, "kind_", answer.kind)}</span>
                )}
              </span>
              {item.actions.length > 0 && (
                <details className="actions-log" open>
                  <summary>
                    {t("actionsLog")} ({item.actions.length})
                  </summary>
                  <ul>
                    {item.actions.map((a) => (
                      <li key={a.action_id}>
                        <ActionLine action={a} />
                      </li>
                    ))}
                  </ul>
                </details>
              )}
              {item.interrupted && <p className="muted">{t("turnInterrupted")}</p>}
              {answer?.text && (
                <div className="answer-text">
                  {answer.text.split("\n").map((line, i) =>
                    line.trim() ? (
                      <p key={i} dir="auto">
                        {line}
                      </p>
                    ) : null,
                  )}
                </div>
              )}
              {!answer && !item.interrupted && <p className="muted">…</p>}
              {answer && answer.sources.length > 0 && (
                <div className="sources">
                  <span className="muted small">{t("sources")}:</span>
                  <ul>
                    {answer.sources.map((s) => (
                      <li key={s.passage_id}>
                        <a href={`#/course/${encodeURIComponent(s.lesson_id)}`} dir="auto">
                          {s.title}
                        </a>{" "}
                        <span className="muted small">
                          <Ltr>
                            {s.lesson_id}#{s.section_id}
                          </Ltr>
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
