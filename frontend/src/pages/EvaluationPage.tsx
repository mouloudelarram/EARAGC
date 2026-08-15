import { BarChart2, Info } from 'lucide-react'
import type { EvaluationResult } from '../types'

// Placeholder data — will be replaced with real evaluation results in Phase 11
const METHODS: EvaluationResult[] = [
  { method: 'Vector Search', recall_at_5: 0, precision_at_5: 0, mrr: 0, avg_latency_ms: 0 },
  { method: 'BM25', recall_at_5: 0, precision_at_5: 0, mrr: 0, avg_latency_ms: 0 },
  { method: 'Hybrid', recall_at_5: 0, precision_at_5: 0, mrr: 0, avg_latency_ms: 0 },
  { method: 'Hybrid + Reranker', recall_at_5: 0, precision_at_5: 0, mrr: 0, avg_latency_ms: 0 },
]

function MetricCell({ value, isHighlighted }: { value: number; isHighlighted?: boolean }) {
  const display = value === 0 ? '—' : value.toFixed(3)
  return (
    <td className={`px-4 py-3 text-sm text-right font-mono ${
      isHighlighted ? 'text-blue-600 font-semibold' : 'text-gray-600'
    }`}>
      {display}
    </td>
  )
}

export default function EvaluationPage() {
  return (
    <div className="p-6 max-w-5xl mx-auto space-y-6">
      {/* Info banner */}
      <div className="flex items-start gap-3 p-4 bg-blue-50 border border-blue-200 rounded-xl text-sm text-blue-800">
        <Info className="w-4 h-4 mt-0.5 flex-shrink-0" />
        <div>
          <p className="font-medium">Evaluation coming in Phase 11</p>
          <p className="text-blue-600 mt-0.5">
            Run <code className="bg-blue-100 px-1 rounded text-xs">docker compose exec backend python scripts/evaluate.py</code> to generate real results.
          </p>
        </div>
      </div>

      {/* Metrics table */}
      <div className="card overflow-hidden">
        <div className="flex items-center gap-2 px-5 py-4 border-b border-gray-100">
          <BarChart2 className="w-4 h-4 text-gray-400" />
          <h2 className="text-sm font-semibold text-gray-900">Retrieval Comparison</h2>
          <span className="ml-auto text-xs text-gray-400">30 eval questions</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Method</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Recall@5</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Precision@5</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">MRR</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Latency</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {METHODS.map((row, idx) => (
                <tr key={row.method} className={idx === METHODS.length - 1 ? 'bg-blue-50/30' : ''}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">
                    {row.method}
                    {idx === METHODS.length - 1 && (
                      <span className="ml-2 text-[10px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full font-medium">Default</span>
                    )}
                  </td>
                  <MetricCell value={row.recall_at_5} isHighlighted={idx === METHODS.length - 1} />
                  <MetricCell value={row.precision_at_5} isHighlighted={idx === METHODS.length - 1} />
                  <MetricCell value={row.mrr} isHighlighted={idx === METHODS.length - 1} />
                  <MetricCell value={row.avg_latency_ms} />
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Generation metrics */}
      <div className="card overflow-hidden">
        <div className="flex items-center gap-2 px-5 py-4 border-b border-gray-100">
          <h2 className="text-sm font-semibold text-gray-900">Generation Quality</h2>
        </div>
        <div className="grid grid-cols-3 divide-x divide-gray-100">
          {[
            { label: 'Faithfulness', value: '—', desc: 'Answer is grounded in context' },
            { label: 'Answer Relevance', value: '—', desc: 'Answer addresses the question' },
            { label: 'P95 Latency', value: '—', desc: 'End-to-end response time' },
          ].map(({ label, value, desc }) => (
            <div key={label} className="p-5">
              <p className="text-2xl font-bold text-gray-300 font-mono">{value}</p>
              <p className="text-sm font-medium text-gray-700 mt-1">{label}</p>
              <p className="text-xs text-gray-400 mt-0.5">{desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Methodology */}
      <div className="card p-5 space-y-3">
        <h2 className="text-sm font-semibold text-gray-900">Evaluation Methodology</h2>
        <div className="text-xs text-gray-600 space-y-2 leading-relaxed">
          <p>
            <strong>Retrieval metrics</strong> are computed against 30 hand-labeled questions with known relevant documents.
            Recall@5 measures what fraction of relevant documents appear in the top 5 results.
            MRR (Mean Reciprocal Rank) rewards finding the best document at a higher rank.
          </p>
          <p>
            <strong>Generation metrics</strong> evaluate whether the LLM answer is grounded in the retrieved context (faithfulness)
            and whether it actually answers the question (relevance).
          </p>
          <p>
            <strong>Latency</strong> includes embedding time, retrieval, reranking, and LLM generation.
            Measured on a standard developer laptop with CPU inference.
          </p>
        </div>
      </div>
    </div>
  )
}

