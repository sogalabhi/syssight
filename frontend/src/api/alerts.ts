import apiRequest from './client'
import type { AlertListResponse, AlertStats } from '../types'

export async function getAlerts(
  hostname?: string,
  status?: string,
  severity?: string,
  page: number = 1,
  limit: number = 50
): Promise<AlertListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString()
  })
  
  if (hostname) params.append('hostname', hostname)
  if (status) params.append('status', status)
  if (severity) params.append('severity', severity)
  
  return apiRequest<AlertListResponse>(`/api/v1/alerts?${params}`)
}

export async function getAlertStats(): Promise<AlertStats> {
  return apiRequest<AlertStats>('/api/v1/alerts/stats')
}

export async function resolveAlert(alertId: number): Promise<{ status: string; message: string }> {
  return apiRequest<{ status: string; message: string }>(
    `/api/v1/alerts/${alertId}/resolve`,
    'PATCH'
  )
}
