import React, { useState, useEffect } from 'react'
import { getThresholds, updateThresholds, resetThresholds } from '../api/thresholds'
import type { ThresholdConfig } from '../types'

const ThresholdSettings: React.FC = () => {
  const [thresholds, setThresholds] = useState<ThresholdConfig[]>([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    loadThresholds()
  }, [])

  const loadThresholds = async () => {
    try {
      setLoading(true)
      const response = await getThresholds()
      setThresholds(response.thresholds)
    } catch (error) {
      console.error('Failed to load thresholds:', error)
      setMessage({ type: 'error', text: 'Failed to load thresholds' })
    } finally {
      setLoading(false)
    }
  }

  const handleThresholdChange = (index: number, value: number) => {
    const newThresholds = [...thresholds]
    newThresholds[index] = { ...newThresholds[index], threshold_value: value }
    setThresholds(newThresholds)
  }

  const handleSave = async () => {
    try {
      setSaving(true)
      setMessage(null)
      await updateThresholds({ thresholds })
      setMessage({ type: 'success', text: 'Thresholds updated successfully! Agents will fetch new values within 20 seconds.' })
      setTimeout(() => setMessage(null), 5000)
    } catch (error) {
      console.error('Failed to save thresholds:', error)
      setMessage({ type: 'error', text: 'Failed to save thresholds' })
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (!window.confirm('Are you sure you want to reset all thresholds to defaults?')) {
      return
    }

    try {
      setResetting(true)
      setMessage(null)
      const response = await resetThresholds()
      setThresholds(response.thresholds)
      setMessage({ type: 'success', text: 'Thresholds reset to defaults' })
      setTimeout(() => setMessage(null), 5000)
    } catch (error) {
      console.error('Failed to reset thresholds:', error)
      setMessage({ type: 'error', text: 'Failed to reset thresholds' })
    } finally {
      setResetting(false)
    }
  }

  const getMetricLabel = (metricName: string): string => {
    const labels: { [key: string]: string } = {
      'cpu_percent': 'CPU Usage',
      'mem_percent_used': 'Memory Usage',
      'disk_percent_used': 'Disk Usage'
    }
    return labels[metricName] || metricName
  }

  const getSeverityColor = (severity: string): string => {
    switch (severity) {
      case 'critical':
        return 'text-red-600 bg-red-50'
      case 'warning':
        return 'text-yellow-600 bg-yellow-50'
      case 'info':
        return 'text-blue-600 bg-blue-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
            <div className="h-10 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Threshold Configuration</h3>
          <p className="mt-1 text-sm text-gray-600">
            Configure alert thresholds for all hosts. Changes apply globally and agents fetch updates every 20 seconds.
          </p>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleReset}
            disabled={saving || resetting}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {resetting ? 'Resetting...' : 'Reset to Defaults'}
          </button>
          <button
            onClick={handleSave}
            disabled={saving || resetting}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>

      {message && (
        <div
          className={`mb-4 p-4 rounded-md ${
            message.type === 'success'
              ? 'bg-green-50 text-green-800 border border-green-200'
              : 'bg-red-50 text-red-800 border border-red-200'
          }`}
        >
          {message.text}
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Metric
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Condition
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Threshold Value (%)
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Severity
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {thresholds.map((threshold, index) => (
              <tr key={index} className="hover:bg-gray-50">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                  {getMetricLabel(threshold.metric_name)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {threshold.operator}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <input
                    type="number"
                    value={threshold.threshold_value}
                    onChange={(e) => handleThresholdChange(index, parseFloat(e.target.value))}
                    min="0"
                    max="100"
                    step="0.1"
                    className="w-24 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-3 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${getSeverityColor(threshold.severity)}`}>
                    {threshold.severity.toUpperCase()}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="mt-4 text-sm text-gray-500">
        <p>
          <strong>Note:</strong> Thresholds are applied globally to all hosts. 
          Agents automatically fetch and apply changes every 20 seconds.
        </p>
      </div>
    </div>
  )
}

export default ThresholdSettings

