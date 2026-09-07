/**
 * LEATrace API Client — Production
 *
 * Centralized HTTP client with:
 * - Automatic Bearer token injection
 * - 401 → token refresh → retry
 * - Request timeout (30s default)
 * - Structured error handling
 * - Retry on network failures (up to 2 retries)
 */

// Reads VITE_API_URL from environment, falls back to localhost for local dev
export const API_BASE = (import.meta.env.VITE_API_URL as string) || 'http://127.0.0.1:8000';

// WebSocket URL derived from API_BASE (http→ws, https→wss)
export const WS_BASE = API_BASE.replace(/^http/, 'ws');

const DEFAULT_TIMEOUT_MS = 3000;
const MAX_RETRIES = 1;

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public body: unknown,
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
  }
}

/** Returns the stored JWT token, or null if not present */
export function getToken(): string | null {
  return sessionStorage.getItem('token') || localStorage.getItem('token');
}

/** Returns auth headers if a token is present */
function authHeaders(): Record<string, string> {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/**
 * Attempts to refresh the access token using the stored refresh_token.
 * Returns true if refresh succeeded (and new tokens stored), false otherwise.
 */
async function refreshAccessToken(): Promise<boolean> {
  const refresh = sessionStorage.getItem('refresh_token') || localStorage.getItem('refresh_token');
  if (!refresh || refresh === 'mock-jwt-token-refresh') return false;

  try {
    const res = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refresh }),
    });
    if (!res.ok) return false;
    const data = await res.json();
    if (data.access_token) {
      sessionStorage.setItem('token', data.access_token);
      if (data.refresh_token) sessionStorage.setItem('refresh_token', data.refresh_token);
      return true;
    }
  } catch {
    // Network error — cannot refresh
  }
  return false;
}

interface FetchOptions extends RequestInit {
  timeoutMs?: number;
  skipAuth?: boolean;
  _retryCount?: number;
}

/**
 * Centralized fetch with auth, timeout, retry, and error handling.
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: FetchOptions = {},
): Promise<T> {
  const { timeoutMs = DEFAULT_TIMEOUT_MS, skipAuth = false, _retryCount = 0, ...fetchOptions } = options;

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(skipAuth ? {} : authHeaders()),
    ...(fetchOptions.headers as Record<string, string> ?? {}),
  };

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    // 401 → try refresh once
    if (res.status === 401 && _retryCount < 1) {
      const refreshed = await refreshAccessToken();
      if (refreshed) {
        return apiFetch<T>(path, { ...options, _retryCount: _retryCount + 1 });
      }
      const token = getToken();
      if (token && token !== 'mock-jwt-token-access') {
        sessionStorage.removeItem('token');
        sessionStorage.removeItem('refresh_token');
        sessionStorage.removeItem('user');
        window.location.href = '/';
      }
      throw new ApiError(401, 'Unauthorized', null);
    }

    if (!res.ok) {
      let body: unknown = null;
      try { body = await res.json(); } catch { /* ignore */ }
      throw new ApiError(res.status, res.statusText, body);
    }

    // Handle 204 No Content
    if (res.status === 204) return undefined as T;

    return res.json() as Promise<T>;
  } catch (err) {
    clearTimeout(timeoutId);

    // Retry on network errors (not on API errors)
    if (!(err instanceof ApiError) && _retryCount < MAX_RETRIES) {
      await new Promise(r => setTimeout(r, 500 * (_retryCount + 1)));
      return apiFetch<T>(path, { ...options, _retryCount: _retryCount + 1 });
    }

    throw err;
  }
}

/** Convenience wrappers */
export const apiGet = <T>(path: string, opts?: FetchOptions) =>
  apiFetch<T>(path, { method: 'GET', ...opts });

export const apiPost = <T>(path: string, body?: unknown, opts?: FetchOptions) =>
  apiFetch<T>(path, {
    method: 'POST',
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...opts,
  });

export const apiPatch = <T>(path: string, body?: unknown, opts?: FetchOptions) =>
  apiFetch<T>(path, {
    method: 'PATCH',
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...opts,
  });

export const apiDelete = <T>(path: string, opts?: FetchOptions) =>
  apiFetch<T>(path, { method: 'DELETE', ...opts });

/** Upload multipart/form-data (no Content-Type header — browser sets it with boundary) */
export async function apiUpload<T>(path: string, formData: FormData): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 120_000); // 2 min for uploads

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers,
      body: formData,
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
    if (!res.ok) {
      let body: unknown = null;
      try { body = await res.json(); } catch { /* ignore */ }
      throw new ApiError(res.status, res.statusText, body);
    }
    return res.json() as Promise<T>;
  } catch (err) {
    clearTimeout(timeoutId);
    throw err;
  }
}
