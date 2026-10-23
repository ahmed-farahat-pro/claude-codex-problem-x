// Typed client for the backend in backend/app/api.py. All routes live under /api.

export type Lang = "ar" | "en";
export type Bilingual = { ar: string; en: string };

export type Health = {
  status: string;
  version: string;
  mode: "deterministic" | "gemini";
  model: string;
  dev_auth: boolean;
};

export type Me = {
  learner_id: string;
  display_name: string;
  language: Lang;
  explanation_pref: "short" | "detailed";
  memory_enabled: boolean;
};

export type Enrollment = {
  course_id: string;
  status: string;
  expires_at: string | null;
  live_allowance_seconds: number;
  live_used_seconds: number;
  live_remaining_seconds: number;
};

export type LessonSummary = {
  lesson_id: string;
  version: string;
  title: Bilingual;
  outcome: string;
  has_lab: boolean;
};

export type Week = {
  week: number;
  title: Bilingual;
  portfolio_result: string;
  lessons: LessonSummary[];
};

export type CourseOutline = {
  course_id: string;
  version: string;
  title: Bilingual;
  brief: Record<string, string | null>;
  release: { last_review_date: string | null; known_limitations: string[] };
  weeks: Week[];
};

export type RubricCriterion = { criterion_id: string; label: Bilingual };

export type LessonDetail = {
  lesson_id: string;
  week: number;
  version: string;
  title: Bilingual;
  outcome: string;
  lab: string;
  deliverable: string;
  acceptance: string;
  course_id: string;
  course_version: string;
  reviewed_at: string | null;
  recipe: null | {
    recipe_version: string;
    outcome: Bilingual;
    timeline: { start: string; end: string; on_screen: string; evidence: string }[];
    fixture_id: string;
    practice_fixture_id: string | null;
    rubric: { rubric_id: string; version: string; note?: string; max_words?: number; criteria: RubricCriterion[] };
    allowed_tools: string[];
  };
  sections: { passage_id: string; section_id: string; title: string; text: string; source_url: string }[];
};

export type Progress = {
  course_id: string;
  lesson_id: string;
  lesson_version: string;
  status: "started" | "completed";
  updated_at: string;
};

export type Draft = {
  draft_id: string;
  number: number;
  text: string;
  model: string;
  prompt: string;
  fixture_id: string;
  fixture_version: string;
  created_at: string;
  created_by?: "learner" | "tutor";
  parent_draft_id?: string;
  instruction?: string;
};

export type LabView = {
  status: "ready" | "disposed" | string;
  state_version: number;
  template_id?: string;
  template_version?: string;
  fixture_id?: string;
  fixture_version?: string;
  business_name?: string;
  brief?: string;
  audience?: string;
  tone?: string;
  prompt?: string;
  drafts?: Draft[];
};

export type SessionState =
  | "warming"
  | "listening"
  | "thinking"
  | "acting"
  | "speaking"
  | "interrupted"
  | "recovering"
  | "ending"
  | "ended";

export type SessionSnapshot = {
  session_id: string;
  course_id: string;
  course_version: string;
  lesson_id: string;
  mode: string;
  state: SessionState;
  epoch: number;
  control: "tutor" | "learner";
  started_at: string;
  expires_at: string;
  ended_at: string | null;
  end_reason: string | null;
  remaining_seconds: number;
  lab: LabView;
  usage: {
    turns: number;
    actions: number;
    model_input_tokens: number;
    model_output_tokens: number;
    duration_seconds: number | null;
  };
};

export type DraftChecks = {
  word_count: number;
  max_words: number;
  within_limit: boolean;
  has_cta: boolean;
  unsupported_numbers: string[];
  offer_terms: string[];
  unsupported_claims: boolean;
};

export type PromptChecks = {
  task: boolean;
  context: boolean;
  audience: boolean;
  constraints: boolean;
  output_format: boolean;
  cta_requested: boolean;
  facts_only: boolean;
  claims_requested: boolean;
  max_words: number | null;
};

export type ActionStatus = "succeeded" | "failed" | "rejected" | "stale" | "skipped" | "pending";

