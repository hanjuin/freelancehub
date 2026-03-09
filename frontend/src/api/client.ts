/**
 * Lightweight fetch wrapper.
 * - Injects Authorization header from in-memory token store.
 * - On 401, attempts one silent token refresh then retries.
 * - Throws ApiError on non-2xx responses.
 */

import type { ApiError } from '@/types/auth'

const BASE_URL = '/api/v1'

// In-memory token store — never written to localStorage
let _accessToken: string | null = null

export const tokenStore = {
  get: () => _accessToken,
  set: (t: string | null) => { _accessToken = t },
  clear: () => { _accessToken = null },
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function buildHeaders(extra?: HeadersInit): HeadersInit {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(extra as Record<string, string>),
  }
  if (_accessToken) {
    headers['Authorization'] = `Bearer ${_accessToken}`
  }
  return headers
}

async function parseError(res: Response): Promise<never> {
  let detail = `HTTP ${res.status}`
  try {
    const body = await res.json() as ApiError
    detail = body.detail ?? detail
  } catch {
    // ignore parse error
  }
  throw new Error(detail)
}

// ── Silent refresh ───────────────────────────────────────────────────────────

let _refreshPromise: Promise<void> | null = null

async function silentRefresh(): Promise<void> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) throw new Error('No refresh token')

  const res = await fetch(`${BASE_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!res.ok) {
    localStorage.removeItem('refresh_token')
    tokenStore.clear()
    throw new Error('Session expired')
  }

  const data = await res.json() as { access_token: string; refresh_token: string }
  tokenStore.set(data.access_token)
  localStorage.setItem('refresh_token', data.refresh_token)
}

// ── Core request ─────────────────────────────────────────────────────────────

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options?: { form?: boolean; skipAuth?: boolean },
): Promise<T> {
  const isForm = options?.form === true

  const headers: Record<string, string> = {}
  if (!isForm) headers['Content-Type'] = 'application/json'
  if (_accessToken && !options?.skipAuth) {
    headers['Authorization'] = `Bearer ${_accessToken}`
  }

  const init: RequestInit = {
    method,
    headers,
    body: body
      ? isForm
        ? (body as BodyInit)
        : JSON.stringify(body)
      : undefined,
  }

  let res = await fetch(`${BASE_URL}${path}`, init)

  // Auto-refresh on 401
  if (res.status === 401 && !options?.skipAuth) {
    if (!_refreshPromise) {
      _refreshPromise = silentRefresh().finally(() => { _refreshPromise = null })
    }
    try {
      await _refreshPromise
    } catch {
      throw new Error('Session expired. Please log in again.')
    }
    // Retry with new token
    headers['Authorization'] = `Bearer ${_accessToken!}`
    res = await fetch(`${BASE_URL}${path}`, { ...init, headers })
  }

  if (!res.ok) return parseError(res)

  // 204 No Content
  if (res.status === 204) return undefined as T

  return res.json() as Promise<T>
}

export const api = {
  get:    <T>(path: string)                     => request<T>('GET', path),
  post:   <T>(path: string, body?: unknown)     => request<T>('POST', path, body),
  put:    <T>(path: string, body?: unknown)     => request<T>('PUT', path, body),
  patch:  <T>(path: string, body?: unknown)     => request<T>('PATCH', path, body),
  delete: <T>(path: string)                     => request<T>('DELETE', path),
  /** For endpoints that require application/x-www-form-urlencoded */
  postForm: <T>(path: string, body: URLSearchParams) =>
    request<T>('POST', path, body, { form: true }),
}

// Also export buildHeaders for non-api usages
export { buildHeaders }
