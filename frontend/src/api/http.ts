/**
 * Minimal fetch wrapper with request / response / error interceptors.
 * Keeps streaming-friendly: does not consume the response body.
 */

export interface RequestConfig extends RequestInit {
  url: string
  /** Prepended to `url`; defaults to '' so it plays well with Vite's /api proxy. */
  baseURL?: string
}

export class ApiError extends Error {
  readonly status: number
  readonly payload?: unknown

  constructor(message: string, status: number, payload?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

type RequestInterceptor = (config: RequestConfig) => RequestConfig | Promise<RequestConfig>
type ResponseInterceptor = (response: Response, config: RequestConfig) => Response | Promise<Response>
type ErrorInterceptor = (error: unknown, config: RequestConfig) => void | Promise<void>

const requestInterceptors: RequestInterceptor[] = []
const responseInterceptors: ResponseInterceptor[] = []
const errorInterceptors: ErrorInterceptor[] = []

export const interceptors = {
  request: {
    use(fn: RequestInterceptor) {
      requestInterceptors.push(fn)
    },
  },
  response: {
    use(fn: ResponseInterceptor) {
      responseInterceptors.push(fn)
    },
  },
  error: {
    use(fn: ErrorInterceptor) {
      errorInterceptors.push(fn)
    },
  },
}

/**
 * Send a request through the interceptor chain.
 * Returns the raw `Response` (body untouched) — callers can `.json()` or stream.
 */
export async function request(config: RequestConfig): Promise<Response> {
  let merged: RequestConfig = { ...config }
  for (const fn of requestInterceptors) {
    merged = await fn(merged)
  }

  const { url, baseURL = '', ...init } = merged
  const fullUrl = `${baseURL}${url}`

  try {
    let response = await fetch(fullUrl, init)
    for (const fn of responseInterceptors) {
      response = await fn(response, merged)
    }
    return response
  } catch (err) {
    for (const fn of errorInterceptors) {
      await fn(err, merged)
    }
    throw err
  }
}

/* -------------------------------------------------------------------------- */
/* Default interceptors                                                       */
/* -------------------------------------------------------------------------- */

// Request: ensure JSON content-type on non-GET when body is a string, attach baseURL.
interceptors.request.use((config) => {
  const method = (config.method ?? 'GET').toUpperCase()
  const headers = new Headers(config.headers)

  if (method !== 'GET' && typeof config.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  return { ...config, headers }
})

// Response: turn non-2xx into ApiError; leave 2xx untouched (body preserved for streaming).
interceptors.response.use(async (response) => {
  if (response.ok) return response

  let payload: unknown
  try {
    payload = await response.clone().json()
  } catch {
    try {
      payload = await response.clone().text()
    } catch {
      /* ignore */
    }
  }

  const message =
    (payload && typeof payload === 'object' && 'message' in (payload as Record<string, unknown>)
      ? String((payload as Record<string, unknown>).message)
      : undefined) ?? `HTTP ${response.status}`

  throw new ApiError(message, response.status, payload)
})

// Error: let AbortError pass through silently; log the rest for debugging.
interceptors.error.use((err) => {
  if (err instanceof DOMException && err.name === 'AbortError') return
  // eslint-disable-next-line no-console
  console.error('[http]', err)
})
