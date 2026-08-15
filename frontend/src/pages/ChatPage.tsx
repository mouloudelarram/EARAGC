import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, ChevronDown, ChevronUp, Loader2, AlertCircle } from 'lucide-react'
import { api } from '../services/api'
import type { ChatMessage } from '../types'

function generateId(): string {
  return Math.random().toString(36).substring(2, 11)
}

interface SourceCardProps {
  sources: ChatMessage['sources']
}

function SourceList({ sources }: SourceCardProps) {
  const [expanded, setExpanded] = useState(false)
  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-3 border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-3 py-2 bg-gray-50 text-xs font-medium text-gray-600 hover:bg-gray-100 transition-colors"
      >
        <span>Sources ({sources.length})</span>
        {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
      </button>
      {expanded && (
        <div className="divide-y divide-gray-100">
          {sources.map((source) => (
            <div key={source.id} className="px-3 py-2 text-xs text-gray-600">
              <span className="font-semibold text-blue-600">[{source.id}]</span>{' '}
              <span className="font-medium">{source.document}</span>
              {source.section && <span className="text-gray-400"> — {source.section}</span>}
              {source.page && <span className="text-gray-400"> (p. {source.page})</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

interface MetaBadgeProps {
  metadata: ChatMessage['metadata']
}

function MetaBadge({ metadata }: MetaBadgeProps) {
  if (!metadata) return null
  const total = metadata.retrieval_latency_ms + metadata.generation_latency_ms
  return (
    <div className="mt-2 flex flex-wrap gap-2">
      {[
        { label: 'Method', value: metadata.retrieval_method },
        { label: 'Candidates', value: String(metadata.candidates) },
        { label: 'Reranked', value: String(metadata.reranked) },
        { label: 'Latency', value: `${total}ms` },
      ].map(({ label, value }) => (
        <span key={label} className="inline-flex items-center gap-1 text-[10px] bg-gray-100 text-gray-500 rounded px-1.5 py-0.5">
          <span className="font-medium text-gray-400">{label}:</span> {value}
        </span>
      ))}
    </div>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: generateId(),
      role: 'assistant',
      content: "Hello! I'm your Enterprise Architecture Copilot. Upload your technical documentation in the **Documents** tab, then ask me anything about your architecture — ADRs, service dependencies, technology decisions, security policies, and more.",
      timestamp: new Date(),
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  const handleSubmit = async () => {
    const question = input.trim()
    if (!question || loading) return

    setInput('')
    setError(null)

    const userMsg: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: question,
      timestamp: new Date(),
    }
    setMessages(prev => [...prev, userMsg])
    setLoading(true)

    try {
      const response = await api.query({ question, top_k: 5 })
      const assistantMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
        metadata: response.metadata,
        timestamp: new Date(),
      }
      setMessages(prev => [...prev, assistantMsg])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to get answer'
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}
          >
            {/* Avatar */}
            <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
              msg.role === 'user' ? 'bg-blue-600' : 'bg-gray-700'
            }`}>
              {msg.role === 'user'
                ? <User className="w-4 h-4 text-white" />
                : <Bot className="w-4 h-4 text-white" />
              }
            </div>

            {/* Bubble */}
            <div className={`max-w-2xl ${msg.role === 'user' ? 'items-end' : 'items-start'} flex flex-col`}>
              <div className={`rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white rounded-tr-sm'
                  : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm'
              }`}>
                {/* Render simple markdown-like content */}
                {msg.content.split('\n').map((line, i) => (
                  <p key={i} className={line === '' ? 'mt-2' : ''}>{line}</p>
                ))}
              </div>

              {/* Sources */}
              {msg.role === 'assistant' && <SourceList sources={msg.sources} />}

              {/* Metadata */}
              {msg.role === 'assistant' && <MetaBadge metadata={msg.metadata} />}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gray-700 flex items-center justify-center flex-shrink-0">
              <Bot className="w-4 h-4 text-white" />
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
              <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
            </div>
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
            <AlertCircle className="w-4 h-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="flex gap-3 items-end max-w-4xl mx-auto">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your architecture... (Enter to send, Shift+Enter for new line)"
            rows={1}
            className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent placeholder-gray-400"
            style={{ minHeight: '48px', maxHeight: '160px' }}
            disabled={loading}
          />
          <button
            onClick={handleSubmit}
            disabled={!input.trim() || loading}
            className="btn-primary rounded-xl w-12 h-12 p-0 flex items-center justify-center flex-shrink-0"
          >
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </div>
        <p className="text-center text-[11px] text-gray-400 mt-2">
          Answers are grounded in your uploaded documents. Always verify important decisions.
        </p>
      </div>
    </div>
  )
}

