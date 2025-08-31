import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import logger from '../utils/logger';

interface User {
  user_id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  is_owner: boolean;
  tenant_id: number;
  tenant_name: string;
  tenant_subdomain: string;
}

interface LoginResponse {
  access_token: string;
  token_type: string;
}

// Check if JWT is expired
const isTokenExpired = (token: string): boolean => {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    const exp = payload.exp * 1000; // Convert to milliseconds
    const isExpired = Date.now() >= exp;
    logger.debug('Token expiration check', { exp: new Date(exp), now: new Date(), isExpired });
    return isExpired;
  } catch (error) {
    logger.debug('Token parsing failed:', error);
    return true;
  }
};

// Auth API functions
const fetchCurrentUser = async (): Promise<User | null> => {
  const token = localStorage.getItem('token');
  logger.debug('fetchCurrentUser called', { hasToken: !!token });
  
  if (!token) {
    logger.debug('No token found in localStorage');
    return null;
  }

  // Check if token is expired before making request
  if (isTokenExpired(token)) {
    logger.debug('Token expired, removing and redirecting');
    localStorage.removeItem('token');
    window.location.href = '/login';
    return null;
  }

  logger.debug('Making /auth/me request');
  const response = await fetch('/api/v1/auth/me', {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  logger.debug('Auth me response', { status: response.status, ok: response.ok });

  if (!response.ok) {
    if (response.status === 401) {
      logger.debug('401 response, clearing token and redirecting');
      localStorage.removeItem('token');
      window.location.href = '/login';
      return null;
    }
    logger.error('Failed to fetch user', { status: response.status });
    throw new Error('Failed to fetch user');
  }

  const user = await response.json();
  logger.debug('User fetched successfully', { userId: user.user_id, email: user.email });
  return user;
};

const loginUser = async ({ email, password }: { email: string; password: string }): Promise<LoginResponse> => {
  logger.debug('Login attempt', { email });
  
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });

  logger.debug('Login response', { status: response.status, ok: response.ok });

  if (!response.ok) {
    const errorData = await response.json();
    logger.error('Login failed', errorData);
    throw new Error(errorData.detail || 'Login failed');
  }

  const loginData = await response.json();
  logger.debug('Login successful, token received');
  return loginData;
};

export const useAuth = () => {
  const queryClient = useQueryClient();

  const token = localStorage.getItem('token');
  
  const { data: user, isLoading } = useQuery({
    queryKey: ['auth', 'me'],
    queryFn: fetchCurrentUser,
    enabled: !!token,
    staleTime: 10 * 60 * 1000,
    retry: false,
  });

  // Login mutation
  const loginMutation = useMutation({
    mutationFn: loginUser,
    onSuccess: async (data) => {
      logger.debug('Login mutation success, storing token and refetching user');
      localStorage.setItem('token', data.access_token);
      await queryClient.refetchQueries({ queryKey: ['auth', 'me'] });
      logger.debug('User data refetch completed');
    },
    onError: (error) => {
      logger.error('Login mutation failed', { error: error.message });
    },
  });

  const login = async (email: string, password: string) => {
    logger.debug('Login method called');
    await loginMutation.mutateAsync({ email, password });
  };

  const logout = async () => {
    logger.debug('Logout called, calling backend and clearing token');
    
    const token = localStorage.getItem('token');
    if (token) {
      try {
        // Call backend logout endpoint to revoke session
        const response = await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
        
        if (response.ok) {
          logger.debug('Backend logout successful');
        } else {
          logger.error('Backend logout failed', { status: response.status });
        }
      } catch (error) {
        logger.error('Backend logout error', { error });
      }
    }
    
    // Always clear local state regardless of backend success
    localStorage.removeItem('token');
    queryClient.clear(); // Clear all cached data
  };

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    loginError: loginMutation.error,
    isLoggingIn: loginMutation.isPending,
  };
};