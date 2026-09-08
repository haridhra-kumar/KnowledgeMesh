import { useState, useEffect } from 'react';
import { AppLayout } from './layouts/AppLayout';
import type { NavTab } from './layouts/AppLayout';
import { OverviewPage } from './pages/OverviewPage';
import { DocumentsPage } from './pages/DocumentsPage';
import { FactsPage } from './pages/FactsPage';
import { RelationshipsPage } from './pages/RelationshipsPage';
import { TimelinePage } from './pages/TimelinePage';
import { ReviewPage } from './pages/ReviewPage';
import { UploadModal } from './components/UploadModal';
import { FactDetailModal } from './components/FactDetailModal';
import { RelationshipDetailModal } from './components/RelationshipDetailModal';
import { api } from './api/client';
import type { DashboardStats, DocumentItem } from './types';

export function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('overview');
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [documentsLoading, setDocumentsLoading] = useState(false);

  // Modal states
  const [isUploadOpen, setIsUploadOpen] = useState(false);
  const [selectedFactId, setSelectedFactId] = useState<string | null>(null);
  const [selectedRelationshipId, setSelectedRelationshipId] = useState<string | null>(null);
  const [selectedDocIdForFacts, setSelectedDocIdForFacts] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      const res = await api.getStats();
      setStats(res);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    } finally {
      setStatsLoading(false);
    }
  };

  const fetchDocuments = async () => {
    setDocumentsLoading(true);
    try {
      const res = await api.getDocuments();
      setDocuments(res);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
    } finally {
      setDocumentsLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchDocuments();
  }, []);

  const handleUploadSuccess = () => {
    fetchStats();
    fetchDocuments();
  };

  const handleClearAll = async () => {
    const confirmed = window.confirm(
      'Are you sure you want to reset all documents and the entire knowledge graph? This action cannot be undone.'
    );
    if (!confirmed) return;

    try {
      await api.clearAllDocuments();
      await fetchStats();
      await fetchDocuments();
      setSelectedFactId(null);
      setSelectedRelationshipId(null);
      setSelectedDocIdForFacts(null);
    } catch (err: any) {
      alert(`Failed to reset knowledge base: ${err.message}`);
    }
  };

  const handleSelectDocumentFacts = (docId: string) => {
    setSelectedDocIdForFacts(docId);
    setCurrentTab('facts');
  };

  return (
    <AppLayout
      currentTab={currentTab}
      onTabChange={(tab) => {
        setCurrentTab(tab);
        if (tab !== 'facts') setSelectedDocIdForFacts(null);
        fetchStats();
      }}
      onOpenUpload={() => setIsUploadOpen(true)}
      onClearAll={handleClearAll}
      stats={stats}
    >
      {currentTab === 'overview' && (
        <OverviewPage
          stats={stats}
          loading={statsLoading}
          onOpenUpload={() => setIsUploadOpen(true)}
          onNavigate={(tab) => setCurrentTab(tab)}
          onSelectRelationship={(id) => setSelectedRelationshipId(id)}
        />
      )}

      {currentTab === 'documents' && (
        <DocumentsPage
          documents={documents}
          loading={documentsLoading}
          onRefresh={() => {
            fetchDocuments();
            fetchStats();
          }}
          onSelectDocumentFacts={handleSelectDocumentFacts}
          onOpenUpload={() => setIsUploadOpen(true)}
        />
      )}

      {currentTab === 'facts' && (
        <FactsPage
          documents={documents}
          onSelectFact={(id) => setSelectedFactId(id)}
          selectedDocId={selectedDocIdForFacts}
          onClearDocFilter={() => setSelectedDocIdForFacts(null)}
        />
      )}

      {currentTab === 'relationships' && (
        <RelationshipsPage
          documents={documents}
          onSelectRelationship={(id) => setSelectedRelationshipId(id)}
        />
      )}

      {currentTab === 'timeline' && (
        <TimelinePage
          onSelectFact={(id) => setSelectedFactId(id)}
        />
      )}

      {currentTab === 'review' && (
        <ReviewPage
          onSelectFact={(id) => setSelectedFactId(id)}
          onSelectRelationship={(id) => setSelectedRelationshipId(id)}
        />
      )}

      {/* Modals */}
      <UploadModal
        isOpen={isUploadOpen}
        onClose={() => setIsUploadOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />

      <FactDetailModal
        factId={selectedFactId}
        onClose={() => setSelectedFactId(null)}
        onSelectRelationship={(relId) => {
          setSelectedFactId(null);
          setSelectedRelationshipId(relId);
        }}
      />

      <RelationshipDetailModal
        relationshipId={selectedRelationshipId}
        onClose={() => setSelectedRelationshipId(null)}
        onSelectFact={(factId) => {
          setSelectedRelationshipId(null);
          setSelectedFactId(factId);
        }}
      />
    </AppLayout>
  );
}

export default App;
