import React from 'react';

interface StatusBadgeProps {
  status: string;
  size?: 'sm' | 'md';
  showDot?: boolean;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  size = 'md',
  showDot = true
}) => {
  const norm = (status || '').toUpperCase();

  // Determine color scheme based on specifications:
  // Green: verified, corroborated, high confidence, completed
  // Red: contradiction, failed, high severity
  // Amber: reconciled, needs review, medium confidence, partial
  // Gray: uncertain, unverified, pending, uploaded, parsing, extracting, normalizing, matching
  let styleClasses = 'bg-slate-100 text-slate-700 border-slate-200';
  let dotColor = 'bg-slate-400';

  if (['VERIFIED', 'CORROBORATE', 'CORROBORATED', 'COMPLETED', 'HIGH', 'HIGH CONFIDENCE'].includes(norm)) {
    styleClasses = 'bg-emerald-50 text-emerald-700 border-emerald-200';
    dotColor = 'bg-emerald-500';
  } else if (['CONTRADICT', 'CONTRADICTION', 'FAILED', 'HIGH SEVERITY', 'REJECTED'].includes(norm)) {
    styleClasses = 'bg-rose-50 text-rose-700 border-rose-200';
    dotColor = 'bg-rose-500';
  } else if (['RECONCILE', 'RECONCILED', 'PARTIAL', 'NEEDS REVIEW', 'MEDIUM', 'MEDIUM CONFIDENCE'].includes(norm)) {
    styleClasses = 'bg-amber-50 text-amber-700 border-amber-200';
    dotColor = 'bg-amber-500';
  } else if (['UNVERIFIED', 'UNCERTAIN', 'LOW', 'LOW CONFIDENCE', 'UPLOADED', 'PARSING', 'EXTRACTING', 'GROUNDING', 'NORMALIZING', 'MATCHING', 'RELATIONSHIPS'].includes(norm)) {
    styleClasses = 'bg-slate-100 text-slate-600 border-slate-200';
    dotColor = 'bg-slate-400';
  }

  const sizeClasses = size === 'sm'
    ? 'text-xs px-2 py-0.5'
    : 'text-xs font-medium px-2.5 py-1';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border ${styleClasses} ${sizeClasses}`}>
      {showDot && <span className={`h-1.5 w-1.5 rounded-full ${dotColor}`} />}
      <span>{status}</span>
    </span>
  );
};
