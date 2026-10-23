import type { ReactNode } from "react";
import { ApiError, BackendUnreachable } from "../api";
import { useI18n } from "../i18n";

/** Identifiers, URLs, code and timestamps stay left-to-right inside Arabic text. */
export function Ltr({ children }: { children: ReactNode }) {
  return (
    <bdi dir="ltr" className="ltr">
      {children}
    </bdi>
  );
}

function pad(n: number): string {
  return String(n).padStart(2, "0");
}

/** Local time as YYYY-MM-DD HH:mm, always left-to-right so it reads the same in Arabic and English. */
export function Time({ iso }: { iso: string | null | undefined }) {
  if (!iso) return null;
  const d = new Date(iso);
  const text = `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
  return (
    <time dateTime={iso} dir="ltr" className="ltr">
      {text}
    </time>
  );
}

export function Mark({ ok, label }: { ok: boolean; label: ReactNode }) {
  // Never colour alone: the ✓/✗ glyph and a screen-reader word carry the meaning.
  const { lang } = useI18n();
  return (
    <span className={`mark ${ok ? "mark-ok" : "mark-bad"}`}>
      <span aria-hidden="true" className="mark-glyph">
        {ok ? "✓" : "✗"}
      </span>
      <span className="sr-only">{ok ? (lang === "ar" ? "ناجح: " : "pass: ") : lang === "ar" ? "غير ناجح: " : "fail: "}</span>
      {label}
    </span>
  );
}

export function errorText(err: unknown, fallback: string): string {
  if (err instanceof ApiError) return `${err.message} (${err.code})`;
  if (err instanceof BackendUnreachable) return "Backend unreachable";
  if (err instanceof Error) return err.message;
  return fallback;
}

export function ErrorNote({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  const { t } = useI18n();
  if (!error) return null;
  return (
    <div className="notice notice-error" role="alert">
      <strong>{t("error")}:</strong> <span>{errorText(error, t("error"))}</span>
      {onRetry && (
        <button type="button" className="btn btn-small" onClick={onRetry}>
          {t("retry")}
        </button>
      )}
    </div>
  );
}

export function Loading() {
  const { t } = useI18n();
  return (
    <p className="muted" role="status">
      {t("loading")}
    </p>
  );
}

export function Card({ title, children, className = "" }: { title?: ReactNode; children: ReactNode; className?: string }) {
  return (
    <section className={`card ${className}`}>
      {title && <h2 className="card-title">{title}</h2>}
      {children}
    </section>
  );
}
