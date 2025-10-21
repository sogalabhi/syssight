import apiRequest from './client'
import type { HostSummary, LatestMetrics, HistoricalSeries, ProcessListResponse } from '../types'

export async function getHosts(): Promise<HostSummary[]> {
  console.log('Fetching hosts from API...')
  const result = await apiRequest<HostSummary[]>('/api/v1/hosts')
  console.log('Hosts fetched:', result)
  return result
}

export async function getLatestMetrics(hostId: string): Promise<LatestMetrics> {
  const response = await apiRequest<any>(`/api/v1/hosts/${hostId}/metrics/latest`)
  
  // Transform API response to match our frontend types
  return {
    host_id: response.host_id,
    timestamp: response.timestamp,
    cpu_percent: response.cpu_percent,
    mem_percent_used: response.memory_percent,
    disk_percent_used: response.disk_usage?.['/']?.percent || 0,
    network_bytes_sent: response.network?.bytes_sent || 0,
    network_bytes_recv: response.network?.bytes_recv || 0,
    load_avg_1m: response.load_average?.[0] || 0,
    load_avg_5m: response.load_average?.[1] || 0,
    load_avg_15m: response.load_average?.[2] || 0,
    processes: 0, // Not available in API
    uptime_seconds: 0, // Not available in API
  }
}

export async function getHistoricalMetrics(
  hostId: string,
  metric: string,
  from: string,
  to: string,
  step: string = '1m'
): Promise<HistoricalSeries> {
  // Convert datetime-local inputs to ISO8601 with timezone
  const fromIso = from.endsWith('Z') || from.includes('+') ? from : `${from}:00Z`.replace(' ', 'T')
  const toIso = to.endsWith('Z') || to.includes('+') ? to : `${to}:00Z`.replace(' ', 'T')
  
  const params = new URLSearchParams({
    start_time: fromIso,
    end_time: toIso,
    step
  })
  
  const response = await apiRequest<any>(`/api/v1/hosts/${hostId}/metrics/historical/${metric}?${params}`)
  
  // Transform API response to match our frontend types
  return {
    metric: response.metric_type,
    data: response.values.map(([timestamp, value]: [number, number]) => ({
      timestamp: new Date(timestamp * 1000).toISOString(),
      value: value
    }))
  }
}

export async function getProcesses(
  hostId: string,
  page: number = 1,
  limit: number = 10,
  sortBy: string = 'cpu_percent',
  sortOrder: 'asc' | 'desc' = 'desc'
): Promise<ProcessListResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    sort_by: sortBy,
    sort_order: sortOrder
  })
  
  return apiRequest<ProcessListResponse>(`/api/v1/hosts/${hostId}/processes?${params}`)
}
