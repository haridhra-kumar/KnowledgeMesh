import React, { useState } from 'react';
import { FileText, UploadCloud, Trash2, Copy, Link2 } from 'lucide-react';
import type { DocumentItem } from '../types';
import { api } from '../api/client';

interface DocumentsPageProps {
  documents: DocumentItem[];
  loading: boolean;
  onRefresh: () => void;
  onSelectDocumentFacts: (docId: string) => void;
  onOpenUpload?: () => void;
}

export const DocumentsPage: React.FC<DocumentsPageProps> = ({
  documents,
  loading,
  onRefresh,
  onSelectDocumentFacts,
  onOpenUpload,
}) => {
  const [actionLoading, setActionLoading] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, doc: DocumentItem) => {
    e.stopPropagation();
    if (!confirm(`Are you sure you want to delete "${doc.filename}" and its associated facts?`)) return;
    setActionLoading(doc.id);
    try {
      await api.deleteDocument(doc.id);
      onRefresh();
    } catch (err: any) {
      alert(`Error deleting document: ${err.message}`);
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      return d.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return dateStr;
    }
  };

  if (loading) {
    return (
      <div className="py-24 text-center text-stone-400 text-sm animate-pulse">
        Loading documents...
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with Title and Upload PDF Button */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-stone-900">Documents</h1>
          <p className="text-xs text-stone-500 mt-1">
            Source PDF filings ingested into the fact layer.
          </p>
        </div>

        {onOpenUpload && (
          <button
            type="button"
            onClick={onOpenUpload}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-lg bg-black text-white hover:bg-stone-800 text-xs font-medium transition-colors shadow-sm"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Upload PDF</span>
          </button>
        )}
      </div>

      {documents.length === 0 ? (
        <div className="rounded-xl border border-dashed border-stone-200 bg-white p-12 text-center space-y-3">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-stone-50 text-stone-400">
            <FileText className="h-6 w-6" />
          </div>
          <h3 className="text-sm font-semibold text-stone-900">No documents in KnowledgeMesh</h3>
          <p className="text-xs text-stone-500 max-w-sm mx-auto">
            Upload financial reports, product specs, or regulatory filings to extract grounded claims and build your cross-document graph.
          </p>
          {onOpenUpload && (
            <button
              type="button"
              onClick={onOpenUpload}
              className="inline-flex items-center gap-2 rounded-lg bg-black px-4 py-2 text-xs font-medium text-white hover:bg-stone-800 transition-colors shadow-sm"
            >
              <UploadCloud className="h-3.5 w-3.5" />
              Upload PDF
            </button>
          )}
        </div>
      ) : (
        <div className="rounded-xl border border-stone-200/80 bg-white overflow-hidden shadow-sm">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-stone-100 bg-white text-[10px] font-bold uppercase tracking-wider text-stone-400">
                <th className="py-3.5 px-6">DOCUMENT</th>
                <th className="py-3.5 px-6">FACTS DISCOVERED</th>
                <th className="py-3.5 px-6">UPLOADED</th>
                <th className="py-3.5 px-6">STATUS</th>
                <th className="py-3.5 px-6 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100">
              {documents.map((doc) => {
                const isActionPending = actionLoading === doc.id;
                const isProcessing = [
                  'PARSING',
                  'EXTRACTING',
                  'GROUNDING',
                  'NORMALIZING',
                  'MATCHING',
                  'RELATIONSHIPS',
                  'UPLOADED',
                ].includes(doc.status);

                const factCount = doc.facts_count ?? 0;

                return (
                  <tr
                    key={doc.id}
                    className="hover:bg-stone-50/60 transition-colors group cursor-pointer"
                    onClick={() => onSelectDocumentFacts(doc.id)}
                  >
                    {/* DOCUMENT */}
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-stone-50 border border-stone-200/70 flex items-center justify-center text-stone-400 shrink-0">
                          <FileText className="w-4 h-4" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <div className="text-xs font-semibold text-stone-900 group-hover:text-blue-600 transition-colors truncate">
                              {doc.filename}
                            </div>
                            {doc.duplicate_of && (
                              <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium bg-violet-50 text-violet-700 border border-violet-200/80 shrink-0">
                                <Copy className="w-2.5 h-2.5" />
                                Duplicate
                              </span>
                            )}
                          </div>
                          <div className="text-[10px] text-stone-400 font-mono mt-0.5 truncate">
                            {doc.id}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* FACTS DISCOVERED */}
                    <td className="py-4 px-6">
                      <span className="inline-block bg-stone-100 text-stone-800 font-mono font-bold text-xs px-2.5 py-0.5 rounded">
                        {factCount} facts
                      </span>
                    </td>

                    {/* UPLOADED */}
                    <td className="py-4 px-6 text-xs text-stone-500 font-normal">
                      {formatDate(doc.created_at)}
                    </td>

                    {/* STATUS */}
                    <td className="py-4 px-6">
                      {isProcessing ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-amber-50 text-amber-700 border border-amber-200/80">
                          <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                          Processing ({doc.progress_pct || 0}%)
                        </span>
                      ) : doc.status === 'FAILED' ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200/80">
                          <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                          Failed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/80">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                          Processed
                        </span>
                      )}
                    </td>

                    {/* ACTION */}
                    <td className="py-4 px-6 text-right">
                      <div className="flex items-center justify-end gap-3">
                        {doc.duplicate_of && (
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              alert(`This document is a duplicate of document ${doc.duplicate_of}.\n\nMerge/associate functionality will group these documents together for unified analysis. For now, both copies are processed independently.`);
                            }}
                            title="Merge with original document"
                            className="inline-flex items-center gap-1 text-xs font-medium text-violet-600 hover:text-violet-800 transition-colors"
                          >
                            <Link2 className="w-3 h-3" />
                            Merge
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectDocumentFacts(doc.id);
                          }}
                          className="text-xs font-medium text-stone-500 hover:text-stone-900 transition-colors"
                        >
                          View facts →
                        </button>
                        <button
                          type="button"
                          disabled={isActionPending}
                          onClick={(e) => handleDelete(e, doc)}
                          title="Delete document"
                          className="text-stone-300 hover:text-rose-600 transition-colors p-1 rounded"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
