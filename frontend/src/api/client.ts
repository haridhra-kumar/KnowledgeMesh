import type {
  DocumentItem,
  FactItem,
  RelationshipItem,
  ClusterItem,
  TimelineGroup,
  ReviewItem,
  DashboardStats,
  DiagnosticItem,
  UploadResponse
} from '../types';

const API_BASE = '/api';

async function fetchJson<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    let errorDetail = `Request failed: ${res.statusText}`;
    try {
      const errObj = await res.json();
      if (errObj.detail) {
        errorDetail = errObj.detail;
      }
    } catch {
      // Ignore
    }
    throw new Error(errorDetail);
  }
  return res.json();
}

export const api = {
  // Stats
  async getStats(): Promise<DashboardStats> {
    return fetchJson<DashboardStats>(`${API_BASE}/stats`);
  },

  // Documents
  async getDocuments(): Promise<DocumentItem[]> {
    return fetchJson<DocumentItem[]>(`${API_BASE}/documents`);
  },

  async getDocument(id: string): Promise<DocumentItem> {
    return fetchJson<DocumentItem>(`${API_BASE}/documents/${id}`);
  },

  async uploadDocument(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);
    return fetchJson<UploadResponse>(`${API_BASE}/documents`, {
      method: 'POST',
      body: formData,
    });
  },

  async deleteDocument(id: string): Promise<{ success: boolean; message: string }> {
    return fetchJson<{ success: boolean; message: string }>(`${API_BASE}/documents/${id}`, {
      method: 'DELETE',
    });
  },

  async clearAllDocuments(): Promise<{ success: boolean; message: string }> {
    return fetchJson<{ success: boolean; message: string }>(`${API_BASE}/documents`, {
      method: 'DELETE',
    });
  },

  async reprocessDocument(id: string): Promise<{ success: boolean; message: string }> {
    return fetchJson<{ success: boolean; message: string }>(`${API_BASE}/documents/${id}/reprocess`, {
      method: 'POST',
    });
  },

  // Facts
  async getFacts(params?: {
    document_id?: string;
    subject?: string;
    predicate?: string;
    fact_type?: string;
    period?: string;
    grounding_status?: string;
    min_confidence?: number;
    status?: string;
    limit?: number;
    offset?: number;
  }): Promise<FactItem[]> {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          query.append(key, String(val));
        }
      });
    }
    return fetchJson<FactItem[]>(`${API_BASE}/facts?${query.toString()}`);
  },

  async getFact(id: string): Promise<FactItem> {
    return fetchJson<FactItem>(`${API_BASE}/facts/${id}`);
  },

  // Relationships
  async getRelationships(params?: {
    type?: string;
    min_confidence?: number;
    document_id?: string;
    limit?: number;
    offset?: number;
  }): Promise<RelationshipItem[]> {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          query.append(key, String(val));
        }
      });
    }
    return fetchJson<RelationshipItem[]>(`${API_BASE}/relationships?${query.toString()}`);
  },

  async getRelationship(id: string): Promise<RelationshipItem> {
    return fetchJson<RelationshipItem>(`${API_BASE}/relationships/${id}`);
  },

  // Clusters
  async getClusters(params?: { subject?: string; limit?: number; offset?: number }): Promise<ClusterItem[]> {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          query.append(key, String(val));
        }
      });
    }
    return fetchJson<ClusterItem[]>(`${API_BASE}/clusters?${query.toString()}`);
  },

  async getCluster(id: string): Promise<ClusterItem> {
    return fetchJson<ClusterItem>(`${API_BASE}/clusters/${id}`);
  },

  // Timeline
  async getTimeline(params?: { subject?: string; predicate?: string; document_id?: string }): Promise<TimelineGroup[]> {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          query.append(key, String(val));
        }
      });
    }
    return fetchJson<TimelineGroup[]>(`${API_BASE}/timeline?${query.toString()}`);
  },

  // Review
  async getReview(params?: { severity?: string; review_type?: string }): Promise<ReviewItem[]> {
    const query = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, val]) => {
        if (val !== undefined && val !== null && val !== '') {
          query.append(key, String(val));
        }
      });
    }
    return fetchJson<ReviewItem[]>(`${API_BASE}/review?${query.toString()}`);
  },

  // Diagnostics
  async getDiagnostics(document_id?: string): Promise<DiagnosticItem[]> {
    const query = document_id ? `?document_id=${encodeURIComponent(document_id)}` : '';
    return fetchJson<DiagnosticItem[]>(`${API_BASE}/diagnostics${query}`);
  },
};
