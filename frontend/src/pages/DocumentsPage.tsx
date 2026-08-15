import { useState, useCallback } from 'react'
import { Upload, FileText, Trash2, AlertCircle, CheckCircle, Loader2, File } from 'lucide-react'
import { api } from '../services/api'
import type { Document } from '../types'

const SUPPORTED_FORMATS = ['.pdf', '.md', '.txt', '.json', '.yaml', '.yml', '.tf']

const TYPE_COLORS: Record<string, string> = {
  pdf: 'bg-red-100 text-red-700',
  markdown: 'bg-blue-100 text-blue-700',
  text: 'bg-gray-100 text-gray-700',
  yaml: 'bg-green-100 text-green-700',
  json: 'bg-yellow-100 text-yellow-700',
  terraform: 'bg-purple-100 text-purple-700',
  unknown: 'bg-gray-100 text-gray-500',
}

function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

interface UploadState {
  status: 'idle' | 'uploading' | 'success' | 'error'
  message?: string
}

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [uploadState, setUploadState] = useState<UploadState>({ status: 'idle' })
  const [isDragging, setIsDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  // Load documents on mount
  useState(() => {
    loadDocuments()
  })

  async function loadDocuments() {
    setLoading(true)
    try {
      const docs = await api.listDocuments()
      setDocuments(docs as Document[])
    } catch {
      // Documents endpoint not yet implemented — show empty state
      setDocuments([])
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return
    const file = files[0]

    setUploadState({ status: 'uploading' })
    try {
      const doc = await api.uploadDocument(file)
      setDocuments(prev => [doc as Document, ...prev])
      setUploadState({ status: 'success', message: `"${file.name}" uploaded successfully.` })
      setTimeout(() => setUploadState({ status: 'idle' }), 4000)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Upload failed'
      setUploadState({ status: 'error', message })
    }
  }

  const handleDelete = async (id: string, filename: string) => {
    if (!confirm(`Delete "${filename}"? This will remove all its indexed chunks.`)) return
    setDeletingId(id)
    try {
      await api.deleteDocument(id)
      setDocuments(prev => prev.filter(d => d.id !== id))
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Delete failed')
    } finally {
      setDeletingId(null)
    }
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    handleUpload(e.dataTransfer.files)
  }, [])

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        className={`border-2 border-dashed rounded-2xl p-10 text-center transition-colors ${
          isDragging ? 'border-blue-400 bg-blue-50' : 'border-gray-200 bg-white hover:border-gray-300'
        }`}
      >
        <div className="flex flex-col items-center gap-3">
          <div className="w-14 h-14 bg-blue-50 rounded-full flex items-center justify-center">
            <Upload className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <p className="text-sm font-medium text-gray-900">
              Drag & drop your document here, or{' '}
              <label className="text-blue-600 cursor-pointer hover:underline">
                browse
                <input
                  type="file"
                  className="hidden"
                  accept={SUPPORTED_FORMATS.join(',')}
                  onChange={(e) => handleUpload(e.target.files)}
                />
              </label>
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Supported formats: {SUPPORTED_FORMATS.join(' ')} — Max 10 MB
            </p>
          </div>
        </div>
      </div>

      {/* Upload status */}
      {uploadState.status !== 'idle' && (
        <div className={`mt-4 flex items-center gap-2 p-3 rounded-lg text-sm ${
          uploadState.status === 'uploading' ? 'bg-blue-50 text-blue-700' :
          uploadState.status === 'success' ? 'bg-green-50 text-green-700' :
          'bg-red-50 text-red-700'
        }`}>
          {uploadState.status === 'uploading' && <Loader2 className="w-4 h-4 animate-spin" />}
          {uploadState.status === 'success' && <CheckCircle className="w-4 h-4" />}
          {uploadState.status === 'error' && <AlertCircle className="w-4 h-4" />}
          <span>
            {uploadState.status === 'uploading' ? 'Uploading and indexing document...' : uploadState.message}
          </span>
        </div>
      )}

      {/* Document list */}
      <div className="mt-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-semibold text-gray-900">
            Indexed Documents
            {documents.length > 0 && (
              <span className="ml-2 text-xs font-normal text-gray-400">({documents.length})</span>
            )}
          </h2>
          <button
            onClick={loadDocuments}
            className="btn-secondary text-xs"
            disabled={loading}
          >
            {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : 'Refresh'}
          </button>
        </div>

        {loading && documents.length === 0 ? (
          <div className="flex items-center justify-center py-16 text-gray-400">
            <Loader2 className="w-6 h-6 animate-spin mr-2" />
            <span className="text-sm">Loading documents...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="card py-16 text-center">
            <File className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-sm font-medium text-gray-500">No documents indexed yet</p>
            <p className="text-xs text-gray-400 mt-1">Upload your architecture docs, ADRs, or API specs above</p>
          </div>
        ) : (
          <div className="card divide-y divide-gray-100 overflow-hidden">
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center gap-4 px-5 py-4 hover:bg-gray-50 transition-colors">
                <FileText className="w-5 h-5 text-gray-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 truncate">{doc.filename}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{formatDate(doc.created_at)}</p>
                </div>
                <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full flex-shrink-0 ${
                  TYPE_COLORS[doc.document_type] ?? TYPE_COLORS.unknown
                }`}>
                  {doc.document_type}
                </span>
                <span className="text-xs text-gray-400 flex-shrink-0">
                  {doc.chunk_count} chunk{doc.chunk_count !== 1 ? 's' : ''}
                </span>
                <button
                  onClick={() => handleDelete(doc.id, doc.filename)}
                  disabled={deletingId === doc.id}
                  className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors flex-shrink-0"
                  title="Delete document"
                >
                  {deletingId === doc.id
                    ? <Loader2 className="w-4 h-4 animate-spin" />
                    : <Trash2 className="w-4 h-4" />
                  }
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

