import { MOCK_LATEST_BY_HOST } from '../constants/mock'
import type { LatestMetrics } from '../constants/mock'

type Props = {
  hostId: string
  onSelectMetric: (metric: string) => void
}

const ROWS: { key: keyof LatestMetrics | 'net_bytes_sent' | 'net_bytes_recv' | 'load_1m' | 'load_5m' | 'load_15m'; label: string; getValue: (m: LatestMetrics) => number }[] = [
  { key: 'cpu_percent', label: 'CPU %', getValue: m => m.cpu_percent },
  { key: 'memory_percent', label: 'Memory %', getValue: m => m.memory_percent },
  { key: 'disk_usage', label: 'Disk %', getValue: m => m.disk_usage['/'].percent },
  { key: 'net_bytes_sent', label: 'Bytes Sent', getValue: m => m.network.bytes_sent },
  { key: 'net_bytes_recv', label: 'Bytes Recv', getValue: m => m.network.bytes_recv },
  { key: 'load_1m', label: 'Load 1m', getValue: m => m.load_average[0] },
  { key: 'load_5m', label: 'Load 5m', getValue: m => m.load_average[1] },
  { key: 'load_15m', label: 'Load 15m', getValue: m => m.load_average[2] },
]

const metricKeyMap: Record<string, string> = {
  cpu_percent: 'cpu_percent',
  memory_percent: 'mem_percent_used',
  disk_usage: 'disk_percent_used',
  net_bytes_sent: 'net_bytes_sent',
  net_bytes_recv: 'net_bytes_received',
  load_1m: 'load_1m',
  load_5m: 'load_5m',
  load_15m: 'load_15m',
}

export default function MetricsTable({ hostId, onSelectMetric }: Props) {
  const latest = MOCK_LATEST_BY_HOST[hostId]
  if (!latest) return <div className="text-gray-500 text-sm">No metrics available.</div>

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
              <td className="px-3 py-2 text-right tabular-nums">{r.getValue(latest)}</td>
              <td className="px-3 py-2 text-right">
                <button
                  onClick={() => onSelectMetric(metricKeyMap[r.key as string])}
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


