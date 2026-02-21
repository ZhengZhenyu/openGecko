import apiClient from './index'
import type { Community } from '../stores/auth'

export interface CommunityCreate {
  name: string
  slug: string
  description?: string
  url?: string
  logo_url?: string
}

export interface CommunityUpdate {
  name?: string
  slug?: string
  description?: string
  url?: string
  logo_url?: string
  is_active?: boolean
}

export interface CommunityUser {
  id: number
  username: string
  email: string
  full_name: string
  is_superuser: boolean
  role: string
}

export async function getCommunities(): Promise<Community[]> {
  const { data } = await apiClient.get<{ items: Community[]; total: number; page: number; page_size: number }>('/communities')
  return data.items
}

export async function getCommunity(id: number): Promise<Community> {
  const { data } = await apiClient.get<Community>(`/communities/${id}`)
  return data
}

export async function createCommunity(community: CommunityCreate): Promise<Community> {
  const { data } = await apiClient.post<Community>('/communities', community)
  return data
}

export async function updateCommunity(
  id: number,
  updates: CommunityUpdate
): Promise<Community> {
  const { data } = await apiClient.put<Community>(`/communities/${id}`, updates)
  return data
}

export interface CommunityBasicUpdate {
  name?: string
  description?: string
  logo_url?: string
  url?: string
}

/** 社区管理员可更新基本信息（名称/描述/Logo/链接），不涉及 SMTP/渠道等敏感配置 */
export async function updateCommunityBasic(
  id: number,
  updates: CommunityBasicUpdate
): Promise<Community> {
  const { data } = await apiClient.put<Community>(`/communities/${id}/basic`, updates)
  return data
}

export async function deleteCommunity(id: number): Promise<void> {
  await apiClient.delete(`/communities/${id}`)
}

export async function getCommunityUsers(communityId: number): Promise<CommunityUser[]> {
  const { data } = await apiClient.get<CommunityUser[]>(
    `/communities/${communityId}/users`
  )
  return data
}

export async function addUserToCommunity(
  communityId: number,
  userId: number,
  role?: string
): Promise<void> {
  await apiClient.post(`/communities/${communityId}/users`, { user_id: userId, role })
}

export async function removeUserFromCommunity(
  communityId: number,
  userId: number
): Promise<void> {
  await apiClient.delete(`/communities/${communityId}/users/${userId}`)
}

export async function updateUserRole(
  communityId: number,
  userId: number,
  role: string
): Promise<void> {
  await apiClient.put(`/communities/${communityId}/users/${userId}/role`, null, {
    params: { role },
  })
}

// Email Settings Types
export interface EmailSmtpConfig {
  host: string
  port: number
  username: string
  password?: string
  use_tls: boolean
}

export interface EmailSettings {
  enabled: boolean
  provider: string
  from_email: string
  from_name?: string
  reply_to?: string
  smtp: EmailSmtpConfig
}

export interface EmailSettingsOut {
  enabled: boolean
  provider: string
  from_email: string
  from_name?: string
  reply_to?: string
  smtp: Record<string, any>
}

export async function getEmailSettings(communityId: number): Promise<EmailSettingsOut> {
  const { data } = await apiClient.get<EmailSettingsOut>(
    `/communities/${communityId}/email-settings`
  )
  return data
}

export async function updateEmailSettings(
  communityId: number,
  settings: EmailSettings
): Promise<void> {
  await apiClient.put(`/communities/${communityId}/email-settings`, settings)
}

export async function testEmailSettings(
  communityId: number,
  toEmail: string
): Promise<{ message: string }> {
  const { data } = await apiClient.post<{ message: string }>(
    `/communities/${communityId}/email-settings/test`,
    { to_email: toEmail }
  )
  return data
}
