export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LegacyConnectionSummary {
  connection_id: string;
  owner_id: string;
  owner_name: string;
  owner_email: string;
  status: string;
  linked_at?: string;
  created_at: string;
}

export interface BeneficiaryInvite {
  connection_id: string;
  beneficiary_id?: string;
  beneficiary_name?: string;
  beneficiary_email?: string;
  connection_code: string;
  status: string;
  linked_at?: string;
  created_at: string;
}

export interface CapsulePayload {
  title: string;
  content: string;
  category: string;
  tags: string[];
  emotional_tone?: string;
}

export interface CapsuleResponse extends CapsulePayload {
  _id: string;
  titular_id: string;
  created_at: string;
  audio_path?: string | null;
  audio_filename?: string | null;
  audio_content_type?: string | null;
}

export interface ChatResponse {
  response: string;
  sources: string[];
  confidence: number;
  matched_memories: number;
}

export interface StyleProfile {
  typical_phrases: string[];
  formality_level: string;
  warmth_score: number;
  sentiment_tendency: string;
}

const API_BASE = '/api';

// Circuit breaker para modo local/offline
let isBackendAvailable: boolean | null = null;

async function checkBackendAvailability(): Promise<boolean> {
  if (isBackendAvailable !== null) return isBackendAvailable;
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 1200);
    const res = await fetch(`${API_BASE}/health`, { 
      method: 'GET',
      signal: controller.signal 
    });
    clearTimeout(timeoutId);
    isBackendAvailable = res.ok;
  } catch {
    isBackendAvailable = false;
  }
  return isBackendAvailable;
}

function getAuthHeader(): Record<string, string> {
  const token = localStorage.getItem('legadovivo_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function requestConnectionJson<T>(url: string, options: RequestInit, errorLabel: string): Promise<T> {
  if (!(await checkBackendAvailability())) {
    throw new Error('El servidor no está disponible; no se puede crear una vinculación real sin conexión.');
  }

  let res: Response;
  try {
    res = await fetch(url, options);
  } catch {
    isBackendAvailable = false;
    throw new Error('No se pudo conectar con el servidor para completar la vinculación.');
  }

  isBackendAvailable = true;
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail || `${errorLabel} (HTTP ${res.status}).`);
  }
  return res.json();
}

