import axios, { AxiosInstance, AxiosError } from 'axios';
import { Token, ApiError } from '../types/api';

const API_BASE_URL = '/api/v1';

class ApiClient {
  private client: AxiosInstance;
  private token: string | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Load token from localStorage
    const storedToken = localStorage.getItem('access_token');
    if (storedToken) {
      this.setToken(storedToken);
    }

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          this.clearToken();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  setToken(token: string) {
    this.token = token;
    localStorage.setItem('access_token', token);
    this.client.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  }

  clearToken() {
    this.token = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    delete this.client.defaults.headers.common['Authorization'];
  }

  isAuthenticated(): boolean {
    return !!this.token;
  }

  // Auth
  async register(email: string, password: string, fullName?: string) {
    const response = await this.client.post('/auth/register', {
      email,
      password,
      full_name: fullName,
    });
    return response.data;
  }

  async login(email: string, password: string): Promise<Token> {
    const response = await this.client.post<Token>('/auth/login', {
      email,
      password,
    });
    const token = response.data;
    this.setToken(token.access_token);
    localStorage.setItem('refresh_token', token.refresh_token);
    return token;
  }

  async logout() {
    this.clearToken();
  }

  async getMe() {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  // Vehicles
  async getVehicles() {
    const response = await this.client.get('/vehicles');
    return response.data;
  }

  async getVehicle(id: number) {
    const response = await this.client.get(`/vehicles/${id}`);
    return response.data;
  }

  async createVehicle(data: {
    license_plate: string;
    name?: string;
    model?: string;
  }) {
    const response = await this.client.post('/vehicles', data);
    return response.data;
  }

  async getVehicleStatus(id: number) {
    const response = await this.client.get(`/vehicles/${id}/status`);
    return response.data;
  }

  async changeVehicleMode(id: number, mode: string, force = false) {
    const response = await this.client.post(`/vehicles/${id}/mode`, {
      mode,
      force,
    });
    return response.data;
  }

  // Earnings
  async getEarningsSummary(startDate?: string, endDate?: string) {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    const response = await this.client.get(`/earnings?${params}`);
    return response.data;
  }

  async getRealtimeEarnings() {
    const response = await this.client.get('/earnings/realtime');
    return response.data;
  }

  async getEarningsHistory(vehicleId?: number, limit = 50) {
    const params = new URLSearchParams();
    if (vehicleId) params.append('vehicle_id', vehicleId.toString());
    params.append('limit', limit.toString());
    const response = await this.client.get(`/earnings/history?${params}`);
    return response.data;
  }

  async getEarningsByMode() {
    const response = await this.client.get('/earnings/by-mode');
    return response.data;
  }

  async simulateEarnings() {
    const response = await this.client.post('/earnings/simulate');
    return response.data;
  }

  // Yield-Drive AI
  async getYieldPrediction(vehicleId: number, timeHorizon = 4) {
    const response = await this.client.get(
      `/yield/prediction/${vehicleId}?time_horizon=${timeHorizon}`
    );
    return response.data;
  }

  async getRecommendation(vehicleId: number) {
    const response = await this.client.get(`/yield/recommendation/${vehicleId}`);
    return response.data;
  }

  async getMarketData(latitude = 35.6762, longitude = 139.6503) {
    const response = await this.client.get(
      `/yield/market-data?latitude=${latitude}&longitude=${longitude}`
    );
    return response.data;
  }

  async compareModes(vehicleId: number, timeHorizon = 4) {
    const response = await this.client.get(
      `/yield/compare-modes/${vehicleId}?time_horizon=${timeHorizon}`
    );
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
