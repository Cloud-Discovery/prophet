import apiClient from './client'

export interface LoginRequest {
  username: string
  password: string
  captcha_id: string
  captcha_code: string
}

export interface RegisterRequest {
  username: string
  email: string
  password: string
  captcha_id: string
  captcha_code: string
}

export interface CaptchaResponse {
  captcha_id: string
  image: string
}

export const authApi = {
  getCaptcha: () => apiClient.get<CaptchaResponse>('/auth/captcha'),
  
  login: (data: LoginRequest) => apiClient.post('/auth/login', data),
  
  register: (data: RegisterRequest) => apiClient.post('/auth/register', data),
  
  getCurrentUser: () => apiClient.get('/auth/me'),
  
  logout: () => apiClient.post('/auth/logout'),
}

