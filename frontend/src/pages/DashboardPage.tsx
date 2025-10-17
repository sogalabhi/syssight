import { useEffect, useState } from 'react'
import HostBar from '../components/HostBar'
import MetricsTable from '../components/MetricsTable'
import GraphView from '../components/GraphView'
import GraphFilters from '../components/GraphFilters'
import { getHosts, getLatestMetrics, getHistoricalMetrics } from '../api/hosts'
import type { HostSummary, LatestMetrics, HistoricalSeries } from '../types'

export default function DashboardPage() {
  const [hosts, setHosts] = useState<HostSummary[]>([])
  const [selectedHostId, setSelectedHostId] = useState<string | undefined>(undefined)
  const [selectedMetric, setSelectedMetric] = useState<string | undefined>(undefined)
  const [latestMetrics, setLatestMetrics] = useState<LatestMetrics | null>(null)
  const [historicalData, setHistoricalData] = useState<HistoricalSeries | null>(null)
  const [range, setRange] = useState<{ from: string; to: string }>(() => {
    const now = new Date()
    const to = new Date(now)
    const from = new Date(now.getTime() - 60 * 60 * 1000) // last 1h
    const toStr = to.toISOString().slice(0, 16)
    const fromStr = from.toISOString().slice(0, 16)
    return { from: fromStr, to: toStr }
  })

  // Fetch hosts on mount
  useEffect(() => {
    console.log('DashboardPage: Fetching hosts on mount...')
    getHosts()
      .then(hosts => {
        console.log('DashboardPage: Hosts received:', hosts)
        setHosts(hosts)
      })
      .catch(err => {
        console.error('DashboardPage: Failed to fetch hosts:', err)
      })
  }, [])

  // Auto-select first host when hosts are loaded
  useEffect(() => {
    if (!selectedHostId && hosts.length > 0) {
      setSelectedHostId(hosts[0].host_id)
    }
  }, [hosts, selectedHostId])

  // Clear metric when host changes
  useEffect(() => {
    setSelectedMetric(undefined)
  }, [selectedHostId])

  // Fetch latest metrics when host changes and poll every 5s
  useEffect(() => {
    if (!selectedHostId) return

    const fetchLatest = () => {
      getLatestMetrics(selectedHostId)
        .then(setLatestMetrics)
        .catch(err => console.error('Failed to fetch latest metrics:', err))
    }

    // Fetch immediately
    fetchLatest()

    // Poll every 5 seconds
    const interval = setInterval(fetchLatest, 10000)

    return () => clearInterval(interval)
  }, [selectedHostId])

  // Fetch historical data when metric or filters change
  useEffect(() => {
    console.log('DashboardPage: Historical data effect triggered', {
      selectedHostId,
      selectedMetric,
      range
    })
    
    if (!selectedHostId || !selectedMetric) {
      console.log('DashboardPage: Clearing historical data - missing host or metric')
      setHistoricalData(null)
      return
    }

    console.log('DashboardPage: Fetching historical data for', selectedMetric)
    getHistoricalMetrics(selectedHostId, selectedMetric, range.from, range.to)
      .then(data => {
        console.log('DashboardPage: Historical data received:', data)
        setHistoricalData(data)
      })
      .catch(err => {
        console.error('DashboardPage: Failed to fetch historical data:', err)
      })
  }, [selectedHostId, selectedMetric, range.from, range.to])

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-4">
      <h1 className="text-2xl font-semibold">SysSight Dashboard</h1>

      {/* Host tab bar */}
      <HostBar hosts={hosts} selectedHostId={selectedHostId} onSelect={setSelectedHostId} />

      {/* Latest metrics for selected host */}
      {selectedHostId ? (
        <div className="space-y-2">
          <h2 className="text-lg font-medium">Latest Metrics — {selectedHostId}</h2>
          <MetricsTable latestMetrics={latestMetrics} onSelectMetric={setSelectedMetric} />
        </div>
      ) : (
        <div className="text-sm text-gray-500">Select a host to view metrics.</div>
      )}

      {/* Single graph view */}
      <div className="space-y-2">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-medium">Graph</h2>
          <GraphFilters from={range.from} to={range.to} onChange={setRange} />
        </div>
        <GraphView historicalData={historicalData} from={range.from} to={range.to} />
      </div>
    </div>
  )
}


