import { useState } from "react";
import { api, type Me } from "../api";
import { Card, ErrorNote, Loading, Ltr, Time } from "../components/common";
import { useApp, useLoad } from "../context";
import { tDynamic, useI18n } from "../i18n";

export function Settings() {
  const { t } = useI18n();
  const { me, setMe } = useApp();
  const [form, setForm] = useState<Pick<Me, "language" | "explanation_pref" | "memory_enabled">>({
    language: me.language,
    explanation_pref: me.explanation_pref,
    memory_enabled: me.memory_enabled,
  });
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [memory, memoryError, reloadMemory] = useLoad(() => api.memory(), []);

  const save = async () => {
    setError(null);
    setSaved(false);
    try {
      setMe(await api.updateMe(form));
      setSaved(true);
    } catch (err) {
      setError(err);
    }
  };

  const remove = async (id: string) => {
    try {
      await api.deleteMemory(id);
    } catch (err) {
      setError(err);
    }
    reloadMemory();
  };

  const resetAll = async () => {
    if (!window.confirm(t("resetMemoryConfirm"))) return;
    try {
      await api.resetMemory();
    } catch (err) {
      setError(err);
    }
    reloadMemory();
  };

  return (
    <div className="page">
      <header className="page-head">
        <h1>{t("settingsTitle")}</h1>
        <p className="muted small">
          {t("learnerId")}: <Ltr>{me.learner_id}</Ltr>
        </p>
      </header>
      <div className="grid-2">
        <Card title={t("preferences")}>
          <form
            className="form"
            onSubmit={(e) => {
              e.preventDefault();
              void save();
            }}
          >
            <label className="field">
              <span className="field-label">{t("language")}</span>
              <select
                value={form.language}
                onChange={(e) => setForm({ ...form, language: e.target.value as Me["language"] })}
              >
                <option value="ar" lang="ar">
                  العربية
                </option>
                <option value="en" lang="en">
                  English
                </option>
              </select>
            </label>
            <fieldset className="field">
              <legend className="field-label">{t("explanationPref")}</legend>
              {(["short", "detailed"] as const).map((pref) => (
                <label key={pref} className="radio">
                  <input
                    type="radio"
                    name="explanation_pref"
                    value={pref}
                    checked={form.explanation_pref === pref}
                    onChange={() => setForm({ ...form, explanation_pref: pref })}
                  />
                  {pref === "short" ? t("prefShort") : t("prefDetailed")}
                </label>
              ))}
            </fieldset>
            <label className="checkbox">
              <input
                type="checkbox"
                checked={form.memory_enabled}
                onChange={(e) => setForm({ ...form, memory_enabled: e.target.checked })}
              />
              {t("memoryEnabled")}
            </label>
            <div className="row">
              <button type="submit" className="btn btn-primary">
                {t("save")}
              </button>
              {saved && (
                <span role="status" className="mark mark-ok">
                  ✓ {t("saved")}
                </span>
              )}
            </div>
          </form>
          <ErrorNote error={error} />
        </Card>

        <Card title={t("memoryTitle")}>
          <p className="muted">{t("memoryExplain")}</p>
          {memoryError ? (
            <ErrorNote error={memoryError} onRetry={reloadMemory} />
          ) : !memory ? (
            <Loading />
          ) : memory.length === 0 ? (
            <p className="placeholder">{t("noMemory")}</p>
          ) : (
            <>
              <ul className="memory-list">
                {memory.map((m) => (
                  <li key={m.memory_id}>
                    <div>
                      <strong>{tDynamic(t, "mem_", m.kind)}</strong>
                      <p dir="auto">{m.text}</p>
                      <p className="muted small">
                        <Time iso={m.updated_at} />
                        {m.source_session_id && (
                          <>
                            {" "}
                            · {t("fromSession")} <Ltr>{m.source_session_id}</Ltr>
                          </>
                        )}
                      </p>
                    </div>
                    <button type="button" className="btn btn-small" onClick={() => void remove(m.memory_id)}>
                      {t("deleteItem")}
                    </button>
                  </li>
                ))}
              </ul>
              <button type="button" className="btn btn-danger-soft" onClick={() => void resetAll()}>
                {t("resetMemory")}
              </button>
            </>
          )}
        </Card>
      </div>
    </div>
  );
}
