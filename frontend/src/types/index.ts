// ================================
// Shared TypeScript types
// ================================

export type DocumentType =
  | 'pdf'
  | 'markdown'
  | 'text'
  | 'yaml'
  | 'json'
  | 'terraform'
  | 'unknown'

export interface Document {
  id: string
  filename: string
  document_type: DocumentType
  chunk_count: number
  created_at: string
  source: string | null
}

export interface Source {
  id: number
  document: string
  section: string | null
  page: number | null
  content?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  metadata?: {
    retrieval_method: string
    candidates: number
    reranked: number
    retrieval_latency_ms: number
    generation_latency_ms: number
  }
  timestamp: Date
}

export interface EvaluationResult {
  method: string
  recall_at_5: number
  precision_at_5: number
  mrr: number
  avg_latency_ms: number
}

