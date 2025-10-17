import { MOCK_HISTORICAL_BY_HOST_METRIC } from '../constants/mock'
import { Line } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  TimeScale,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend, TimeScale)

type Props = {
  hostId?: string
  metric?: string
  from?: string
  to?: string
}

export default function GraphView({ hostId, metric, from, to }: Props) {
  if (!hostId || !metric) {
    return <div className="text-sm text-gray-500">Select a metric to view its historical chart.</div>
  }
  const key = `${hostId}|${metric}`
  const series = MOCK_HISTORICAL_BY_HOST_METRIC[key]
  if (!series) {
    return <div className="text-sm text-gray-500">No historical data for {metric}.</div>
  }

  // Filter data by date range if provided (treat inputs as UTC)
  let filteredValues = series.values
  if (from && to) {
    const parseUtc = (s: string) => {
      // datetime-local has no TZ; append 'Z' to interpret as UTC
      const str = s.endsWith('Z') || s.includes('+') ? s : `${s}:00Z`.replace(' ', 'T')
      return new Date(str).getTime() / 1000
    }

    let fromTime = parseUtc(from)
    let toTime = parseUtc(to)

    // if inputs got reversed, fix it
    if (fromTime > toTime) [fromTime, toTime] = [toTime, fromTime]

    // include full last minute window
    toTime = toTime + 59

    filteredValues = series.values.filter(([t]) => t >= fromTime && t <= toTime)
  }
  // If no points in range, show an empty-state message
  if (!filteredValues.length) {
    return (
      <div className="rounded-md border border-gray-200 bg-white p-3">
        <div className="font-medium mb-1">{series.metric_type} (mock)</div>
        <div className="text-sm text-gray-500">No data in selected date range.</div>
      </div>
    )
  }

  const labels = filteredValues.map(([t]) => new Date(t * 1000).toISOString())
  const data = filteredValues.map(([, v]) => v)

  const chartData = {
    labels,
    datasets: [
      {
        label: series.metric_type,
        data,
        borderColor: 'rgb(37, 99, 235)',
        backgroundColor: 'rgba(37, 99, 235, 0.3)',
        pointRadius: 0,
        tension: 0.3,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      tooltip: { mode: 'index' as const, intersect: false },
    },
    scales: {
      x: { ticks: { maxTicksLimit: 6 } },
      y: { beginAtZero: true },
    },
  }

  return (
    <div className="rounded-md border border-gray-200 bg-white p-3 h-64">
      <div className="font-medium mb-2">{series.metric_type} (mock)</div>
      <Line key={`${hostId}|${metric}|${from}|${to}|${labels.length}`} data={chartData} options={options} />
    </div>
  )
}