export type ActionResult = {
  action_id: string;
  tool: string;
  actor: "learner" | "tutor";
  status: ActionStatus;
  observed_state_version: number | null;
  result: Record<string, unknown> | null;
  screenshot_ref: string | null;
  duration_ms: number;
  error_category: string | null;
  error_message: string | null;
  replayed: boolean;
  call_id?: string | null;
};

export type Source = {
  passage_id: string;
  lesson_id: string;
  section_id: string;
  title: string;
  source_url: string;
  version: string;
};

export type TurnOut = {
  turn_id: string;
  epoch: number;
  status: "completed" | "interrupted" | "failed";
  answer: string | null;
  answer_kind: string | null;
  error_category: string | null;
  sources: Source[];
  actions: ActionResult[];
  state: SessionState;
  current_epoch: number;
  lab_state_version: number;
};

export type SessionEvent = {
  seq: number;
  session_id: string;
  turn_id: string | null;
  epoch: number;
  type: string;
  payload: Record<string, any>;
  created_at: string;
};

export type MemoryItem = {
  memory_id: string;
  course_id: string;
  kind: "last_successful_task" | "misconception" | "next_practice" | string;
  text: string;
  source_session_id: string | null;
  updated_at: string;
};

export type EndSummary = {
  session_id: string;
  state: string;
  end_reason: string | null;
  usage: {
    duration_seconds: number | null;
    turns: number;
    actions: number;
    model_input_tokens: number;
    model_output_tokens: number;
    allowance_remaining_seconds: number;
  };
  memory_written: MemoryItem[];
};

export type ArtifactSummary = {
  artifact_id: string;
  session_id: string | null;
  course_id: string;
  lesson_id: string;
  kind: string;
  title: string;
  content_hash: string;
  created_at: string;
};

export type Artifact = ArtifactSummary & {
  content: {
    prompt: string;
    draft_text: string;
    model: string;
    draft_id: string;
    draft_number: number | null;
    created_by: string | null;
    generated_at: string;
    fixture_id: string;
    fixture_version: string;
    course_version: string;
    checks: { prompt_checks: PromptChecks; draft_checks: DraftChecks };
    note: string | null;
  };
};

export type Submission = {
  submission_id: string;
  artifact_id: string;
  rubric_id: string;
  rubric_version: string;
  status: "checks_passed" | "revision_requested" | string;
  review_status: "not_reviewed" | "appeal_requested" | string;
  appeal_reason: string | null;
  created_at: string;
  updated_at: string;
  results: { criterion_id: string; label: Bilingual; passed: boolean; evidence: string }[];
};

// ---------------------------------------------------------------- errors

export class ApiError extends Error {
  status: number;
  code: string;
  extra: Record<string, unknown>;
  constructor(status: number, code: string, message: string, extra: Record<string, unknown> = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.extra = extra;
  }
}

/** The backend is not running or the dev proxy cannot reach it. */
export class BackendUnreachable extends Error {}

// ---------------------------------------------------------------- client

const TOKEN_KEY = "fourweeks.token";

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function setToken(token: string | null) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* storage unavailable: the token lives for this page only */
  }
}

let memoryToken: string | null = null;

