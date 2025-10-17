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
