import { api } from './client'
import type { FreelancerMe, TokenResponse } from '@/types/auth'

export interface LoginPayload {
  email: string
  password: string
}

export interface RegisterPayload {
  email: string
  password: string
  first_name: string
  last_name: string
  username: string
}

export const authApi = {
  /**
   * POST /auth/login
   * Backend uses OAuth2PasswordRequestForm → x-www-form-urlencoded
   * Field is "username" even though it's an email.
   */
  login(payload: LoginPayload): Promise<TokenResponse> {
    const form = new URLSearchParams()
    form.set('username', payload.email)
    form.set('password', payload.password)
    return api.postForm<TokenResponse>('/auth/login', form)
  },

  register(payload: RegisterPayload): Promise<TokenResponse> {
    return api.post<TokenResponse>('/auth/register', payload)
  },

  logout(refreshToken: string): Promise<void> {
    return api.post<void>('/auth/logout', { refresh_token: refreshToken })
  },

  getMe(): Promise<FreelancerMe> {
    return api.get<FreelancerMe>('/freelancers/me')
  },
}
