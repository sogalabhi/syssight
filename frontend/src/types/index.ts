// Type definitions for the SysSight dashboard

export interface HostSummary {
  host_id: string
  ip_address: string
  status: 'online' | 'offline'
  last_seen: string
}

export interface LatestMetrics {
  host_id: string
  timestamp: string
  cpu_percent: number
  mem_percent_used: number
  disk_percent_used: number
  network_bytes_sent: number
  network_bytes_recv: number
  load_avg_1m: number
  load_avg_5m: number
  load_avg_15m: number
  processes: number
  uptime_seconds: number
}

export interface HistoricalPoint {
  timestamp: string
  value: number
}

export interface HistoricalSeries {
  metric: string
  data: HistoricalPoint[]
}

export interface Process {
  pid: number
  name: string
  cpu_percent: number
  memory_percent: number
}

export interface ProcessListResponse {
  processes: Process[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface Alert {
  id: number
  hostname: string
  metric_name: string
  metric_value: number
  threshold_value: number
  severity: 'info' | 'warning' | 'critical'
  status: 'active' | 'resolved' | 'acknowledged'
  message: string
  triggered_at: string
  resolved_at: string | null
  resolved_by: string | null
}

export interface AlertListResponse {
  alerts: Alert[]
  total: number
  page: number
  limit: number
  total_pages: number
}

export interface AlertStats {
  active_count: number
  resolved_count: number
  by_severity: {
    info: number
    warning: number
    critical: number
  }
}

export interface ThresholdConfig {
  id?: number
  metric_name: string
  operator: string
  threshold_value: number
  severity: 'info' | 'warning' | 'critical'
  enabled: boolean
}

export interface ThresholdConfigResponse {
  thresholds: ThresholdConfig[]
}

export interface ThresholdConfigUpdate {
  thresholds: ThresholdConfig[]
}
