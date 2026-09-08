import React, { useState, useEffect } from 'react';
import { X, Quote, FileText, Calendar, Building, Layers, Link as LinkIcon, Code } from 'lucide-react';
import type { FactItem } from '../types';
import { StatusBadge } from './StatusBadge';
import { api } from '../api/client';

interface FactDetailModalProps {
  factId: string | null;
  onClose: () => void;
  onSelectRelationship?: (relId: string) => void;
}

export const FactDetailModal: React.FC<FactDetailModalProps> = ({
  factId,
  onClose,
  onSelectRelationship,
}) => {
  const [fact, setFact] = useState<FactItem | null>(null);
  const [loading, setLoading] = useState(false);
  const [showJson, setShowJson] = useState(false);

  useEffect(() => {
    if (factId) {
      setLoading(true);
      api.getFact(factId)
        .then((res) => setFact(res))
        .catch((err) => console.error('Failed to load fact details:', err))
        .finally(() => setLoading(false));
    } else {
      setFact(null);
    }
  }, [factId]);

  if (!factId) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-xs p-4 overflow-y-auto">
      <div className="w-full max-w-2xl rounded-xl border border-stone-200 bg-white p-6 shadow-xl transition-all my-8 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-stone-100 pb-4 shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-bold uppercase tracking-wider text-stone-400">Fact Details</span>
            {fact && <StatusBadge status={fact.grounding_status} size="sm" />}
            {fact && (
              <span className="text-xs bg-stone-100 text-stone-600 px-2 py-0.5 rounded-full font-mono">
                {Math.round(fact.confidence * 100)}% Conf
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

        {/* Content */}
        {loading || !fact ? (
          <div className="py-20 text-center text-stone-400 text-sm animate-pulse">Loading fact evidence...</div>
        ) : (
          <div className="flex-1 overflow-y-auto pt-4 space-y-6 pr-1">
            {/* Primary Fact Card */}
            <div className="rounded-xl border border-stone-200/80 bg-stone-50/50 p-5">
              <div className="flex items-center justify-between text-xs text-stone-500 mb-1">
                <span className="flex items-center gap-1.5 font-semibold text-stone-800">
                  <Building className="h-3.5 w-3.5 text-stone-400" />
                  {fact.subject}
                </span>
                <span className="capitalize font-mono bg-white px-2 py-0.5 rounded border border-stone-200 text-stone-600">
                  {fact.fact_type.replace('_', ' ')}
                </span>
              </div>
              <div className="mt-2 text-2xl font-bold text-stone-900 flex items-baseline gap-2">
                <span>{fact.value}</span>
                <span className="text-sm font-normal text-stone-500 capitalize">({fact.predicate})</span>
              </div>
              {fact.period && (
                <div className="mt-2 flex items-center gap-1 text-xs text-stone-600 font-medium">
                  <Calendar className="h-3.5 w-3.5 text-stone-400" />
                  Period: <span className="text-stone-900 font-mono font-bold">{fact.period}</span>
                  {fact.scope && <span className="text-stone-400 ml-2">Scope: {fact.scope}</span>}
                </div>
              )}
            </div>

            {/* Source Evidence (Prominent) */}
            <div className="rounded-xl border border-stone-200 bg-stone-50/70 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-stone-700">
                  <Quote className="h-3.5 w-3.5 text-stone-500" />
                  Exact Source Evidence
                </div>
                <div className="text-xs text-emerald-700 font-medium bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                  Grounding Match: {(fact.grounding_score * 100).toFixed(1)}%
                </div>
              </div>
              <p className="text-sm italic text-stone-800 leading-relaxed bg-white p-3 rounded-lg border border-stone-200/80 shadow-2xs">
                &ldquo;{fact.evidence_quote}&rdquo;
              </p>
              <div className="flex items-center justify-between text-xs text-stone-500 pt-1">
                <div className="flex items-center gap-1.5 font-mono">
                  <FileText className="h-3.5 w-3.5 text-stone-400" />
                  <span className="font-medium text-stone-700">{fact.document_filename || 'Source Document'}</span>
                  <span className="text-stone-300">•</span>
                  <span>Page {fact.page_number}</span>
                </div>
                {fact.document_filename && (
                  <a
                    href={`/files/${fact.document_filename}`}
                    target="_blank"
                    rel="noreferrer"
                    className="text-stone-800 hover:text-black font-semibold text-xs flex items-center gap-1"
                  >
                    View PDF <LinkIcon className="h-3 w-3" />
                  </a>
                )}
              </div>
            </div>

            {/* Normalization & Contextual Qualifiers */}
            <div className="grid grid-cols-2 gap-4">
              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <div className="text-xs font-bold text-stone-400 mb-2 uppercase tracking-wider">Normalized Values</div>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="text-stone-500">Normalized Value:</span>
                    <span className="font-mono font-medium text-stone-900">
                      {fact.normalized_value !== null && fact.normalized_value !== undefined
                        ? Number(fact.normalized_value).toLocaleString()
                        : 'Unscaled'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-500">Normalized Unit:</span>
                    <span className="font-mono font-medium text-stone-900">{fact.normalized_unit || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-stone-500">Detected Currency:</span>
                    <span className="font-mono font-medium text-stone-900">{fact.currency || 'None'}</span>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-stone-200 bg-white p-4">
                <div className="text-xs font-bold text-stone-400 mb-2 uppercase tracking-wider">Concept Cluster</div>
                {fact.cluster ? (
                  <div className="text-xs space-y-1">
                    <p className="font-semibold text-stone-900">{fact.cluster.display_name}</p>
                    <p className="text-stone-500">{fact.cluster.description}</p>
                    <p className="text-stone-400 text-[11px] pt-1 font-mono">
                      {fact.cluster.fact_count} facts across {fact.cluster.source_doc_count} source documents
                    </p>
                  </div>
                ) : (
                  <p className="text-xs text-stone-400 italic">No cluster assigned</p>
                )}
              </div>
            </div>

            {/* Cross-Document Relationships */}
            {fact.relationships && fact.relationships.length > 0 && (
              <div>
                <div className="text-xs font-bold text-stone-400 mb-2 uppercase tracking-wider flex items-center gap-1.5">
                  <Layers className="h-3.5 w-3.5" />
                  Cross-Document Relationships ({fact.relationships.length})
                </div>
                <div className="space-y-2">
                  {fact.relationships.map((rel: any) => {
                    const isFactA = rel.fact_a_id === fact.id;
                    const otherSubject = isFactA ? rel.fact_b_subject : rel.fact_a_subject;
                    const otherValue = isFactA ? rel.fact_b_value : rel.fact_a_value;

                    return (
                      <div
                        key={rel.id}
                        onClick={() => onSelectRelationship && onSelectRelationship(rel.id)}
                        className="cursor-pointer rounded-lg border border-stone-200 bg-white p-3 hover:border-stone-400 hover:shadow-xs transition-all text-xs flex items-center justify-between"
                      >
                        <div className="flex items-center gap-2">
                          <StatusBadge status={rel.type} size="sm" />
                          <span className="font-medium text-stone-800">
                            with {otherSubject} ({otherValue})
                          </span>
                        </div>
                        <span className="text-stone-400 font-mono text-[11px]">{Math.round(rel.confidence * 100)}%</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* JSON Inspector Toggle */}
            <div className="pt-2 border-t border-stone-100">
              <button
                type="button"
                onClick={() => setShowJson(!showJson)}
                className="text-xs text-stone-400 hover:text-stone-600 flex items-center gap-1 transition-colors"
              >
                <Code className="h-3.5 w-3.5" />
                {showJson ? 'Hide Raw Fact Object' : 'Inspect Raw Fact Object'}
              </button>
              {showJson && (
                <pre className="mt-2 p-3 bg-stone-900 text-stone-200 text-[11px] rounded-lg overflow-x-auto font-mono max-h-48">
                  {JSON.stringify(fact, null, 2)}
                </pre>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