async function send(method: string, path: string, body?: unknown): Promise<Response> {
  const headers: Record<string, string> = {};
  const token = memoryToken ?? getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let res: Response;
  try {
    res = await fetch(`/api${path}`, {
      method,
      headers,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new BackendUnreachable("Network error");
  }
  const isJson = (res.headers.get("content-type") ?? "").includes("application/json");
  if (!res.ok) {
    if (!isJson && res.status >= 500) throw new BackendUnreachable(`HTTP ${res.status}`);
    let data: any = null;
    try {
      data = isJson ? await res.json() : null;
    } catch {
      data = null;
    }
    const err = data?.error;
    if (err) {
      const { code, message, ...extra } = err;
      throw new ApiError(res.status, code, message, extra);
    }
    // FastAPI request validation errors come back as {"detail": [...]}
    const detail = Array.isArray(data?.detail) ? data.detail.map((d: any) => d.msg).join("; ") : `HTTP ${res.status}`;
    throw new ApiError(res.status, res.status === 422 ? "validation" : "http_error", detail);
  }
  return res;
}

async function json<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await send(method, path, body);
  return (await res.json()) as T;
}

let pendingLearner: Promise<Me> | null = null;

/** Ensure there is a working dev token. Creates a dev learner when none exists or the old one is invalid. */
export function ensureLearner(lang: Lang): Promise<Me> {
  // One in-flight call: React StrictMode runs effects twice and must not create two learners.
  pendingLearner ??= resolveLearner(lang).finally(() => {
    pendingLearner = null;
  });
  return pendingLearner;
}

async function resolveLearner(lang: Lang): Promise<Me> {
  if (getToken()) {
    try {
      return await api.me();
    } catch (e) {
      if (!(e instanceof ApiError && e.status === 401)) throw e;
      setToken(null);
    }
  }
  const created = await json<{ learner_id: string; token: string }>("POST", "/dev/learners", {
    display_name: lang === "ar" ? "متعلم" : "Learner",
    language: lang,
  });
  memoryToken = created.token;
  setToken(created.token);
  return api.me();
}

export const api = {
  health: () => json<Health>("GET", "/health"),
  me: () => json<Me>("GET", "/me"),
  updateMe: (changes: Partial<Pick<Me, "language" | "explanation_pref" | "memory_enabled">>) =>
    json<Me>("PATCH", "/me", changes),
  enrollments: () => json<Enrollment[]>("GET", "/me/enrollments"),

  course: (courseId: string) => json<CourseOutline>("GET", `/courses/${encodeURIComponent(courseId)}`),
  lesson: (courseId: string, lessonId: string) =>
    json<LessonDetail>("GET", `/courses/${encodeURIComponent(courseId)}/lessons/${encodeURIComponent(lessonId)}`),
  progress: () => json<Progress[]>("GET", "/me/progress"),
  setProgress: (courseId: string, lessonId: string, status: "started" | "completed") =>
    json<Progress>("PUT", `/me/progress/${encodeURIComponent(courseId)}/${encodeURIComponent(lessonId)}`, { status }),

  createSession: (courseId: string, lessonId: string) =>
    json<SessionSnapshot>("POST", "/sessions", { course_id: courseId, lesson_id: lessonId }),
  sessionState: (id: string) => json<SessionSnapshot>("GET", `/sessions/${encodeURIComponent(id)}/state`),
  events: (id: string, after: number) =>
    json<SessionEvent[]>("GET", `/sessions/${encodeURIComponent(id)}/events?after=${after}`),
  message: (id: string, text: string, epoch: number) =>
    json<TurnOut>("POST", `/sessions/${encodeURIComponent(id)}/messages`, { text, epoch }),
  action: (id: string, tool: string, args: Record<string, unknown>, epoch: number) =>
    json<ActionResult>("POST", `/sessions/${encodeURIComponent(id)}/actions`, {
      tool,
      args,
      epoch,
      idempotency_key: crypto.randomUUID(),
    }),
  control: (id: string, holder: "tutor" | "learner") =>
    json<SessionSnapshot>("POST", `/sessions/${encodeURIComponent(id)}/control`, { holder }),
  stop: (id: string) =>
    json<{ session_id: string; epoch: number; state: string; lab_state_version: number }>(
      "POST",
      `/sessions/${encodeURIComponent(id)}/stop`,
    ),
  end: (id: string) => json<EndSummary>("POST", `/sessions/${encodeURIComponent(id)}/end`),

  memory: () => json<MemoryItem[]>("GET", "/me/memory"),
  deleteMemory: (id: string) => json<{ deleted: number }>("DELETE", `/me/memory/${encodeURIComponent(id)}`),
  resetMemory: () => json<{ deleted: number }>("DELETE", "/me/memory"),

  artifacts: () => json<ArtifactSummary[]>("GET", "/me/artifacts"),
  artifact: (id: string) => json<Artifact>("GET", `/me/artifacts/${encodeURIComponent(id)}`),
  exportArtifact: async (id: string): Promise<Blob> =>
    (await send("GET", `/me/artifacts/${encodeURIComponent(id)}/export`)).blob(),
  submit: (id: string) => json<Submission>("POST", `/me/artifacts/${encodeURIComponent(id)}/submissions`),
  submissions: () => json<Submission[]>("GET", "/me/submissions"),
  appeal: (id: string, reason: string) =>
    json<Submission>("POST", `/me/submissions/${encodeURIComponent(id)}/appeal`, { reason }),
};

export const COURSE_ID = "ai-for-everyone";
