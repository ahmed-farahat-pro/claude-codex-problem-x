import type { DraftChecks, PromptChecks } from "../api";
import { useI18n, type StringKey } from "../i18n";
import { Mark } from "./common";

const ELEMENTS = ["task", "context", "audience", "constraints", "output_format"] as const;

export function DraftChecksView({ draft, prompt }: { draft: DraftChecks; prompt?: PromptChecks }) {
  const { t, lang } = useI18n();
  const unsupported = [...draft.unsupported_numbers, ...draft.offer_terms];
  const sep = lang === "ar" ? "، " : ", ";
  return (
    <div className="checks">
      <ul className="check-list" aria-label={t("checks")}>
        <li>
          <Mark ok={draft.within_limit} label={`${t("length")}: ${t("wordsOf", { count: draft.word_count, max: draft.max_words })}`} />
        </li>
        <li>
          <Mark ok={draft.has_cta} label={t("cta")} />
        </li>
        <li>
          <Mark
            ok={unsupported.length === 0}
            label={unsupported.length ? t("unsupported", { items: unsupported.join(sep) }) : t("noUnsupported")}
          />
        </li>
      </ul>
      {prompt && (
        <>
          <h4 className="checks-subtitle">{t("promptElements")}</h4>
          <ul className="check-list check-list-inline">
            {ELEMENTS.map((el) => (
              <li key={el}>
                <Mark ok={prompt[el]} label={t(`el_${el}` as StringKey)} />
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
