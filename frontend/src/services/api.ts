// ================================
// API Service — communicates with FastAPI backend
// ================================

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface HealthResponse {
  status: string
  timestamp: string
  version: string
  environment: Record<string, string | number>
  services: Record<string, { status: string; detail?: string }>
}

export interface QueryRequest {
  question: string
  top_k?: number
}

export interface Source {
  id: number
  document: string
  section: string | null
  page: number | null
}

export interface QueryResponse {
  answer: string
  sources: Source[]
  metadata: {
    retrieval_method: string
    candidates: number
    reranked: number
    retrieval_latency_ms: number
    generation_latency_ms: number
  }
}

export interface DocumentInfo {
  id: string
  filename: string
  document_type: string
  chunk_count: number
  created_at: string
  source: string | null
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }))
    throw new Error(error.detail ?? `HTTP ${response.status}`)
  }
  return response.json()
}

// ─── API Functions ────────────────────────────────────────────────────────────

export const api = {
  /** Check the health of the backend API. */
  health: (): Promise<HealthResponse> => request('/health'),

  /** Send a query to the RAG pipeline. */
  query: (body: QueryRequest): Promise<QueryResponse> =>
    request('/query', { method: 'POST', body: JSON.stringify(body) }),

  /** Upload a document. */
  uploadDocument: async (file: File): Promise<DocumentInfo> => {
    const formData = new FormData()
    formData.append('file', file)
    const response = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(error.detail ?? `HTTP ${response.status}`)
    }
    return response.json()
  },

  /** List all uploaded documents. */
  listDocuments: (): Promise<DocumentInfo[]> => request('/documents'),

  /** Delete a document by ID. */
  deleteDocument: (id: string): Promise<void> =>
    request(`/documents/${id}`, { method: 'DELETE' }),
}

