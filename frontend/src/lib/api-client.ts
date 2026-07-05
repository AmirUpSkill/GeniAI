import { env } from './env'

type ApiClientOptions = {
  body?: unknown
  method?: 'DELETE' | 'GET' | 'PATCH' | 'POST'
}

export async function apiClient<TData>(
  path: string,
  options: ApiClientOptions = {},
): Promise<TData> {
  const response = await fetch(new URL(path, env.VITE_API_BASE_URL), {
    body: options.body === undefined ? undefined : JSON.stringify(options.body),
    credentials: 'include',
    headers: {
      Accept: 'application/json',
      ...(options.body === undefined ? {} : { 'Content-Type': 'application/json' }),
    },
    method: options.method ?? 'GET',
  })

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`)
  }

  return response.json() as Promise<TData>
}
