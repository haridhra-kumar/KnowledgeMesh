import React, { useState, useEffect } from 'react';
import { X, Quote, HelpCircle, Calendar, Building } from 'lucide-react';
import type { RelationshipItem } from '../types';
import { StatusBadge } from './StatusBadge';
import { api } from '../api/client';

interface RelationshipDetailModalProps {
  relationshipId: string | null;
  onClose: () => void;
  onSelectFact?: (factId: string) => void;
}

export const RelationshipDetailModal: React.FC<RelationshipDetailModalProps> = ({
  relationshipId,
  onClose,
  onSelectFact,
}) => {
  const [relationship, setRelationship] = useState<RelationshipItem | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (relationshipId) {
      setLoading(true);
      api.getRelationship(relationshipId)
        .then((res) => setRelationship(res))
        .catch((err) => console.error('Failed to load relationship details:', err))
        .finally(() => setLoading(false));
    } else {
      setRelationship(null);
    }
  }, [relationshipId]);

  if (!relationshipId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="w-full max-w-4xl rounded-xl border border-stone-200 bg-white p-6 shadow-xl transition-all my-8 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-stone-100 pb-4 shrink-0">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold uppercase tracking-wider text-stone-400">Cross-Document Relationship</span>
            {relationship && <StatusBadge status={relationship.type} size="md" />}
            {relationship && (
              <span className="text-xs bg-stone-100 text-stone-700 px-2.5 py-1 rounded-full font-mono font-medium">
                {Math.round(relationship.confidence * 100)}% Confidence
              </span>
            )}
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-stone-400 hover:bg-stone-100 hover:text-stone-600 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Body */}
        {loading || !relationship ? (
          <div className="py-20 text-center text-stone-400 text-sm animate-pulse">Loading cross-document analysis...</div>
        ) : (
          <div className="flex-1 overflow-y-auto pt-4 space-y-6 pr-1">
            {/* Why Are These Related? Reasoning Card */}
            <div className={`rounded-xl border p-5 ${
              relationship.type === 'CORROBORATE'
                ? 'bg-emerald-50/50 border-emerald-200/80'
                : relationship.type === 'CONTRADICT'
                ? 'bg-rose-50/50 border-rose-200/80'
                : 'bg-amber-50/50 border-amber-200/80'
            }`}>
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-stone-800 mb-2">
                <HelpCircle className="h-4 w-4 text-stone-600" />
                Why are these facts classified as {relationship.type}?
              </div>
              <p className="text-sm font-medium text-stone-900 leading-relaxed bg-white p-3.5 rounded-lg border border-stone-200/80 shadow-2xs">
                {relationship.reasoning}
              </p>
            </div>

            {/* Side-by-Side Comparison (Fact A vs Fact B) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Fact A */}
              <div className="rounded-xl border border-stone-200/80 bg-white p-5 shadow-sm flex flex-col justify-between space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                    <span className="text-xs font-bold text-stone-400 uppercase tracking-wider">Fact A</span>
                    <span className="text-xs text-stone-500 font-mono">{relationship.fact_a_doc_name}</span>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <div className="text-[11px] text-stone-400 flex items-center gap-1 mb-0.5">
                        <Building className="h-3 w-3" /> Entity &amp; Metric
                      </div>
                      <div className="text-sm font-bold text-stone-900">
                        {relationship.fact_a_subject} — <span className="font-normal text-stone-600 capitalize">{relationship.fact_a_predicate}</span>
                      </div>
                    </div>

                    <div>
                      <div className="text-[11px] text-stone-400 mb-0.5">Reported Value</div>
                      <div className="text-xl font-bold text-stone-900">{relationship.fact_a_value}</div>
                    </div>

                    {relationship.fact_a_period && (
                      <div>
                        <div className="text-[11px] text-stone-400 flex items-center gap-1 mb-0.5">
                          <Calendar className="h-3 w-3" /> Period
                        </div>
                        <div className="text-xs font-mono font-bold text-stone-800">{relationship.fact_a_period}</div>
                      </div>
                    )}

                    <div>
                      <div className="text-[11px] text-stone-400 flex items-center gap-1 mb-1">
                        <Quote className="h-3 w-3" /> Evidence Quote
                      </div>
                      <p className="text-xs italic text-stone-700 bg-stone-50/70 p-2.5 rounded-lg border border-stone-100 leading-relaxed">
                        &ldquo;{relationship.fact_a?.evidence_quote || 'Exact quote from source page.'}&rdquo;
                      </p>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-500">
                  <span className="font-mono text-[11px]">Page {relationship.fact_a_page || 1}</span>
                  {relationship.fact_a_id && onSelectFact && (
                    <button
                      type="button"
                      onClick={() => onSelectFact(relationship.fact_a_id)}
                      className="text-xs text-stone-800 hover:text-black font-semibold"
                    >
                      Inspect Full Fact →
                    </button>
                  )}
                </div>
              </div>

              {/* Fact B */}
              <div className="rounded-xl border border-stone-200/80 bg-white p-5 shadow-sm flex flex-col justify-between space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                    <span className="text-xs font-bold text-stone-400 uppercase tracking-wider">Fact B</span>
                    <span className="text-xs text-stone-500 font-mono">{relationship.fact_b_doc_name}</span>
                  </div>

                  <div className="space-y-3">
                    <div>
                      <div className="text-[11px] text-stone-400 flex items-center gap-1 mb-0.5">
                        <Building className="h-3 w-3" /> Entity &amp; Metric
                      </div>
                      <div className="text-sm font-bold text-stone-900">
                        {relationship.fact_b_subject} — <span className="font-normal text-stone-600 capitalize">{relationship.fact_b_predicate}</span>
                      </div>
                    </div>

                    <div>
                      <div className="text-[11px] text-stone-400 mb-0.5">Reported Value</div>
                      <div className="text-xl font-bold text-stone-900">{relationship.fact_b_value}</div>
                    </div>

                    {relationship.fact_b_period && (
                      <div>
                        <div className="text-[11px] text-stone-400 flex items-center gap-1 mb-0.5">
                          <Calendar className="h-3 w-3" /> Period
                        </div>
                        <div className="text-xs font-mono font-bold text-stone-800">{relationship.fact_b_period}</div>
                      </div>
                    )}

                    <div>
                      <div className="text-[11px] text-stone-400 flex items-center gap-1 mb-1">
                        <Quote className="h-3 w-3" /> Evidence Quote
                      </div>
                      <p className="text-xs italic text-stone-700 bg-stone-50/70 p-2.5 rounded-lg border border-stone-100 leading-relaxed">
                        &ldquo;{relationship.fact_b?.evidence_quote || 'Exact quote from source page.'}&rdquo;
                      </p>
                    </div>
                  </div>
                </div>

                <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs text-stone-500">
                  <span className="font-mono text-[11px]">Page {relationship.fact_b_page || 1}</span>
                  {relationship.fact_b_id && onSelectFact && (
                    <button
                      type="button"
                      onClick={() => onSelectFact(relationship.fact_b_id)}
                      className="text-xs text-stone-800 hover:text-black font-semibold"
                    >
                      Inspect Full Fact →
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
