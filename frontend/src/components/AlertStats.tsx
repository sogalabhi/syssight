import React, { useState, useEffect } from 'react'
import { getAlertStats } from '../api/alerts'
import type { AlertStats as AlertStatsType } from '../types'

const AlertStats: React.FC = () => {
  const [stats, setStats] = useState<AlertStatsType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await getAlertStats()
      setStats(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch alert stats')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStats()
  }, [])

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Alert Statistics</h3>
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Alert Statistics</h3>
        <div className="text-red-600 text-sm">
          Error: {error}
          <button
            onClick={fetchStats}
            className="ml-2 text-blue-600 hover:text-blue-800 underline"
          >
            Retry
          </button>
        </div>
      </div>
    )
  }

  if (!stats) return null

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-100'
      case 'warning':
        return 'text-yellow-600 bg-yellow-100'
      case 'info':
        return 'text-blue-600 bg-blue-100'
      default:
        return 'text-gray-600 bg-gray-100'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Alert Statistics</h3>
        <button
          onClick={fetchStats}
          className="text-sm text-blue-600 hover:text-blue-800 underline"
        >
          Refresh
        </button>
      </div>
      
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center">
          <div className="text-2xl font-bold text-red-600">{stats.active_count}</div>
          <div className="text-sm text-gray-500">Active Alerts</div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-green-600">{stats.resolved_count}</div>
          <div className="text-sm text-gray-500">Resolved Alerts</div>
        </div>
      </div>
      
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-gray-700">By Severity (Active)</h4>
        {Object.entries(stats.by_severity).map(([severity, count]) => (
          <div key={severity} className="flex items-center justify-between">
            <span className="capitalize text-sm text-gray-600">{severity}</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(severity)}`}>
              {count}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}

export default AlertStats
