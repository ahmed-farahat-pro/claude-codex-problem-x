import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { Health, Me } from "./api";

type AppState = {
  me: Me;
  setMe: (me: Me) => void;
  health: Health;
};

export const AppContext = createContext<AppState | null>(null);

export function useApp(): AppState {
  const value = useContext(AppContext);
  if (!value) throw new Error("useApp outside AppContext");
  return value;
}

export type Route = { screen: string; param: string | null };

function parseHash(): Route {
  const parts = window.location.hash.replace(/^#\/?/, "").split("/").filter(Boolean);
  return { screen: parts[0] ?? "dashboard", param: parts[1] ? decodeURIComponent(parts[1]) : null };
}

export function useHashRoute(): Route {
  const [route, setRoute] = useState<Route>(parseHash);
  useEffect(() => {
    const onChange = () => setRoute(parseHash());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}

export function navigate(screen: string, param?: string | null) {
  window.location.hash = `#/${screen}${param ? `/${encodeURIComponent(param)}` : ""}`;
}

/** Load data once per key; returns [data, error, reload]. */
export function useLoad<T>(load: () => Promise<T>, deps: unknown[]): [T | null, unknown, () => void] {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [tick, setTick] = useState(0);
  // eslint-style exhaustive deps are intentionally the caller's deps plus the reload tick.
  useEffect(() => {
    let alive = true;
    setError(null);
    load().then(
      (value) => alive && setData(value),
      (err) => alive && setError(err),
    );
    return () => {
      alive = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);
  const reload = useCallback(() => setTick((n) => n + 1), []);
  return [data, error, reload];
}
