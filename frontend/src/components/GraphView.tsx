import type { HistoricalSeries } from '../types'
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
  historicalData: HistoricalSeries | null
  from?: string
  to?: string
}

export default function GraphView({ historicalData, from, to }: Props) {
  console.log('GraphView: Received data:', { historicalData, from, to })
  
  if (!historicalData) {
    return <div className="text-sm text-gray-500">Select a metric to view its historical chart.</div>
  }

  // Filter data by date range if provided (treat inputs as UTC)
  let filteredData = historicalData.data
  if (from && to) {
    const parseUtc = (s: string) => {
      // datetime-local has no TZ; append 'Z' to interpret as UTC
      const str = s.endsWith('Z') || s.includes('+') ? s : `${s}:00Z`.replace(' ', 'T')
      return new Date(str).getTime()
    }

    let fromTime = parseUtc(from)
    let toTime = parseUtc(to)

    // if inputs got reversed, fix it
    if (fromTime > toTime) [fromTime, toTime] = [toTime, fromTime]

    filteredData = historicalData.data.filter(point => {
      const pointTime = new Date(point.timestamp).getTime()
      return pointTime >= fromTime && pointTime <= toTime
    })
  }
  // If no points in range, show an empty-state message
  if (!filteredData.length) {
    return (
      <div className="rounded-md border border-gray-200 bg-white p-3">
        <div className="font-medium mb-1">{historicalData.metric}</div>
        <div className="text-sm text-gray-500">No data in selected date range.</div>
      </div>
    )
  }

  const labels = filteredData.map(point => point.timestamp)
  const data = filteredData.map(point => point.value)

  const chartData = {
    labels,
    datasets: [
      {
        label: historicalData.metric,
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
      <div className="font-medium mb-2">{historicalData.metric}</div>
      <Line key={`${historicalData.metric}|${from}|${to}|${labels.length}`} data={chartData} options={options} />
    </div>
  )
}