export const api = {
  isOnline(): boolean {
    return isBackendAvailable === true;
  },
  resetBackendCheck() {
    isBackendAvailable = null;
  },

  // ==========================================
  // AUTENTICACIÓN
  // ==========================================
  async register(email: string, password: string, fullName: string): Promise<AuthResponse> {
    try {
      const res = await fetch(`${API_BASE}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, full_name: fullName })
      });
      if (res.ok) {
        const data = await res.json();
        isBackendAvailable = true;
        return data;
      }
    } catch {
      isBackendAvailable = false;
    }

    // Fallback reactivo local
    const mockUser: User = {
      id: `usr-${Date.now()}`,
      email,
      full_name: fullName,
      is_active: true,
      created_at: new Date().toISOString()
    };
    return {
      access_token: `mock-jwt-token-${Date.now()}`,
      token_type: "bearer",
      user: mockUser
    };
  },

  async login(email: string, password: string): Promise<AuthResponse> {
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      if (res.ok) {
        const data = await res.json();
        isBackendAvailable = true;
        return data;
      }
    } catch {
      isBackendAvailable = false;
    }

    // Fallback reactivo local
    const mockUser: User = {
      id: "usr-demo-alberto",
      email: email || "alberto@legadovivo.com",
      full_name: email.split('@')[0].toUpperCase() || "Alberto Gómez",
      is_active: true,
      created_at: new Date().toISOString()
    };
    return {
      access_token: `mock-jwt-token-${Date.now()}`,
      token_type: "bearer",
      user: mockUser
    };
  },

  async getMe(): Promise<User | null> {
    try {
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: getAuthHeader()
      });
      if (res.ok) return await res.json();
    } catch {
      // Ignorar en fallback
    }
    return null;
  },

  // ==========================================
  // VINCULACIONES & DOBLE ROL
  // ==========================================
  // Rol Titular: Generar código de invitación
  async generateInviteCode(): Promise<{ connection_code: string; message: string }> {
    return requestConnectionJson(`${API_BASE}/legacy/generate-code`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() }
    }, 'No se pudo generar el código');
  },

  // Rol Titular: Obtener invitaciones/beneficiarios propios
  async getMyBeneficiaries(): Promise<BeneficiaryInvite[]> {
    return requestConnectionJson(`${API_BASE}/legacy/my-beneficiaries`, {
      headers: getAuthHeader()
    }, 'No se pudieron cargar tus invitaciones');
  },

  // Rol Beneficiario: Enviar código para vincularse a un Titular
  async linkWithCode(code: string): Promise<LegacyConnectionSummary> {
    return requestConnectionJson(`${API_BASE}/legacy/link`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ connection_code: code })
    }, 'No se pudo canjear el código');
  },

  // Rol Beneficiario: Lista de Titulares a los que tengo acceso ("Seres Queridos")
  async getMyConnections(): Promise<LegacyConnectionSummary[]> {
    return requestConnectionJson(`${API_BASE}/legacy/my-connections`, {
      headers: getAuthHeader()
    }, 'No se pudieron cargar tus vinculaciones');
  },

  // ==========================================
  // CÁPSULAS & CHAT RAG
  // ==========================================
  async getCapsules(titularId?: string): Promise<CapsuleResponse[]> {
    const url = new URL(`${API_BASE}/capsules/`, window.location.origin);
    if (titularId) url.searchParams.set('titular_id', titularId);
    const res = await fetch(url, { headers: getAuthHeader() });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(body?.detail || `No se pudieron cargar las memorias (HTTP ${res.status}).`);
    }
    return res.json();
  },

  async createCapsule(capsule: CapsulePayload): Promise<CapsuleResponse> {
    const res = await fetch(`${API_BASE}/capsules/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify(capsule)
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(body?.detail || `No se pudo guardar el recuerdo (HTTP ${res.status}).`);
    }
    return res.json();
  },

  async uploadCapsuleAudio(capsuleId: string, audio: File | Blob, filename: string): Promise<CapsuleResponse> {
    const form = new FormData();
    const uploadFile = audio instanceof File ? audio : new File([audio], filename, { type: audio.type || 'audio/webm' });
    form.append('audio', uploadFile, filename);
    const res = await fetch(`${API_BASE}/capsules/${encodeURIComponent(capsuleId)}/audio`, {
      method: 'POST',
      headers: getAuthHeader(),
      body: form
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(body?.detail || 'No se pudo guardar el audio.');
    }
    return res.json();
  },

  async getCapsuleAudio(capsuleId: string, titularId?: string): Promise<Blob> {
    const url = new URL(`${API_BASE}/capsules/${encodeURIComponent(capsuleId)}/audio`, window.location.origin);
    if (titularId) url.searchParams.set('titular_id', titularId);
    const res = await fetch(url, {
      headers: getAuthHeader()
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(`Error ${res.status}${body?.detail ? `: ${body.detail}` : ''}`);
    }
    return res.blob();
  },

  async getStyleProfile(): Promise<StyleProfile> {
    try {
      const res = await fetch(`${API_BASE}/capsules/style-profile`, {
        headers: getAuthHeader()
      });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }
    return {
      typical_phrases: [],
      formality_level: "Aún no hay datos suficientes",
      warmth_score: 0.5,
      sentiment_tendency: "Aún no hay recuerdos suficientes"
    };
  },

  async sendChatMessage(message: string, titularName: string, titularId?: string): Promise<ChatResponse> {
    const res = await fetch(`${API_BASE}/chat/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
      body: JSON.stringify({ message, titular_name: titularName, titular_id: titularId })
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      throw new Error(body?.detail || `No se pudo consultar el legado (HTTP ${res.status}).`);
    }
    isBackendAvailable = true;
    return res.json();
  }
};
