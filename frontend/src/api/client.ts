import type { ApiFailure } from "@/types/api";

export const API_PREFIX = "/api/v1";

export class ApiError extends Error {
  constructor(public readonly failure: ApiFailure, public readonly status: number) {
    super(failure.message);
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    const failure = (await response.json().catch(() => ({
      code: "NETWORK_ERROR",
      message: `请求失败 (${response.status})`,
    }))) as ApiFailure;
    throw new ApiError(failure, response.status);
  }
  return response.json() as Promise<T>;
}

export function query(parameters: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(parameters)) {
    if (value !== undefined) search.set(key, String(value));
  }
  return search.toString();
}
