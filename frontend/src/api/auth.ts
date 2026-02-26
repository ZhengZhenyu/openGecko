import apiClient from './index'
import type { User, Community } from '../stores/auth'

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  is_default_admin: boolean
}

export interface UserInfoResponse {
  user: User
  communities: Community[]
}

export interface SystemStatusResponse {
  needs_setup: boolean
  message: string
}

export interface InitialSetupRequest {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface PasswordResetRequestData {
  email: string
}

export interface PasswordResetConfirmData {
  token: string
  new_password: string
}

export async function login(credentials: LoginRequest): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/auth/login', credentials)
  return data
}

export async function getUserInfo(): Promise<UserInfoResponse> {
  const { data } = await apiClient.get<UserInfoResponse>('/auth/me')
  return data
}

export async function register(userData: {
  username: string
  email: string
  password: string
  full_name?: string
  is_superuser?: boolean
}): Promise<User> {
  const { data } = await apiClient.post<User>('/auth/register', userData)
  return data
}

export async function getSystemStatus(): Promise<SystemStatusResponse> {
  const { data } = await apiClient.get<SystemStatusResponse>('/auth/status')
  return data
}

export async function initialSetup(setupData: InitialSetupRequest): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>('/auth/setup', setupData)
  return data
}

export async function requestPasswordReset(email: string): Promise<{ message: string; reset_url?: string; token?: string }> {
  const { data } = await apiClient.post('/auth/password-reset/request', { email })
  return data
}

export async function confirmPasswordReset(token: string, new_password: string): Promise<{ message: string }> {
  const { data } = await apiClient.post('/auth/password-reset/confirm', { token, new_password })
  return data
}

export async function listAllUsers(): Promise<User[]> {
  const { data } = await apiClient.get<User[]>('/auth/users')
  return data
}

export async function updateUser(userId: number, userData: {
  email?: string
  full_name?: string
  is_superuser?: boolean
  is_active?: boolean
}): Promise<User> {
  const { data } = await apiClient.patch<User>(`/auth/users/${userId}`, userData)
  return data
}

export async function deleteUser(userId: number): Promise<void> {
  await apiClient.delete(`/auth/users/${userId}`)
}

export interface SelfProfileUpdateRequest {
  full_name?: string
  email?: string
  current_password?: string
  new_password?: string
}

export async function updateMyProfile(data: SelfProfileUpdateRequest): Promise<User> {
  const res = await apiClient.patch<User>('/auth/me', data)
  return res.data
}
