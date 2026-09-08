import React, { useState, useEffect, useMemo } from 'react';
import { HelpCircle } from 'lucide-react';
import type { RelationshipItem, DocumentItem } from '../types';
import { api } from '../api/client';

interface RelationshipsPageProps {
  documents?: DocumentItem[];
  onSelectRelationship: (relId: string) => void;
}

type RelationshipFilter = '' | 'CORROBORATE' | 'RECONCILE' | 'CONTRADICT';

export const RelationshipsPage: React.FC<RelationshipsPageProps> = ({
  documents = [],
  onSelectRelationship,
}) => {
  const [relationships, setRelationships] = useState<RelationshipItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [typeFilter, setTypeFilter] = useState<RelationshipFilter>('');

  const docMap = useMemo(() => {
    const map: Record<string, string> = {};
    documents.forEach((d) => {
      map[d.id] = d.filename;
    });
    return map;
  }, [documents]);

  const loadRelationships = () => {
    setLoading(true);
    api.getRelationships({
      type: typeFilter || undefined,
      limit: 150,
    })
      .then((res) => setRelationships(res))
      .catch((err) => console.error('Failed to load relationships:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadRelationships();
  }, [typeFilter]);

  // Count by type
  const counts = useMemo(() => {
    const all = relationships.length;
    let corroborations = 0;
    let reconciliations = 0;
    let contradictions = 0;
    relationships.forEach((r) => {
      if (r.type === 'CORROBORATE') corroborations++;
      if (r.type === 'RECONCILE') reconciliations++;
      if (r.type === 'CONTRADICT') contradictions++;
    });
    return { all, corroborations, reconciliations, contradictions };
  }, [relationships]);

  return (
    <div className="space-y-6">
      {/* Page Title Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-stone-900">Relationships</h1>
        <p className="text-xs text-stone-500 mt-1">
          How facts across documents agree, conflict, or differ by context.
        </p>
      </div>

      {/* Filter Tabs matching reference screenshot */}
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => setTypeFilter('')}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            typeFilter === ''
              ? 'bg-black text-white'
              : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
          }`}
        >
          All ({counts.all})
        </button>

        <button
          type="button"
          onClick={() => setTypeFilter('CORROBORATE')}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            typeFilter === 'CORROBORATE'
              ? 'bg-black text-white'
              : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
          }`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          Corroborated ({counts.corroborations})
        </button>

        <button
          type="button"
          onClick={() => setTypeFilter('RECONCILE')}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            typeFilter === 'RECONCILE'
              ? 'bg-black text-white'
              : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
          }`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
          Reconciled ({counts.reconciliations})
        </button>

        <button
          type="button"
          onClick={() => setTypeFilter('CONTRADICT')}
          className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            typeFilter === 'CONTRADICT'
              ? 'bg-black text-white'
              : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
          }`}
        >
          <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
          Contradictions ({counts.contradictions})
        </button>
      </div>

      {/* Relationships 2-Column Grid */}
      {loading ? (
        <div className="py-24 text-center text-stone-400 text-sm animate-pulse">
          Loading relationships...
        </div>
      ) : relationships.length === 0 ? (
        <div className="rounded-xl border border-dashed border-stone-200 bg-white p-12 text-center space-y-2">
          <h3 className="text-sm font-semibold text-stone-900">No relationships found</h3>
          <p className="text-xs text-stone-500">
            Cross-document links are discovered automatically when comparable metrics are extracted from multiple documents.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {relationships.map((rel) => {
            const isCorroborated = rel.type === 'CORROBORATE';
            const isReconciled = rel.type === 'RECONCILE';
            const isContradiction = rel.type === 'CONTRADICT';

            // Colored border
            const borderClass = isCorroborated
              ? 'border-emerald-200 hover:border-emerald-300'
              : isReconciled
              ? 'border-amber-200 hover:border-amber-300'
              : 'border-rose-200 hover:border-rose-300';

            const docAName = rel.fact_a_doc_name || (rel.fact_a_id && docMap[rel.fact_a_id]) || 'Doc A';
            const docBName = rel.fact_b_doc_name || (rel.fact_b_id && docMap[rel.fact_b_id]) || 'Doc B';

            return (
              <div
                key={rel.id}
                onClick={() => onSelectRelationship(rel.id)}
                className={`rounded-xl border ${borderClass} bg-white p-5 shadow-sm hover:shadow transition-all cursor-pointer space-y-4 flex flex-col justify-between`}
              >
                <div className="space-y-3">
                  {/* Top Row: Pill Badge + Confidence */}
                  <div className="flex items-center justify-between">
                    {isCorroborated && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200/80">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                        CORROBORATED
                      </span>
                    )}
                    {isReconciled && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200/80">
                        <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                        RECONCILED
                      </span>
                    )}
                    {isContradiction && (
                      <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200/80">
                        <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                        CONTRADICTION
                      </span>
                    )}

                    <span className="text-xs text-stone-400 font-mono">
                      {Math.round(rel.confidence * 100)}% confidence
                    </span>
                  </div>

                  {/* Title & Subject */}
                  <div>
                    <h3 className="text-sm font-bold text-stone-900 leading-snug">
                      {rel.fact_a_predicate}
                    </h3>
                    <p className="text-xs text-stone-500 mt-0.5">
                      {rel.fact_a_subject}
                    </p>
                  </div>

                  {/* Side-by-side comparison boxes */}
                  <div className="grid grid-cols-2 gap-3 bg-stone-50/70 border border-stone-200/60 rounded-lg p-3">
                    {/* Source Fact A */}
                    <div className="min-w-0">
                      <div className="text-[10px] text-stone-400 font-mono uppercase truncate">
                        {docAName}
                      </div>
                      <div className="flex items-baseline gap-1.5 mt-1">
                        <span className="text-base font-bold text-stone-900 tracking-tight">
                          {rel.fact_a_value || '—'}
                        </span>
                        {rel.fact_a_period && (
                          <span className="text-[10px] font-mono text-stone-600 bg-white border border-stone-200 px-1 py-0.2 rounded shrink-0">
                            {rel.fact_a_period}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Source Fact B */}
                    <div className="min-w-0">
                      <div className="text-[10px] text-stone-400 font-mono uppercase truncate">
                        {docBName}
                      </div>
                      <div className="flex items-baseline gap-1.5 mt-1">
                        <span className="text-base font-bold text-stone-900 tracking-tight">
                          {rel.fact_b_value || '—'}
                        </span>
                        {rel.fact_b_period && (
                          <span className="text-[10px] font-mono text-stone-600 bg-white border border-stone-200 px-1 py-0.2 rounded shrink-0">
                            {rel.fact_b_period}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Why? Contextual Explanation */}
                  <div className="space-y-1 pt-1">
                    <div className="text-xs font-bold text-stone-700 flex items-center gap-1">
                      <HelpCircle className="w-3.5 h-3.5 text-stone-400" />
                      <span>Why?</span>
                    </div>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      {rel.reasoning || 'Candidate metrics compared across source documents.'}
                    </p>
                  </div>
                </div>

                {/* Footer Action */}
                <div className="flex justify-end pt-2 border-t border-stone-100">
                  <span className="text-xs font-semibold text-stone-800 hover:text-black flex items-center gap-1">
                    View evidence & details →
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
