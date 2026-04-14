export const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api";

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

export async function apiFetch<T>(
  path: string,
  token: string,
  init?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init?.headers || {})
    },
    cache: "no-store"
  });

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
