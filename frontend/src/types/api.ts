export interface Token {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Owner {
  id: number;
  email: string;
  full_name: string | null;
  phone: string | null;
  is_active: boolean;
  created_at: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password: string;
  full_name?: string;
  phone?: string;
}

export interface ApiError {
  detail: string;
}
