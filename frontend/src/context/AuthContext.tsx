import React, { createContext, useContext, useState, useEffect } from 'react';
import { User as SupabaseUser, Session } from '@supabase/supabase-js';
import { supabase, isSupabaseConfigured } from '../lib/supabase';

export interface AuthUser {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at?: string;
  raw_user?: SupabaseUser;
}

interface AuthContextType {
  user: AuthUser | null;
  session: Session | null;
  token: string | null;
  isAuthenticated: boolean;
  loading: boolean;
  isConfigured: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<{ needsEmailVerification?: boolean }>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

function mapSupabaseUser(sbUser: SupabaseUser | null): AuthUser | null {
  if (!sbUser) return null;
  const fullName =
    sbUser.user_metadata?.full_name ||
    sbUser.user_metadata?.name ||
    sbUser.email?.split('@')[0] ||
    'Usuario';

  return {
    id: sbUser.id,
    email: sbUser.email || '',
    full_name: fullName,
    is_active: true,
    created_at: sbUser.created_at,
    raw_user: sbUser,
  };
}

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [session, setSession] = useState<Session | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const isConfigured = isSupabaseConfigured();

  useEffect(() => {
    let mounted = true;

    async function initSession() {
      if (!isConfigured) {
        setLoading(false);
        return;
      }

      try {
        const { data: { session: initialSession }, error } = await supabase.auth.getSession();
        if (error) {
          console.error('Error al obtener sesión de Supabase:', error.message);
        }
        if (mounted && initialSession) {
          setSession(initialSession);
          setToken(initialSession.access_token);
          setUser(mapSupabaseUser(initialSession.user));
          localStorage.setItem('legadovivo_token', initialSession.access_token);
        }
      } catch (err) {
        console.error('Excepción al inicializar sesión:', err);
      } finally {
        if (mounted) setLoading(false);
      }
    }

    initSession();

    // Suscripción a cambios de sesión en tiempo real (login, logout, refresh de token)
    const { data: authListener } = supabase.auth.onAuthStateChange((_event, currentSession) => {
      if (!mounted) return;

      setSession(currentSession);
      if (currentSession) {
        const mapped = mapSupabaseUser(currentSession.user);
        setUser(mapped);
        setToken(currentSession.access_token);
        localStorage.setItem('legadovivo_token', currentSession.access_token);
        if (mapped) {
          localStorage.setItem('legadovivo_user', JSON.stringify(mapped));
        }
      } else {
        setUser(null);
        setToken(null);
        localStorage.removeItem('legadovivo_token');
        localStorage.removeItem('legadovivo_user');
      }
      setLoading(false);
    });

    return () => {
      mounted = false;
      authListener.subscription.unsubscribe();
    };
  }, [isConfigured]);

  const login = async (email: string, password: string) => {
    if (!isConfigured) {
      throw new Error(
        'Supabase no está configurado. Por favor define VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY en tu archivo .env'
      );
    }

    const { data, error } = await supabase.auth.signInWithPassword({
      email: email.trim(),
      password,
    });

    if (error) {
      if (error.message.includes('Invalid login credentials')) {
        throw new Error('Credenciales inválidas. Por favor verifica tu correo y contraseña.');
      }
      if (error.message.includes('Email not confirmed')) {
        throw new Error('Tu correo electrónico aún no ha sido confirmado. Revisa tu bandeja de entrada.');
      }
      throw new Error(error.message);
    }

    if (data.session) {
      setSession(data.session);
      setToken(data.session.access_token);
      setUser(mapSupabaseUser(data.user));
      localStorage.setItem('legadovivo_token', data.session.access_token);
    }
  };

  const register = async (
    email: string,
    password: string,
    fullName: string
  ): Promise<{ needsEmailVerification?: boolean }> => {
    if (!isConfigured) {
      throw new Error(
        'Supabase no está configurado. Por favor define VITE_SUPABASE_URL y VITE_SUPABASE_ANON_KEY en tu archivo .env'
      );
    }

    const { data, error } = await supabase.auth.signUp({
      email: email.trim(),
      password,
      options: {
        data: {
          full_name: fullName.trim(),
        },
      },
    });

    if (error) {
      if (error.message.includes('User already registered')) {
        throw new Error('Ya existe una cuenta registrada con este correo electrónico.');
      }
      if (error.message.includes('Password should be')) {
        throw new Error('La contraseña debe tener al menos 6 caracteres.');
      }
      throw new Error(error.message);
    }

    // Si Supabase tiene confirmación de email obligatoria, la sesión será null inicialmente
    const needsEmailVerification = !data.session && !!data.user;

    if (data.session) {
      setSession(data.session);
      setToken(data.session.access_token);
      setUser(mapSupabaseUser(data.user));
      localStorage.setItem('legadovivo_token', data.session.access_token);
    }

    return { needsEmailVerification };
  };

  const logout = async () => {
    if (isConfigured) {
      try {
        await supabase.auth.signOut();
      } catch (err) {
        console.warn('Error al cerrar sesión en Supabase:', err);
      }
    }
    setSession(null);
    setUser(null);
    setToken(null);
    localStorage.removeItem('legadovivo_token');
    localStorage.removeItem('legadovivo_user');
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        session,
        token,
        isAuthenticated: !!session || (isConfigured ? false : !!token),
        loading,
        isConfigured,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth debe ser utilizado dentro de un AuthProvider');
  }
  return context;
};
