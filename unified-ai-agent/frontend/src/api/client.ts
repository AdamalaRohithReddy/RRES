import {
  AuthResponse,
  ChatMessage,
  DocumentItem,
  EligibilityResult,
  SchemeResult,
  ApplicationItem,
  UserProfile,
  DetectedNeed
} from '../types';

const API_BASE = '/api';

function getHeaders(isMultipart = false): HeadersInit {
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = {
    'X-Correlation-ID': 'web-' + Math.random().toString(36).substring(2, 10),
  };
  if (!isMultipart) {
    headers['Content-Type'] = 'application/json';
  }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    let message = errorData.message;
    if (!message && errorData.fieldErrors) {
      message = Object.entries(errorData.fieldErrors)
        .map(([k, v]) => `${k}: ${v}`)
        .join(', ');
    }
    if (!message) {
      message = errorData.error || `HTTP error ${res.status}`;
    }
    throw new Error(message);
  }
  return res.json();
}

export const api = {
  // Auth
  async login(username: string, password: string): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ username, password }),
    });
    return handleResponse(res);
  },

  async register(data: any): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  async getMe(): Promise<any> {
    const res = await fetch(`${API_BASE}/auth/me`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  // Citizen Profile
  async getProfile(): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/profile`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async updateProfile(profile: Partial<UserProfile>): Promise<UserProfile> {
    const res = await fetch(`${API_BASE}/profile`, {
      method: 'PUT',
      headers: getHeaders(),
      body: JSON.stringify(profile),
    });
    return handleResponse(res);
  },

  // AI Chat & Multi-Need Detection
  async chat(message: string, conversationId?: string): Promise<any> {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({
        message: message.trim(),
        query: message.trim(),
        conversation_id: conversationId || null,
        session_id: conversationId || null,
      }),
    });
    return handleResponse(res);
  },

  async detectNeeds(text: string): Promise<any> {
    const res = await fetch(`${API_BASE}/chat/needs`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ text }),
    });
    return handleResponse(res);
  },

  async getCitizenNeeds(): Promise<DetectedNeed[]> {
    const res = await fetch(`${API_BASE}/chat/needs`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  // Documents
  async uploadDocument(file: File): Promise<DocumentItem> {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      headers: getHeaders(true),
      body: formData,
    });
    return handleResponse(res);
  },

  async getDocuments(): Promise<DocumentItem[]> {
    const res = await fetch(`${API_BASE}/documents`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async getDocumentDetail(id: number): Promise<DocumentItem> {
    const res = await fetch(`${API_BASE}/documents/${id}`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  // Schemes
  async searchSchemes(q: string, category?: string, limit = 10): Promise<{ results: SchemeResult[]; total_matches: number }> {
    const params = new URLSearchParams({ q });
    if (category) params.append('category', category);
    if (limit) params.append('limit', limit.toString());
    const res = await fetch(`${API_BASE}/schemes/search?${params.toString()}`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  // Eligibility
  async checkEligibility(schemeName: string, citizenProfile?: any): Promise<EligibilityResult> {
    const res = await fetch(`${API_BASE}/eligibility/check`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify({ scheme_name: schemeName, citizen_profile: citizenProfile }),
    });
    return handleResponse(res);
  },

  async getEligibilityHistory(): Promise<any[]> {
    const res = await fetch(`${API_BASE}/eligibility/history`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  // Applications
  async getApplications(): Promise<ApplicationItem[]> {
    const res = await fetch(`${API_BASE}/applications`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async getApplication(id: string): Promise<ApplicationItem> {
    const res = await fetch(`${API_BASE}/applications/${id}`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },

  async createApplication(data: any): Promise<ApplicationItem> {
    const res = await fetch(`${API_BASE}/applications`, {
      method: 'POST',
      headers: getHeaders(),
      body: JSON.stringify(data),
    });
    return handleResponse(res);
  },

  // Health
  async getHealthReady(): Promise<any> {
    const res = await fetch(`${API_BASE}/health/ready`, {
      headers: getHeaders(),
    });
    return handleResponse(res);
  },
};
