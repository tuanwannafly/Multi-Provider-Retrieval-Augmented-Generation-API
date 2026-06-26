import type {
  AskRequest,
  AskResponse,
  CompareRequest,
  CompareResponse,
  EvaluateRequest,
  EvaluateResponse,
  HealthResponse,
  ReadinessResponse,
  UploadResponse,
  CollectionsListResponse,
  DeleteCollectionResponse,
  ApiError,
} from './types'

const BASE = import.meta.env.VITE_API_BASE_URL || '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      ...(init?.body && !(init.body instanceof FormData)
        ? { 'Content-Type': 'application/json' }
        : {}),
      ...init?.headers,
    },
  })
  if (!resp.ok) {
    let errBody: ApiError
    try {
      errBody = (await resp.json()) as ApiError
    } catch {
      errBody = {
        error: 'UNKNOWN',
        message: `Request failed with status ${resp.status}`,
        status_code: resp.status,
      }
    }
    throw errBody
  }
  return (await resp.json()) as T
}

export const api = {
  health: () => request<HealthResponse>('/health'),
  readiness: () => request<ReadinessResponse>('/readiness'),

  uploadDocument: (file: File, collection: string, docName?: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('collection', collection)
    if (docName) form.append('doc_name', docName)
    return request<UploadResponse>('/documents/upload', {
      method: 'POST',
      body: form,
    })
  },

  listCollections: () => request<CollectionsListResponse>('/collections'),
  deleteCollection: (name: string) =>
    request<DeleteCollectionResponse>(`/collections/${name}`, { method: 'DELETE' }),

  ask: (req: AskRequest) =>
    request<AskResponse>('/ask', { method: 'POST', body: JSON.stringify(req) }),

  compare: (req: CompareRequest) =>
    request<CompareResponse>('/compare', { method: 'POST', body: JSON.stringify(req) }),

  evaluate: (req: EvaluateRequest) =>
    request<EvaluateResponse>('/evaluate', {
      method: 'POST',
      body: JSON.stringify(req),
    }),

  // SSE streaming for /ask: returns an async generator of tokens
  async *askStream(req: AskRequest): AsyncGenerator<{
    token?: string
    done?: boolean
    error?: string
    message?: string
    [key: string]: unknown
  }> {
    const resp = await fetch(`${BASE}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...req, stream: true }),
    })
    if (!resp.ok || !resp.body) {
      throw { error: 'STREAM_FAILED', message: 'Stream request failed', status_code: resp.status }
    }
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        const data = line.replace(/^data: /, '').trim()
        if (data) {
          try {
            yield JSON.parse(data)
          } catch {
            // skip malformed
          }
        }
      }
    }
  },
}
