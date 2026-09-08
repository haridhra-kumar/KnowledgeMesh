import React, { useState, useEffect, useMemo } from 'react';
import { Search, FileText, X } from 'lucide-react';
import type { FactItem, DocumentItem } from '../types';
import { api } from '../api/client';

interface FactsPageProps {
  documents?: DocumentItem[];
  onSelectFact: (factId: string) => void;
  selectedDocId?: string | null;
  onClearDocFilter?: () => void;
}

type FilterTab = 'all' | 'verified' | 'review' | 'unverified';

export const FactsPage: React.FC<FactsPageProps> = ({
  documents = [],
  onSelectFact,
  selectedDocId,
  onClearDocFilter,
}) => {
  const [facts, setFacts] = useState<FactItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState<FilterTab>('all');

  const docMap = useMemo(() => {
    const map: Record<string, string> = {};
    documents.forEach((d) => {
      map[d.id] = d.filename;
    });
    return map;
  }, [documents]);

  const loadFacts = () => {
    setLoading(true);
    let groundingStatus: string | undefined;
    let minConfidence: number | undefined;

    if (activeTab === 'verified') {
      groundingStatus = 'VERIFIED';
      minConfidence = 0.85;
    } else if (activeTab === 'review') {
      groundingStatus = 'PARTIAL';
    } else if (activeTab === 'unverified') {
      groundingStatus = 'UNVERIFIED';
    }

    api.getFacts({
      document_id: selectedDocId || undefined,
      subject: search ? search : undefined,
      grounding_status: groundingStatus,
      min_confidence: minConfidence,
      limit: 200,
    })
      .then((res) => setFacts(res))
      .catch((err) => console.error('Failed to load facts:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadFacts();
  }, [selectedDocId, activeTab]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadFacts();
  };

  const selectedDocName = selectedDocId ? (docMap[selectedDocId] || selectedDocId) : null;

  return (
    <div className="space-y-6">
      {/* Page Title Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-stone-900">Facts</h1>
        <p className="text-xs text-stone-500 mt-1">
          Verified claims extracted from your documents.
        </p>
      </div>

      {/* Search Bar and Filter Pills in One Row */}
      <div className="flex flex-col sm:flex-row items-center gap-3">
        {/* Search Input */}
        <form onSubmit={handleSearchSubmit} className="relative flex-1 w-full">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-stone-400" />
          <input
            type="text"
            placeholder="Search facts by subject, predicate, or value..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-lg border border-stone-200/80 bg-white pl-9 pr-4 py-2 text-xs text-stone-900 placeholder-stone-400 focus:border-stone-900 focus:outline-none transition-colors shadow-2xs"
          />
        </form>

        {/* Filter Pill Tabs */}
        <div className="flex items-center gap-1.5 self-start sm:self-auto shrink-0">
          <button
            type="button"
            onClick={() => setActiveTab('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'all'
                ? 'bg-black text-white'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
            }`}
          >
            All ({facts.length})
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('verified')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'verified'
                ? 'bg-black text-white'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
            }`}
          >
            Verified (≥90%)
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('review')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'review'
                ? 'bg-black text-white'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
            }`}
          >
            Needs Review
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('unverified')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
              activeTab === 'unverified'
                ? 'bg-black text-white'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
            }`}
          >
            Unverified
          </button>
        </div>
      </div>

      {/* Document Filter Banner (if selected) */}
      {selectedDocName && (
        <div className="inline-flex items-center gap-2 bg-stone-100 border border-stone-200 text-stone-800 text-xs px-3 py-1 rounded-lg">
          <span>Filtering by: <strong className="font-semibold">{selectedDocName}</strong></span>
          {onClearDocFilter && (
            <button
              type="button"
              onClick={onClearDocFilter}
              className="text-stone-400 hover:text-stone-800 p-0.5 rounded"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      )}

      {/* Facts Card Grid */}
      {loading ? (
        <div className="py-24 text-center text-stone-400 text-sm animate-pulse">
          Loading facts...
        </div>
      ) : facts.length === 0 ? (
        <div className="rounded-xl border border-dashed border-stone-200 bg-white p-12 text-center space-y-2">
          <h3 className="text-sm font-semibold text-stone-900">No matching facts discovered</h3>
          <p className="text-xs text-stone-500">
            Try adjusting your search query or switching to a different filter tab.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {facts.map((fact) => {
            const isVerified = fact.grounding_status === 'VERIFIED';
            const isPartial = fact.grounding_status === 'PARTIAL';
            const groundingScore = Math.round((fact.grounding_score ?? 1.0) * 100);
            const docName = docMap[fact.document_id] || fact.document_id;

            return (
              <div
                key={fact.id}
                onClick={() => onSelectFact(fact.id)}
                className="rounded-xl border border-stone-200/80 bg-white p-4 shadow-sm hover:border-stone-300 hover:shadow transition-all cursor-pointer flex flex-col justify-between space-y-3 min-h-[140px]"
              >
                {/* Top Row: Subject · Predicate + Status Pill */}
                <div className="flex items-start justify-between gap-2">
                  <div className="text-xs text-stone-600 line-clamp-2 leading-relaxed">
                    <span className="font-bold text-stone-900">{fact.subject}</span>
                    <span className="text-stone-400 mx-1.5 font-normal">·</span>
                    <span>{fact.predicate}</span>
                  </div>

                  {isVerified ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/70 whitespace-nowrap shrink-0">
                      ✓ Verified {groundingScore}% ↗
                    </span>
                  ) : isPartial ? (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-amber-50 text-amber-800 border border-amber-200/70 whitespace-nowrap shrink-0">
                      Needs Review
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-stone-100 text-stone-600 border border-stone-200 whitespace-nowrap shrink-0">
                      Unverified
                    </span>
                  )}
                </div>

                {/* Middle Row: Value + Period Pill */}
                <div className="flex items-baseline gap-2 flex-wrap">
                  <span className="text-lg font-bold text-stone-900 tracking-tight">
                    {fact.value}
                  </span>
                  {fact.period && (
                    <span className="text-[11px] font-mono font-medium text-stone-600 bg-stone-100 px-1.5 py-0.5 rounded">
                      {fact.period}
                    </span>
                  )}
                </div>

                {/* Bottom Row: Doc Filename + Page Number + Extraction Confidence */}
                <div className="pt-2 border-t border-stone-100 flex items-center justify-between text-[11px] text-stone-400 font-mono">
                  <span
                    className="flex items-center gap-1 truncate max-w-[200px]"
                    title={`${docName} · p.${fact.page_number || 1}`}
                  >
                    <FileText className="w-3 h-3 text-stone-400 shrink-0" />
                    <span className="truncate">{docName}</span>
                    <span className="shrink-0">· p.{fact.page_number || 1}</span>
                  </span>

                  <span className="shrink-0">
                    {Math.round((fact.confidence ?? 0.88) * 100)}% conf
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
