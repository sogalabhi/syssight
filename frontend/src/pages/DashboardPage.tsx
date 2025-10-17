import { useEffect, useState } from 'react'
import HostBar from '../components/HostBar'
import MetricsTable from '../components/MetricsTable'
import GraphView from '../components/GraphView'
import GraphFilters from '../components/GraphFilters'
import { MOCK_HOSTS } from '../constants/mock'

export default function DashboardPage() {
  const [selectedHostId, setSelectedHostId] = useState<string | undefined>(undefined)
  const [selectedMetric, setSelectedMetric] = useState<string | undefined>(undefined)
  const [range, setRange] = useState<{ from: string; to: string }>(() => {
    const now = new Date()
    const to = new Date(now)
    const from = new Date(now.getTime() - 60 * 60 * 1000) // last 1h
    const toStr = to.toISOString().slice(0, 16)
    const fromStr = from.toISOString().slice(0, 16)
    return { from: fromStr, to: toStr }
  })

  useEffect(() => {
    // Auto-select first host on mount (mocked)
    if (!selectedHostId && MOCK_HOSTS.length > 0) {
      setSelectedHostId(MOCK_HOSTS[0].host_id)
    }
  }, [selectedHostId])

  // Clear metric when host changes
  useEffect(() => {
    setSelectedMetric(undefined)
  }, [selectedHostId])

  return (
    <div className="max-w-6xl mx-auto p-4 space-y-4">
      <h1 className="text-2xl font-semibold">SysSight Dashboard (Mock)</h1>

      {/* Host tab bar */}
      <HostBar selectedHostId={selectedHostId} onSelect={setSelectedHostId} />

      {/* Latest metrics for selected host */}
      {selectedHostId ? (
        <div className="space-y-2">
          <h2 className="text-lg font-medium">Latest Metrics — {selectedHostId}</h2>
          <MetricsTable hostId={selectedHostId} onSelectMetric={setSelectedMetric} />
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
        <GraphView hostId={selectedHostId} metric={selectedMetric} from={range.from} to={range.to} />
      </div>
    </div>
  )
}


