import React, { useState, useEffect } from 'react';
import {
  FileText,
  CheckCircle2,
  ShieldCheck,
  GitCompare,
  Upload,
} from 'lucide-react';
import type { DashboardStats, RelationshipItem } from '../types';
import { api } from '../api/client';

interface OverviewPageProps {
  stats: DashboardStats | null;
  loading: boolean;
  onOpenUpload: () => void;
  onNavigate: (tab: any) => void;
  onSelectRelationship: (id: string) => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  stats,
  loading,
  onOpenUpload,
  onNavigate,
  onSelectRelationship,
}) => {
  const [recentFindings, setRecentFindings] = useState<RelationshipItem[]>([]);
  const [findingsLoading, setFindingsLoading] = useState(false);

  useEffect(() => {
    setFindingsLoading(true);
    api.getRelationships({ limit: 8 })
      .then((res) => setRecentFindings(res))
      .catch((err) => console.error('Failed to load recent findings:', err))
      .finally(() => setFindingsLoading(false));
  }, [stats?.total_relationships]);

  if (loading || !stats) {
    return (
      <div className="py-24 text-center text-stone-400 text-sm animate-pulse">
        Loading knowledge metrics...
      </div>
    );
  }

  const isEmpty = stats.total_documents === 0;

  return (
    <div className="space-y-6">
      {/* Page Title Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-stone-900">Knowledge Overview</h1>
        <p className="text-xs text-stone-500 mt-1">
          Facts, evidence, and relationships discovered across your documents.
        </p>
      </div>

      {/* Top 4 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Documents */}
        <div
          onClick={() => onNavigate('documents')}
          className="rounded-xl border border-stone-200/80 bg-white p-5 shadow-sm hover:border-stone-300 hover:shadow transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-stone-400 mb-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
              DOCUMENTS
            </span>
            <FileText className="h-4 w-4 text-stone-400" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-stone-900">
            {stats.total_documents}
          </div>
          <p className="text-xs text-stone-400 mt-1">Ingested source PDFs</p>
        </div>

        {/* Facts */}
        <div
          onClick={() => onNavigate('facts')}
          className="rounded-xl border border-stone-200/80 bg-white p-5 shadow-sm hover:border-stone-300 hover:shadow transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-stone-400 mb-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
              FACTS
            </span>
            <CheckCircle2 className="h-4 w-4 text-stone-400" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-stone-900">
            {stats.total_facts}
          </div>
          <p className="text-xs text-stone-400 mt-1">Extracted claims</p>
        </div>

        {/* Verified */}
        <div
          onClick={() => onNavigate('facts')}
          className="rounded-xl border border-stone-200/80 bg-white p-5 shadow-sm hover:border-stone-300 hover:shadow transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-stone-400 mb-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
              VERIFIED
            </span>
            <ShieldCheck className="h-4 w-4 text-emerald-500" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-emerald-600">
            {stats.verified_facts}
          </div>
          <p className="text-xs text-stone-400 mt-1">≥90% evidence match</p>
        </div>

        {/* Relationships */}
        <div
          onClick={() => onNavigate('relationships')}
          className="rounded-xl border border-stone-200/80 bg-white p-5 shadow-sm hover:border-stone-300 hover:shadow transition-all cursor-pointer"
        >
          <div className="flex items-center justify-between text-stone-400 mb-1">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-400">
              RELATIONSHIPS
            </span>
            <GitCompare className="h-4 w-4 text-stone-400" />
          </div>
          <div className="text-3xl font-bold tracking-tight text-stone-900">
            {stats.total_relationships}
          </div>
          <p className="text-xs text-stone-400 mt-1">Compared candidate pairs</p>
        </div>
      </div>

      {/* Relationship Breakdown Card */}
      <div className="rounded-xl border border-stone-200/80 bg-white p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-stone-900">Relationship Breakdown</h2>
          <button
            type="button"
            onClick={() => onNavigate('relationships')}
            className="text-xs text-stone-500 hover:text-stone-900 font-medium transition-colors"
          >
            View all relationships →
          </button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {/* Corroborated */}
          <div
            onClick={() => onNavigate('relationships')}
            className="rounded-lg border border-emerald-200/70 bg-emerald-50/40 p-3.5 flex items-center justify-between cursor-pointer hover:bg-emerald-50/80 transition-colors"
          >
            <div>
              <div className="text-xs font-bold text-emerald-900">Corroborated</div>
              <div className="text-[11px] text-emerald-600 mt-0.5">Substantially agreed</div>
            </div>
            <div className="text-2xl font-bold text-emerald-700">{stats.corroborations}</div>
          </div>

          {/* Reconciled */}
          <div
            onClick={() => onNavigate('relationships')}
            className="rounded-lg border border-amber-200/70 bg-amber-50/40 p-3.5 flex items-center justify-between cursor-pointer hover:bg-amber-50/80 transition-colors"
          >
            <div>
              <div className="text-xs font-bold text-amber-900">Reconciled</div>
              <div className="text-[11px] text-amber-600 mt-0.5">Explained by context</div>
            </div>
            <div className="text-2xl font-bold text-amber-700">{stats.reconciliations}</div>
          </div>

          {/* Contradictions */}
          <div
            onClick={() => onNavigate('relationships')}
            className="rounded-lg border border-rose-200/70 bg-rose-50/40 p-3.5 flex items-center justify-between cursor-pointer hover:bg-rose-50/80 transition-colors"
          >
            <div>
              <div className="text-xs font-bold text-rose-900">Contradictions</div>
              <div className="text-[11px] text-rose-600 mt-0.5">Unreconciled conflict</div>
            </div>
            <div className="text-2xl font-bold text-rose-700">{stats.contradictions}</div>
          </div>

          {/* Needs Review */}
          <div
            onClick={() => onNavigate('review')}
            className="rounded-lg border border-stone-200 bg-stone-50 p-3.5 flex items-center justify-between cursor-pointer hover:bg-stone-100/80 transition-colors"
          >
            <div>
              <div className="text-xs font-bold text-stone-900">Needs Review</div>
              <div className="text-[11px] text-stone-500 mt-0.5">Uncertain or unverified</div>
            </div>
            <div className="text-2xl font-bold text-stone-800">{stats.needs_review_count}</div>
          </div>
        </div>
      </div>

      {/* Recent Cross-Document Findings */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold text-stone-900">Recent Cross-Document Findings</h2>
          <span className="text-xs text-stone-400 font-normal">Click to inspect evidence</span>
        </div>

        {isEmpty ? (
          <div className="rounded-xl border border-dashed border-stone-200 bg-white p-10 text-center space-y-3">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-stone-50 text-stone-400">
              <FileText className="h-6 w-6" />
            </div>
            <h3 className="text-sm font-semibold text-stone-900">No documents ingested yet</h3>
            <p className="text-xs text-stone-500 max-w-sm mx-auto">
              Upload PDF reports or specifications to discover grounded facts and cross-document relationships.
            </p>
            <button
              type="button"
              onClick={onOpenUpload}
              className="inline-flex items-center gap-2 rounded-lg bg-black px-4 py-2 text-xs font-medium text-white hover:bg-stone-800 transition-colors shadow-sm"
            >
              <Upload className="h-3.5 w-3.5" />
              Upload Your First PDF
            </button>
          </div>
        ) : findingsLoading ? (
          <div className="py-8 text-center text-stone-400 text-xs animate-pulse">
            Loading cross-document findings...
          </div>
        ) : recentFindings.length === 0 ? (
          <div className="rounded-xl border border-stone-200/80 bg-white p-8 text-center text-xs text-stone-500">
            Upload at least two related PDF documents to automatically identify corroborations, reconciliations, and contradictions.
          </div>
        ) : (
          <div className="space-y-2.5">
            {recentFindings.map((rel) => {
              const isContradiction = rel.type === 'CONTRADICT';
              const isReconciled = rel.type === 'RECONCILE';
              const isCorroboration = rel.type === 'CORROBORATE';

              const valA = rel.fact_a_value || '—';
              const valB = rel.fact_b_value || '—';
              const docA = rel.fact_a_doc_name || 'Doc A';
              const docB = rel.fact_b_doc_name || 'Doc B';

              return (
                <div
                  key={rel.id}
                  onClick={() => onSelectRelationship(rel.id)}
                  className="rounded-xl border border-stone-200/80 bg-white p-4 shadow-sm hover:border-stone-300 hover:shadow transition-all cursor-pointer space-y-2"
                >
                  {/* Row 1: Status Pill + Predicate - Subject + Confidence */}
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2.5">
                      {isContradiction && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200/70">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                          CONTRADICTION
                        </span>
                      )}
                      {isReconciled && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200/70">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />
                          RECONCILED
                        </span>
                      )}
                      {isCorroboration && (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200/70">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          CORROBORATED
                        </span>
                      )}

                      <span className="text-xs font-bold text-stone-900">
                        {rel.fact_a_predicate} — {rel.fact_a_subject}
                      </span>
                    </div>

                    <span className="text-xs text-stone-400 font-mono flex items-center gap-1">
                      {Math.round(rel.confidence * 100)}% conf →
                    </span>
                  </div>

                  {/* Row 2: Value Comparison in monospace/clean font */}
                  <div className="text-xs font-mono text-stone-700">
                    <span className="font-semibold text-stone-900">{valA} ({docA})</span>
                    <span className="text-stone-400 mx-2 font-sans">vs</span>
                    <span className="font-semibold text-stone-900">{valB} ({docB})</span>
                  </div>

                  {/* Row 3: Italic Quote / Contextual Explanation */}
                  <div className="text-xs text-stone-500 italic truncate">
                    &ldquo;{rel.reasoning || 'Cross-document relationship detected.'}&rdquo;
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};
