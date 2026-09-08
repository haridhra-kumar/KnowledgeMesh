import { useState, useRef, useEffect } from 'react';
import { Upload, X, FileText, CheckCircle2, AlertTriangle, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import type { DocumentItem } from '../types';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (doc: DocumentItem) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const [file, setFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [activeDoc, setActiveDoc] = useState<DocumentItem | null>(null);
  const [isDuplicate, setIsDuplicate] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>('');
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollIntervalRef = useRef<any>(null);

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  if (!isOpen) return null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const dropped = e.dataTransfer.files[0];
      if (dropped.type === 'application/pdf' || dropped.name.endsWith('.pdf')) {
        setFile(dropped);
        setError(null);
      } else {
        setError('Only PDF documents are supported.');
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selected = e.target.files[0];
      if (selected.type === 'application/pdf' || selected.name.endsWith('.pdf')) {
        setFile(selected);
        setError(null);
      } else {
        setError('Only PDF documents are supported.');
      }
    }
  };

  const startPolling = (docId: string) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    pollIntervalRef.current = setInterval(async () => {
      try {
        const updated = await api.getDocument(docId);
        setActiveDoc(updated);
        setStatusMessage(updated.progress_message || `Processing: ${updated.status}`);

        if (updated.status === 'COMPLETED' || updated.status === 'FAILED') {
          clearInterval(pollIntervalRef.current);
          setIsUploading(false);
          if (updated.status === 'COMPLETED') {
            onUploadSuccess(updated);
          } else {
            setError(updated.error_message || 'Processing failed.');
          }
        }
      } catch (err: any) {
        console.error('Polling error:', err);
      }
    }, 1200);
  };

  const handleUpload = async () => {
    if (!file) return;

    setIsUploading(true);
    setError(null);
    setIsDuplicate(false);
    setStatusMessage('Uploading document and computing hash...');

    try {
      const response = await api.uploadDocument(file);
      setActiveDoc(response.document);
      setStatusMessage(response.message);

      if (response.is_duplicate) {
        setIsDuplicate(true);
        setIsUploading(false);
        onUploadSuccess(response.document);
      } else {
        // Document is newly created and processing in background
        startPolling(response.document.id);
      }
    } catch (err: any) {
      setIsUploading(false);
      setError(err.message || 'Failed to upload document.');
    }
  };

  const handleReset = () => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    setFile(null);
    setIsUploading(false);
    setActiveDoc(null);
    setIsDuplicate(false);
    setError(null);
    setStatusMessage('');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-xs p-4">
      <div className="w-full max-w-lg rounded-xl border border-stone-200 bg-white p-6 shadow-xl transition-all">
        {/* Modal Header */}
        <div className="flex items-center justify-between border-b border-stone-100 pb-4 mb-4">
          <div>
            <h3 className="text-base font-bold text-stone-900">Upload PDF Document</h3>
            <p className="text-xs text-stone-500 mt-0.5">Extract facts, ground evidence, and reason across documents</p>
          </div>
          <button
            onClick={onClose}
            disabled={isUploading && activeDoc?.status !== 'COMPLETED' && activeDoc?.status !== 'FAILED'}
            className="rounded-lg p-1.5 text-stone-400 hover:bg-stone-100 hover:text-stone-600 transition-colors disabled:opacity-40"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Modal Body */}
        {!activeDoc ? (
          <div>
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
                file
                  ? 'border-stone-400 bg-stone-50/60'
                  : 'border-stone-200 hover:border-stone-300 hover:bg-stone-50/50'
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={handleFileChange}
              />
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-stone-100 text-stone-600 mb-3">
                <Upload className="h-5 w-5" />
              </div>
              {file ? (
                <div>
                  <p className="text-xs font-semibold text-stone-900 flex items-center justify-center gap-1.5">
                    <FileText className="h-4 w-4 text-stone-600" />
                    {file.name}
                  </p>
                  <p className="text-[11px] text-stone-500 mt-1">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              ) : (
                <div>
                  <p className="text-xs font-semibold text-stone-800">Click to select PDF or drag &amp; drop</p>
                  <p className="text-[11px] text-stone-400 mt-1">PDF documents only (financial reports, filings, manuals)</p>
                </div>
              )}
            </div>

            {error && (
              <div className="mt-4 flex items-center gap-2 rounded-lg bg-rose-50 border border-rose-200 p-3 text-xs text-rose-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <div className="mt-6 flex justify-end gap-2.5">
              <button
                type="button"
                onClick={onClose}
                className="px-3.5 py-1.5 text-xs font-medium text-stone-600 hover:bg-stone-100 rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleUpload}
                disabled={!file || isUploading}
                className="inline-flex items-center gap-1.5 px-4 py-1.5 text-xs font-medium text-white bg-black hover:bg-stone-800 rounded-lg shadow-sm transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isUploading ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <>
                    <Upload className="h-3.5 w-3.5" />
                    <span>Process Document</span>
                  </>
                )}
              </button>
            </div>
          </div>
        ) : (
          /* Processing / Duplicate / Result State */
          <div className="space-y-4">
            {isDuplicate && (
              <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 flex items-start gap-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                <div className="text-xs text-amber-900">
                  <div className="font-bold">Duplicate Document Detected</div>
                  <p className="mt-0.5 text-amber-800">
                    A document with identical SHA-256 hash already exists in KnowledgeMesh.
                    Existing facts and cross-document relationships have been preserved.
                  </p>
                </div>
              </div>
            )}

            <div className="rounded-xl border border-stone-200 bg-stone-50/50 p-4 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-stone-800 truncate max-w-[280px]">
                  {activeDoc.filename}
                </span>
                <span className="font-mono text-[11px] text-stone-500 uppercase">
                  {activeDoc.status}
                </span>
              </div>

              {/* Progress Bar */}
              <div className="space-y-1.5">
                <div className="h-2 w-full rounded-full bg-stone-200 overflow-hidden">
                  <div
                    className={`h-full transition-all duration-300 ${
                      activeDoc.status === 'COMPLETED'
                        ? 'bg-emerald-600'
                        : activeDoc.status === 'FAILED'
                        ? 'bg-rose-600'
                        : 'bg-black'
                    }`}
                    style={{ width: `${Math.max(activeDoc.progress_pct || 10, 8)}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] text-stone-500">
                  <span>{statusMessage}</span>
                  <span className="font-mono font-medium">{activeDoc.progress_pct || 0}%</span>
                </div>
              </div>
            </div>

            {activeDoc.status === 'COMPLETED' && (
              <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-4 flex items-center gap-3">
                <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
                <div className="text-xs text-emerald-900">
                  <div className="font-bold">Ingestion Complete!</div>
                  <p className="text-emerald-800 mt-0.5">
                    Extracted verified claims, grounded source page evidence, and updated cross-document relationship graph.
                  </p>
                </div>
              </div>
            )}

            {activeDoc.status === 'FAILED' && (
              <div className="rounded-xl border border-rose-200 bg-rose-50/60 p-4 flex items-center gap-3">
                <AlertCircle className="h-5 w-5 text-rose-600 shrink-0" />
                <div className="text-xs text-rose-900">
                  <div className="font-bold">Processing Failed</div>
                  <p className="text-rose-800 mt-0.5">{error || activeDoc.error_message || 'An error occurred during extraction.'}</p>
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={handleReset}
                className="px-3.5 py-1.5 text-xs font-medium text-stone-600 hover:bg-stone-100 rounded-lg transition-colors"
              >
                Upload Another
              </button>
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-1.5 text-xs font-medium text-white bg-black hover:bg-stone-800 rounded-lg shadow-sm transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
