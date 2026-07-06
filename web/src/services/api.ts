import type {
  HealthResponse,
  ReadinessResponse,
  UploadResponse,
  CollectionsResponse,
  DeleteCollectionResponse,
  AskRequest,
  AskResponse,
  CompareRequest,
  CompareResponse,
  EvaluateRequest,
  EvaluateResponse,
} from '@/types/api'

const API_BASE_URL = '/api' // New base URL for business endpoints

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: 'INTERNAL_ERROR',
      message: 'An unexpected error occurred',
      status_code: response.status,
    }))
    throw new Error(error.message || 'Request failed')
  }
  return response.json()
}

export const api = {
  async health() {
    // Health endpoint remains at root
    const response = await fetch(`/health`)
    return handleResponse<HealthResponse>(response)
  },

  async readiness() {
    // Readiness endpoint remains at root
    const response = await fetch(`/readiness`)
    return handleResponse<ReadinessResponse>(response)
  },

  async upload(file: File, collection: string, doc_name?: string) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('collection', collection)
    if (doc_name) formData.append('doc_name', doc_name)

    const response = await fetch(`${API_BASE_URL}/documents/upload`, {
      method: 'POST',
      body: formData,
    })
    return handleResponse<UploadResponse>(response)
  },

  async getCollections() {
    const response = await fetch(`${API_BASE_URL}/collections`)
    return handleResponse<CollectionsResponse>(response)
  },

  async deleteCollection(name: string) {
    const response = await fetch(`${API_BASE_URL}/collections/${name}`, {
      method: 'DELETE',
    })
    return handleResponse<DeleteCollectionResponse>(response)
  },

  async ask(data: AskRequest) {
    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return handleResponse<AskResponse>(response)
  },

  async askStream(data: AskRequest, onToken: (token: string) => void) {
    const response = await fetch(`${API_BASE_URL}/ask`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...data, stream: true }),
    })

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.message || 'Streaming failed')
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No response body')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('
')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6))
          if (data.token) {
            onToken(data.token)
          }
        }
      }
    }
  },

  async compare(data: CompareRequest) {
    const response = await fetch(`${API_BASE_URL}/compare`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return handleResponse<CompareResponse>(response)
  },

  async evaluate(data: EvaluateRequest) {
    const response = await fetch(`${API_BASE_URL}/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    })
    return handleResponse<EvaluateResponse>(response)
  },
}
