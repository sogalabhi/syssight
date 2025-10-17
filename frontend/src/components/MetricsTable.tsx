import type { LatestMetrics } from '../types'

type Props = {
  latestMetrics: LatestMetrics | null
  onSelectMetric: (metric: string) => void
}

const ROWS: { key: keyof LatestMetrics; label: string; getValue: (m: LatestMetrics) => number }[] = [
  { key: 'cpu_percent', label: 'CPU %', getValue: m => m.cpu_percent },
  { key: 'mem_percent_used', label: 'Memory %', getValue: m => m.mem_percent_used },
  { key: 'disk_percent_used', label: 'Disk %', getValue: m => m.disk_percent_used },
  { key: 'network_bytes_sent', label: 'Bytes Sent', getValue: m => m.network_bytes_sent },
  { key: 'network_bytes_recv', label: 'Bytes Recv', getValue: m => m.network_bytes_recv },
  { key: 'load_avg_1m', label: 'Load 1m', getValue: m => m.load_avg_1m },
  { key: 'load_avg_5m', label: 'Load 5m', getValue: m => m.load_avg_5m },
  { key: 'load_avg_15m', label: 'Load 15m', getValue: m => m.load_avg_15m },
]

const metricKeyMap: Record<string, string> = {
  cpu_percent: 'cpu_percent',
  mem_percent_used: 'mem_percent_used',
  disk_percent_used: 'disk_percent_used',
  network_bytes_sent: 'network_bytes_sent',
  network_bytes_recv: 'network_bytes_recv',
  load_avg_1m: 'load_avg_1m',
  load_avg_5m: 'load_avg_5m',
  load_avg_15m: 'load_avg_15m',
}

export default function MetricsTable({ latestMetrics, onSelectMetric }: Props) {
  if (!latestMetrics) return <div className="text-gray-500 text-sm">Loading metrics...</div>

  return (
    <div className="overflow-hidden rounded-md border border-gray-200 bg-white">
      <table className="min-w-full text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-3 py-2 text-left font-medium text-gray-600">Metric</th>
            <th className="px-3 py-2 text-right font-medium text-gray-600">Value</th>
            <th className="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {ROWS.map(r => (
            <tr key={r.key} className="border-t border-gray-100">
              <td className="px-3 py-2">{r.label}</td>
              <td className="px-3 py-2 text-right tabular-nums">{r.getValue(latestMetrics)}</td>
              <td className="px-3 py-2 text-right">
                <button
                  onClick={() => {
                    const metricKey = metricKeyMap[r.key as string]
                    console.log('MetricsTable: Graph button clicked for metric:', metricKey)
                    onSelectMetric(metricKey)
                  }}
                  className="px-3 py-1 rounded bg-blue-600 text-white hover:bg-blue-700"
                >
                  Graph
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}


