import { env } from './env'

type ApiClientOptions = {
  body?: FormData | unknown
  method?: 'DELETE' | 'GET' | 'PATCH' | 'POST'
}

export class ApiError extends Error {
  readonly status: number
  readonly code?: string

  constructor(message: string, status: number, code?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

export async function apiClient<TData>(
  path: string,
  options: ApiClientOptions = {},
): Promise<TData> {
  const isFormData = options.body instanceof FormData
  let requestBody: BodyInit | undefined
  if (options.body instanceof FormData) {
    requestBody = options.body
  } else if (options.body !== undefined) {
    requestBody = JSON.stringify(options.body)
  }

  const response = await fetch(new URL(path, env.VITE_API_BASE_URL), {
    body: requestBody,
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(options.body === undefined || isFormData
        ? {}
        : { 'Content-Type': 'application/json' }),
    },
    method: options.method ?? 'GET',
  })

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      error?: { code?: string; message?: string }
    } | null
    throw new ApiError(
      payload?.error?.message ?? `Request failed with status ${response.status}`,
      response.status,
      payload?.error?.code,
    )
  }

  return response.json() as Promise<TData>
}
