import React, { useState, useEffect } from 'react';
import { AlertTriangle, Check, ArrowRight } from 'lucide-react';
import type { ReviewItem } from '../types';
import { api } from '../api/client';

interface ReviewPageProps {
  onSelectFact: (factId: string) => void;
  onSelectRelationship: (relId: string) => void;
}

export const ReviewPage: React.FC<ReviewPageProps> = ({
  onSelectFact,
  onSelectRelationship,
}) => {
  const [reviewItems, setReviewItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [severityFilter, setSeverityFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');

  const loadReview = () => {
    setLoading(true);
    api.getReview({
      severity: severityFilter || undefined,
      review_type: typeFilter || undefined,
    })
      .then((res) => setReviewItems(res))
      .catch((err) => console.error('Failed to load review queue:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadReview();
  }, [severityFilter, typeFilter]);

  return (
    <div className="space-y-6">
      {/* Page Title Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-stone-900">Review Queue</h1>
        <p className="text-xs text-stone-500 mt-1">
          Ungrounded claims, isolated extraction noise, and conflicting metrics requiring human review.
        </p>
      </div>

      {/* Honesty & Uncertainty Banner */}
      <div className="rounded-xl border border-amber-200/80 bg-amber-50/50 p-4">
        <div className="flex items-start gap-3">
          <AlertTriangle className="h-4 w-4 text-amber-700 shrink-0 mt-0.5" />
          <div className="text-xs text-amber-900 space-y-0.5">
            <div className="font-bold">Honesty &amp; Uncertainty Layer</div>
            <p className="text-amber-800 leading-relaxed">
              KnowledgeMesh deliberately rejects meaningless numbers (e.g., isolated footnote digits like &ldquo;4 FY23&rdquo;) and highlights weak evidence matches or genuine cross-report contradictions for human verification instead of hallucinating certainty.
            </p>
          </div>
        </div>
      </div>

      {/* Filter Row */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="rounded-lg border border-stone-200/80 bg-white px-3 py-1.5 text-xs text-stone-800 focus:border-stone-900 focus:outline-none transition-colors shadow-2xs"
          >
            <option value="">All Types</option>
            <option value="CONTRADICTION">Contradictions</option>
            <option value="REJECTED_FACT">Rejected Extraction Noise</option>
            <option value="UNGROUNDED">Weak Grounding</option>
            <option value="LOW_CONFIDENCE">Low Confidence</option>
          </select>

          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="rounded-lg border border-stone-200/80 bg-white px-3 py-1.5 text-xs text-stone-800 focus:border-stone-900 focus:outline-none transition-colors shadow-2xs"
          >
            <option value="">All Severities</option>
            <option value="high">High Severity</option>
            <option value="medium">Medium Severity</option>
            <option value="low">Low Severity</option>
          </select>
        </div>

        <span className="text-xs text-stone-400 font-mono">
          {reviewItems.length} items flagged
        </span>
      </div>

      {/* Review Queue Items */}
      {loading ? (
        <div className="py-24 text-center text-stone-400 text-sm animate-pulse">
          Loading review items...
        </div>
      ) : reviewItems.length === 0 ? (
        <div className="rounded-xl border border-dashed border-stone-200 bg-white p-12 text-center space-y-2">
          <Check className="mx-auto h-8 w-8 text-emerald-500 mb-2" />
          <h3 className="text-sm font-semibold text-stone-900">Review queue is empty</h3>
          <p className="text-xs text-stone-500">
            All extracted facts pass evidence grounding and consistency checks.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {reviewItems.map((item) => {
            const isHigh = item.severity === 'high';
            const isMedium = item.severity === 'medium';

            return (
              <div
                key={item.id}
                className={`rounded-xl border bg-white p-4 shadow-sm transition-all space-y-3 ${
                  isHigh ? 'border-rose-200' : isMedium ? 'border-amber-200' : 'border-stone-200/80'
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border ${
                          isHigh
                            ? 'bg-rose-50 text-rose-700 border-rose-200'
                            : isMedium
                            ? 'bg-amber-50 text-amber-800 border-amber-200'
                            : 'bg-stone-100 text-stone-600 border-stone-200'
                        }`}
                      >
                        {item.severity}
                      </span>
                      <span className="text-xs font-bold text-stone-900">{item.title}</span>
                    </div>

                    <p className="text-xs text-stone-600 leading-relaxed">
                      {item.reason}
                    </p>
                  </div>

                  {item.fact_id && (
                    <button
                      type="button"
                      onClick={() => onSelectFact(item.fact_id!)}
                      className="shrink-0 inline-flex items-center gap-1 text-xs font-semibold text-stone-800 hover:text-black transition-colors"
                    >
                      <span>Inspect Fact</span>
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  )}

                  {item.relationship_id && (
                    <button
                      type="button"
                      onClick={() => onSelectRelationship(item.relationship_id!)}
                      className="shrink-0 inline-flex items-center gap-1 text-xs font-semibold text-stone-800 hover:text-black transition-colors"
                    >
                      <span>Inspect Relationship</span>
                      <ArrowRight className="h-3 w-3" />
                    </button>
                  )}
                </div>

                <div className="flex items-center justify-between text-[11px] text-stone-400 font-mono pt-1 border-t border-stone-100">
                  <span>Type: {item.review_type}</span>
                  {item.document_filename && <span>{item.document_filename}</span>}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
