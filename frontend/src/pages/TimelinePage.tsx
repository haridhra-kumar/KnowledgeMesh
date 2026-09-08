import React, { useState, useEffect } from 'react';
import { CalendarDays, Building, FileText } from 'lucide-react';
import type { TimelineGroup } from '../types';
import { api } from '../api/client';

interface TimelinePageProps {
  onSelectFact: (factId: string) => void;
}

export const TimelinePage: React.FC<TimelinePageProps> = ({
  onSelectFact,
}) => {
  const [timelineGroups, setTimelineGroups] = useState<TimelineGroup[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedSubject, setSelectedSubject] = useState('');

  const loadTimeline = () => {
    setLoading(true);
    api.getTimeline({
      subject: selectedSubject || undefined,
    })
      .then((res) => setTimelineGroups(res))
      .catch((err) => console.error('Failed to load timeline:', err))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadTimeline();
  }, [selectedSubject]);

  return (
    <div className="space-y-6">
      {/* Page Title Header */}
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-stone-900">Timeline</h1>
        <p className="text-xs text-stone-500 mt-1">
          Chronological progression ordered strictly by explicit period metadata (independent of PDF page order).
        </p>
      </div>

      {/* Filter Control */}
      <div className="flex items-center justify-between gap-4">
        <input
          type="text"
          placeholder="Filter timeline by entity (e.g. Acme, Delhivery)..."
          value={selectedSubject}
          onChange={(e) => setSelectedSubject(e.target.value)}
          className="rounded-lg border border-stone-200/80 bg-white px-3.5 py-2 text-xs text-stone-900 placeholder-stone-400 focus:border-stone-900 focus:outline-none max-w-sm w-full transition-colors shadow-2xs"
        />

        <span className="text-xs text-stone-400 font-mono">
          {timelineGroups.length} metrics tracked
        </span>
      </div>

      {/* Timeline Streams */}
      {loading ? (
        <div className="py-24 text-center text-stone-400 text-sm animate-pulse">
          Building temporal progression...
        </div>
      ) : timelineGroups.length === 0 ? (
        <div className="rounded-xl border border-dashed border-stone-200 bg-white p-12 text-center space-y-2">
          <CalendarDays className="mx-auto h-8 w-8 text-stone-300 mb-2" />
          <h3 className="text-sm font-semibold text-stone-900">No temporal facts found</h3>
          <p className="text-xs text-stone-500 max-w-md mx-auto">
            Upload documents with explicit dates or fiscal periods (e.g., FY2023, FY2024, Q1 FY2025) to view chronological progressions.
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {timelineGroups.map((group, gIdx) => (
            <div key={gIdx} className="rounded-xl border border-stone-200/80 bg-white p-5 shadow-sm space-y-4">
              <div className="border-b border-stone-100 pb-3 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Building className="h-4 w-4 text-stone-400" />
                  <h3 className="text-sm font-bold text-stone-900">{group.subject}</h3>
                  <span className="text-stone-300">—</span>
                  <span className="text-xs font-medium text-stone-600 capitalize">{group.predicate}</span>
                </div>
                <span className="text-xs text-stone-400 font-mono">{group.items.length} periods</span>
              </div>

              {/* Chronological Series */}
              <div className="relative pl-6 before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-stone-200 space-y-4">
                {group.items.map((item) => {
                  const isVerified = item.grounding_status === 'VERIFIED';
                  return (
                    <div
                      key={item.id}
                      onClick={() => onSelectFact(item.fact_id)}
                      className="relative cursor-pointer group"
                    >
                      {/* Dot on timeline */}
                      <div className="absolute -left-[27px] top-1.5 h-3.5 w-3.5 rounded-full border-2 border-white bg-stone-900 shadow-sm group-hover:scale-125 transition-transform" />

                      <div className="rounded-lg border border-stone-200/80 bg-stone-50/50 p-4 hover:bg-white hover:border-stone-300 hover:shadow-sm transition-all space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-baseline gap-2">
                            <span className="font-mono font-bold text-stone-900 text-xs bg-white px-2 py-0.5 rounded border border-stone-200/80">
                              {item.period}
                            </span>
                            <span className="text-base font-bold text-stone-900 group-hover:text-blue-600 transition-colors">
                              {item.value}
                            </span>
                          </div>

                          {isVerified ? (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200/70">
                              ✓ Verified
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-amber-50 text-amber-800 border border-amber-200/70">
                              Review
                            </span>
                          )}
                        </div>

                        <p className="text-xs italic text-stone-600 bg-white p-2 rounded border border-stone-100 line-clamp-2">
                          &ldquo;{item.evidence_quote}&rdquo;
                        </p>

                        <div className="flex items-center justify-between text-[11px] text-stone-400 font-mono pt-1">
                          <span className="flex items-center gap-1 truncate max-w-[250px]">
                            <FileText className="w-3 h-3 text-stone-400 shrink-0" />
                            <span className="truncate">{item.document_filename}</span>
                            <span>· p.{item.page_number}</span>
                          </span>
                          <span className="text-stone-700 font-medium group-hover:text-black">
                            Inspect source evidence →
                          </span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
