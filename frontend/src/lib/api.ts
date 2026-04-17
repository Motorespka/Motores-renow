export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

/** Sem URL pública da API, o bundle usa localhost — no Vercel o browser não alcança isso. */
function isDefaultLocalApiBase(): boolean {
  const base = (process.env.NEXT_PUBLIC_API_BASE_URL || "").trim();
  return !base || base.includes("localhost") || base.includes("127.0.0.1");
}

export type ApiError = {
  status: number;
  detail: string;
};

export class ApiRequestError extends Error {
  status: number;

  constructor(status: number, detail: string) {
    super(detail || "Erro de requisicao.");
    this.name = "ApiRequestError";
    this.status = status;
  }
}

function mockFetch<T>(path: string, init?: RequestInit): T {
  const cleanPath = path.split("?")[0] || path;
  if (cleanPath === "/auth/me") {
    return {
      authenticated: true,
      profile: {
        user_id: "dev",
        email: "dev@localhost",
        username: "dev",
        display_name: "Dev (Localhost)",
        nome: "Dev",
        role: "admin",
        plan: "dev",
        source: "dev",
        tier: "local",
        ativo: true,
        is_admin: true,
        cadastro_allowed: true,
      },
    } as T;
  }
  if (cleanPath === "/motors") {
    const now = Date.now();
    const items = [
      { id: "dev-1001", marca: "WEG", modelo: "W22", potencia: "10 CV", rpm: "1750", created_at: now - 1000 * 60 * 15 },
      { id: "dev-1002", marca: "Siemens", modelo: "1LE0", potencia: "15 CV", rpm: "3500", created_at: now - 1000 * 60 * 40 },
      { id: "dev-1003", marca: "ABB", modelo: "M2BAX", potencia: "7.5 CV", rpm: "1750", created_at: now - 1000 * 60 * 90 },
      { id: "dev-1004", marca: "Eberle", modelo: "Linha X", potencia: "5 CV", rpm: "1750", created_at: now - 1000 * 60 * 160 },
    ];
    return { mode: "full", total: items.length, items } as T;
  }
  if (cleanPath.startsWith("/motors/")) {
    const id = decodeURIComponent(cleanPath.replace("/motors/", ""));
    return {
      item: {
        id,
        marca: "WEG",
        modelo: "W22",
        potencia: "10 CV",
        rpm: "1750",
        tensao: "220/380V",
        carcaca: "112M",
      },
      raw: {
        id,
        origem: "dev-mock",
        placa: { fabricante: "WEG", modelo: "W22", potencia: "10 CV", rpm: "1750", tensao: "220/380V" },
        observacoes: ["Mock local para validação de UI."],
      },
    } as T;
  }
  if (cleanPath.startsWith("/admin/users/search")) {
    const base = [
      { id: "dev-u1", email: "admin@localhost", username: "admin", nome: "Admin Dev", role: "admin", plan: "dev", ativo: true },
      { id: "dev-u2", email: "tech@localhost", username: "tech", nome: "Tecnico Dev", role: "user", plan: "free", ativo: true },
      { id: "dev-u3", email: "viewer@localhost", username: "viewer", nome: "Viewer Dev", role: "user", plan: "free", ativo: false },
    ];
    return base as T;
  }
  if (cleanPath.startsWith("/admin/users/") && (init?.method || "GET").toUpperCase() === "PATCH") {
    try {
      const body = typeof init?.body === "string" ? (JSON.parse(init.body) as Record<string, unknown>) : {};
      const id = decodeURIComponent(cleanPath.replace("/admin/users/", ""));
      return {
        id,
        email: "dev@localhost",
        username: String(body.username ?? "dev"),
        nome: String(body.nome ?? "Dev"),
        role: String(body.role ?? "user"),
        plan: String(body.plan ?? "free"),
        ativo: Boolean(body.ativo ?? true),
      } as T;
    } catch {
      return {} as T;
    }
  }
  if (cleanPath === "/diagnostics") {
    return {
      total: 2,
      items: [
        { id: "d1", motor_id: "dev-1001", created_by: "dev", status: "done", score: 88, summary: "OK", recommendations: [], evidence: { source: "dev" }, error: "" },
        { id: "d2", motor_id: "dev-1002", created_by: "dev", status: "done", score: 72, summary: "Atenção", recommendations: [], evidence: { source: "dev" }, error: "" },
      ],
    } as T;
  }
  if (cleanPath === "/diagnostics/run") {
    return {
      ok: true,
      message: "Diagnóstico gerado (DEV).",
      created: 1,
      items: [
        { id: "d3", motor_id: "dev-1003", created_by: "dev", status: "done", score: 81, summary: "OK", recommendations: [], evidence: { source: "dev" }, error: "" },
      ],
    } as T;
  }
  if (cleanPath === "/conferences") {
    return {
      total: 1,
      items: [
        { id: "c1", motor_id: "dev-1001", created_by: "dev", status: "pending", confidence: 92, diff: {}, decision: {} },
      ],
    } as T;
  }
  if (cleanPath.includes("/conferences/") && cleanPath.endsWith("/diff")) {
    return {
      ok: true,
      record: { id: "c1", motor_id: "dev-1001", created_by: "dev", status: "pending", confidence: 92, diff: { rpm: { ok: true } }, decision: {} },
    } as T;
  }
  if (cleanPath.includes("/conferences/") && cleanPath.endsWith("/decision")) {
    return {
      ok: true,
      record: { id: "c1", motor_id: "dev-1001", created_by: "dev", status: "approved", confidence: 92, diff: {}, decision: { approved: true } },
    } as T;
  }
  if (cleanPath === "/settings/me") {
    if ((init?.method || "GET").toUpperCase() === "PATCH") {
      return { ui_prefs: { theme: "dark" }, feature_flags: { dev: true } } as T;
    }
    return { ui_prefs: { theme: "dark" }, feature_flags: { dev: true } } as T;
  }
  return {} as T;
}

export async function apiFetch<T>(
  path: string,
  token: string,
  init?: RequestInit
): Promise<T> {
  // Local DEV fallback: when auth returns the "dev" token, serve mock data
  // so the UI can be validated without Supabase/backend running.
  if (token === "dev") {
    return mockFetch<T>(path, init);
  }

  const onLocalhost =
    typeof window !== "undefined" &&
    (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1");
  // Localhost: mock se API cair. Vercel sem NEXT_PUBLIC_API_BASE_URL público: mesmo problema que localhost na URL.
  const allowMockFallback = onLocalhost || (typeof window !== "undefined" && isDefaultLocalApiBase());

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...(init?.headers || {})
      },
      cache: "no-store"
    });
  } catch (e) {
    // If the API is offline locally, keep the UI functional with mock data.
    if (allowMockFallback) {
      return mockFetch<T>(path, init);
    }
    throw e;
  }

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = (await response.json()) as { detail?: string };
      if (payload?.detail) {
        detail = payload.detail;
      }
    } catch {
      // no-op
    }
    throw new ApiRequestError(response.status, detail);
  }

  return (await response.json()) as T;
}
