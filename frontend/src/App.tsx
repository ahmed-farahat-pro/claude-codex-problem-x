import { useCallback, useEffect, useMemo, useState } from "react";
import { api, BackendUnreachable, ensureLearner, type Health, type Lang, type Me } from "./api";
import { ErrorNote, Loading } from "./components/common";
import { ModeBadge, NavRail } from "./components/NavRail";
import { AppContext, useHashRoute } from "./context";
import { I18nContext, makeT } from "./i18n";
import { CourseScreen } from "./screens/Course";
import { Dashboard } from "./screens/Dashboard";
import { LiveRoom } from "./screens/LiveRoom";
import { MyWork } from "./screens/MyWork";
import { Settings } from "./screens/Settings";

const LANG_KEY = "fourweeks.lang";

function initialLang(): Lang {
  try {
    return localStorage.getItem(LANG_KEY) === "en" ? "en" : "ar";
  } catch {
    return "ar";
  }
}

export function App() {
  const [lang, setLang] = useState<Lang>(initialLang);
  const [health, setHealth] = useState<Health | null>(null);
  const [me, setMeState] = useState<Me | null>(null);
  const [bootError, setBootError] = useState<unknown>(null);
  const route = useHashRoute();
  const t = useMemo(() => makeT(lang), [lang]);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
    try {
      localStorage.setItem(LANG_KEY, lang);
    } catch {
      /* preference kept for this page only */
    }
  }, [lang]);

  const boot = useCallback(async () => {
    setBootError(null);
    try {
      const [h, learner] = await Promise.all([api.health(), ensureLearner(initialLang())]);
      setHealth(h);
      setMeState(learner);
      setLang(learner.language);
    } catch (err) {
      setBootError(err);
    }
  }, []);

  useEffect(() => {
    void boot();
  }, [boot]);

  const setMe = useCallback((next: Me) => {
    setMeState(next);
    setLang(next.language);
  }, []);

  const toggleLanguage = async () => {
    const next: Lang = lang === "ar" ? "en" : "ar";
    setLang(next);
    if (me) {
      try {
        setMeState(await api.updateMe({ language: next }));
      } catch {
        /* the UI still switches; the tutor language follows on the next successful save */
      }
    }
  };

  const i18n = { lang, t };

  if (bootError) {
    const down = bootError instanceof BackendUnreachable;
    return (
      <I18nContext.Provider value={i18n}>
        <main className="boot" id="main">
          {down ? (
            <div className="notice notice-error" role="alert">
              <h1>{t("backendDownTitle")}</h1>
              <p>{t("backendDownBody")}</p>
              <pre dir="ltr" className="code">
                cd backend && .venv/bin/uvicorn app.main:create_app --factory --reload --port 8000
              </pre>
              <button type="button" className="btn btn-primary" onClick={() => void boot()}>
                {t("retry")}
              </button>
            </div>
          ) : (
            <ErrorNote error={bootError} onRetry={() => void boot()} />
          )}
        </main>
      </I18nContext.Provider>
    );
  }

  if (!health || !me) {
    return (
      <I18nContext.Provider value={i18n}>
        <main className="boot" id="main">
          <Loading />
        </main>
      </I18nContext.Provider>
    );
  }

  let screen;
  switch (route.screen) {
    case "course":
      screen = <CourseScreen lessonId={route.param} />;
      break;
    case "live":
      screen = <LiveRoom lessonId={route.param ?? "L03"} />;
      break;
    case "work":
      screen = <MyWork artifactId={route.param} />;
      break;
    case "settings":
      screen = <Settings />;
      break;
    default:
      screen = <Dashboard />;
  }

  return (
    <I18nContext.Provider value={i18n}>
      <AppContext.Provider value={{ me, setMe, health }}>
        <a className="skip-link" href="#main">
          {t("skipToContent")}
        </a>
        <div className="shell">
          <NavRail current={route.screen} health={health} />
          <div className="workspace">
            <header className="topbar">
              <ModeBadge health={health} />
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => void toggleLanguage()}
                aria-label={t("switchLanguageLabel")}
                lang={lang === "ar" ? "en" : "ar"}
              >
                {t("switchLanguage")}
              </button>
            </header>
            <main id="main" tabIndex={-1}>
              {screen}
            </main>
          </div>
        </div>
      </AppContext.Provider>
    </I18nContext.Provider>
  );
}
