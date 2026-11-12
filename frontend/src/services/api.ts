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

// ==========================================
// Memoria Local Reactiva para Simulación MVP
// ==========================================
let LOCAL_CONNECTIONS: LegacyConnectionSummary[] = [
  {
    connection_id: "conn-1",
    owner_id: "titular-alberto",
    owner_name: "Alberto Gómez (Abuelo)",
    owner_email: "alberto@legadovivo.com",
    status: "active",
    linked_at: new Date(Date.now() - 86400000 * 10).toISOString(),
    created_at: new Date(Date.now() - 86400000 * 12).toISOString()
  }
];

let LOCAL_INVITES: BeneficiaryInvite[] = [
  {
    connection_id: "inv-1",
    beneficiary_id: "ben-carlos",
    beneficiary_name: "Carlos Gómez (Hijo)",
    beneficiary_email: "carlos@correo.com",
    connection_code: "LEG-8X9K2M",
    status: "active",
    linked_at: new Date(Date.now() - 86400000 * 3).toISOString(),
    created_at: new Date(Date.now() - 86400000 * 4).toISOString()
  }
];

let LOCAL_CAPSULES: CapsuleResponse[] = [
  {
    _id: "demo-cap-1",
    titular_id: "titular-demo-12345",
    title: "El viaje en tren a Cusco con mi hermano Carlos",
    content: "Mijito lindo, te cuento que en 1982 viajamos con Carlos a Cusco. Llovía a cántaros cuando bajamos del tren y nos compramos dos ponchos de lana gruesa en el mercado de San Pedro. Reímos tanto tomando mate de coca caliente junto a un fogón.",
    category: "Anécdotas",
    tags: ["familia", "viajes", "hermanos", "cusco"],
    emotional_tone: "cálido y nostálgico",
    created_at: new Date(Date.now() - 86400000 * 5).toISOString()
  },
  {
    _id: "demo-cap-2",
    titular_id: "titular-demo-12345",
    title: "El secreto del estofado de los domingos",
    content: "Oye, escúchame bien: el gran secreto del estofado nunca fue el vino, sino dejar dorar la cebolla roja con una pizca de azúcar y laurel por al menos veinte minutos a fuego muy bajito. Con todo mi cariño te dejo esta enseñanza para cuando cocines.",
    category: "Cocina y Familia",
    tags: ["recetas", "abuela", "tradición", "comida"],
    emotional_tone: "afectuoso y protector",
    created_at: new Date(Date.now() - 86400000 * 2).toISOString()
  }
];

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
    const online = await checkBackendAvailability();
    if (online) {
      try {
        const res = await fetch(`${API_BASE}/legacy/generate-code`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getAuthHeader() }
        });
        if (res.ok) return await res.json();
      } catch {
        isBackendAvailable = false;
      }
    }

    const randomSuffix = Math.random().toString(36).substring(2, 8).toUpperCase();
    const newCode = `LEG-${randomSuffix}`;
    const newInvite: BeneficiaryInvite = {
      connection_id: `inv-${Date.now()}`,
      connection_code: newCode,
      status: "active",
      created_at: new Date().toISOString()
    };
    LOCAL_INVITES = [newInvite, ...LOCAL_INVITES];
    return {
      connection_code: newCode,
      message: "Código generado exitosamente. Compártelo con tu familiar."
    };
  },

  // Rol Titular: Obtener invitaciones/beneficiarios propios
  async getMyBeneficiaries(): Promise<BeneficiaryInvite[]> {
    const online = await checkBackendAvailability();
    if (online) {
      try {
        const res = await fetch(`${API_BASE}/legacy/my-beneficiaries`, {
          headers: getAuthHeader()
        });
        if (res.ok) return await res.json();
      } catch {
        isBackendAvailable = false;
      }
    }
    return LOCAL_INVITES;
  },

  // Rol Beneficiario: Enviar código para vincularse a un Titular
  async linkWithCode(code: string): Promise<LegacyConnectionSummary> {
    const online = await checkBackendAvailability();
    if (online) {
      try {
        const res = await fetch(`${API_BASE}/legacy/link`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
          body: JSON.stringify({ connection_code: code })
        });
        if (res.ok) return await res.json();
      } catch {
        isBackendAvailable = false;
      }
    }

    const newConnection: LegacyConnectionSummary = {
      connection_id: `conn-${Date.now()}`,
      owner_id: `titular-${Date.now()}`,
      owner_name: `Titular Vinculado (${code.toUpperCase()})`,
      owner_email: "titular@familia.com",
      status: "active",
      linked_at: new Date().toISOString(),
      created_at: new Date().toISOString()
    };
    LOCAL_CONNECTIONS = [newConnection, ...LOCAL_CONNECTIONS];
    return newConnection;
  },

  // Rol Beneficiario: Lista de Titulares a los que tengo acceso ("Seres Queridos")
  async getMyConnections(): Promise<LegacyConnectionSummary[]> {
    const online = await checkBackendAvailability();
    if (online) {
      try {
        const res = await fetch(`${API_BASE}/legacy/my-connections`, {
          headers: getAuthHeader()
        });
        if (res.ok) return await res.json();
      } catch {
        isBackendAvailable = false;
      }
    }
    return LOCAL_CONNECTIONS;
  },

  // ==========================================
  // CÁPSULAS & CHAT RAG
  // ==========================================
  async getCapsules(): Promise<CapsuleResponse[]> {
    try {
      const res = await fetch(`${API_BASE}/capsules/`, {
        headers: getAuthHeader()
      });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }
    return LOCAL_CAPSULES;
  },

  async createCapsule(capsule: CapsulePayload): Promise<CapsuleResponse> {
    try {
      const res = await fetch(`${API_BASE}/capsules/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify(capsule)
      });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }

    const newCap: CapsuleResponse = {
      ...capsule,
      _id: `cap-${Date.now()}`,
      titular_id: "titular-demo-12345",
      created_at: new Date().toISOString()
    };
    LOCAL_CAPSULES = [newCap, ...LOCAL_CAPSULES];
    return newCap;
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

  async getCapsuleAudio(capsuleId: string): Promise<Blob> {
    const res = await fetch(`${API_BASE}/capsules/${encodeURIComponent(capsuleId)}/audio`, {
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
      typical_phrases: ["mijito lindo", "oye", "escúchame bien", "con todo mi cariño", "te cuento"],
      formality_level: "cálido, cercano y profundamente afectuoso",
      warmth_score: 0.95,
      sentiment_tendency: "nostálgico, protector y sereno"
    };
  },

  async sendChatMessage(message: string, titularName: string = "Abuelo", titularId?: string): Promise<ChatResponse> {
    try {
      const res = await fetch(`${API_BASE}/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...getAuthHeader() },
        body: JSON.stringify({ message, titular_name: titularName, titular_id: titularId })
      });
      if (res.ok) return await res.json();
    } catch {
      // Fallback
    }

    // Simulación RAG + Cero Alucinación
    const lower = message.toLowerCase();
    const matched = LOCAL_CAPSULES.filter(c => {
      const inTitle = c.title.toLowerCase().split(/\s+/).some(w => w.length > 3 && lower.includes(w));
      const inContent = c.content.toLowerCase().split(/\s+/).some(w => w.length > 4 && lower.includes(w));
      const inTags = c.tags.some(t => lower.includes(t.toLowerCase()));
      return inTitle || inContent || inTags;
    });

    if (matched.length > 0) {
      const best = matched[0];
      return {
        response: `Mijito lindo, qué alegría que me preguntes eso. Mira, te cuento: ${best.content.replace(/^.*?te cuento que\s*/i, '')} Guardo este recuerdo con todo mi cariño en el alma.`,
        sources: [best.title],
        confidence: 0.94,
        matched_memories: matched.length
      };
    } else {
      const suggested = LOCAL_CAPSULES.length > 0 
        ? LOCAL_CAPSULES[0].title 
        : "mis anécdotas de juventud";
      return {
        response: `No dejé registros sobre este tema específico en mi legado, pero me encantaría que recordáramos "${suggested}".`,
        sources: [],
        confidence: 0.0,
        matched_memories: 0
      };
    }
  }
};
