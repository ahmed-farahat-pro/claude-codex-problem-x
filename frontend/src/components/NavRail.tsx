import type { Health } from "../api";
import { useI18n, type StringKey } from "../i18n";

const ITEMS: { screen: string; key: StringKey; icon: string }[] = [
  { screen: "dashboard", key: "navDashboard", icon: "◧" },
  { screen: "course", key: "navCourse", icon: "☰" },
  { screen: "live", key: "navLive", icon: "◉" },
  { screen: "work", key: "navWork", icon: "▤" },
  { screen: "settings", key: "navSettings", icon: "⚙" },
];

export function NavRail({ current, health }: { current: string; health: Health }) {
  const { t } = useI18n();
  return (
    <nav className="rail" aria-label={t("navLabel")}>
      <a className="brand" href="#/dashboard">
        <span dir="ltr">4weeks.ai</span>
      </a>
      <ul>
        {ITEMS.map((item) => (
          <li key={item.screen}>
            <a
              href={`#/${item.screen}`}
              className={current === item.screen ? "rail-link active" : "rail-link"}
              aria-current={current === item.screen ? "page" : undefined}
            >
              <span aria-hidden="true" className="rail-icon">
                {item.icon}
              </span>
              {t(item.key)}
            </a>
          </li>
        ))}
      </ul>
      <p className="rail-foot">
        {t("version")} <bdi dir="ltr">{health.version}</bdi>
      </p>
    </nav>
  );
}

export function ModeBadge({ health }: { health: Health }) {
  const { t } = useI18n();
  const deterministic = health.mode === "deterministic";
  return (
    <span
      className={`mode-badge ${deterministic ? "mode-test" : "mode-real"}`}
      title={deterministic ? t("modeDeterministicHint") : t("modeRealHint")}
    >
      <span aria-hidden="true">{deterministic ? "◇" : "◆"}</span>{" "}
      {deterministic ? t("modeDeterministic") : t("modeReal")}
      {!deterministic && (
        <>
          {" · "}
          <bdi dir="ltr">{health.model}</bdi>
        </>
      )}
      <span className="mode-hint">{deterministic ? t("modeDeterministicHint") : t("modeRealHint")}</span>
    </span>
  );
}
