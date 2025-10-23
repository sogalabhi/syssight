import { useState } from 'react'
import { getProcesses } from '../api/hosts'
import type { Process, ProcessListResponse } from '../types'

type Props = {
  hostId: string
}

type SortField = 'pid' | 'name' | 'cpu_percent' | 'memory_percent'

export default function ProcessTable({ hostId }: Props) {
  const [processes, setProcesses] = useState<Process[]>([])
  const [page, setPage] = useState(1)
  const [limit] = useState(10)
  const [sortBy, setSortBy] = useState<SortField>('cpu_percent')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [totalPages, setTotalPages] = useState(0)
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchProcesses = async () => {
    if (!hostId) return
    
    setLoading(true)
    setError(null)
    
    try {
      const response: ProcessListResponse = await getProcesses(hostId, page, limit, sortBy, sortOrder)
      setProcesses(response.processes)
      setTotalPages(response.total_pages)
      setTotal(response.total)
    } catch (err) {
      console.error('Failed to fetch processes:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch processes')
    } finally {
      setLoading(false)
    }
  }

  // Only fetch processes when explicitly requested (no auto-fetch on load)

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      // Toggle sort order if same field
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      // New field, default to descending
      setSortBy(field)
      setSortOrder('desc')
    }
    setPage(1) // Reset to first page when sorting
    // Fetch data after sorting changes
    fetchProcesses()
  }

  const handlePageChange = (newPage: number) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage)
      // Fetch data after page changes
      fetchProcesses()
    }
  }

  const getSortIcon = (field: SortField) => {
    if (sortBy !== field) return '↕️'
    return sortOrder === 'asc' ? '↑' : '↓'
  }

  const formatPercent = (value: number) => {
    return `${value.toFixed(1)}%`
  }

  if (!hostId) {
    return <div className="text-sm text-gray-500">Select a host to view processes.</div>
  }

  if (processes.length === 0 && !loading && !error) {
    return (
      <div className="space-y-4">
        {/* Header with refresh button */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium">Running Processes</h3>
          <button
            onClick={fetchProcesses}
            disabled={loading}
            className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? 'Loading...' : 'Load Processes'}
          </button>
        </div>
        <div className="text-sm text-gray-500 text-center py-8">
          Click "Load Processes" to fetch process data for this host.
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-sm text-red-500">
        Error: {error}
        <button 
          onClick={fetchProcesses}
          className="ml-2 px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200"
        >
          Retry
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Header with refresh button */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium">Running Processes</h3>
        <button
          onClick={fetchProcesses}
          disabled={loading}
          className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Process count */}
      <div className="text-sm text-gray-600">
        Showing {processes.length} of {total} processes
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-md border border-gray-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th 
                className="px-3 py-2 text-left font-medium text-gray-600 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('pid')}
              >
                PID {getSortIcon('pid')}
              </th>
              <th 
                className="px-3 py-2 text-left font-medium text-gray-600 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('name')}
              >
                Name {getSortIcon('name')}
              </th>
              <th 
                className="px-3 py-2 text-right font-medium text-gray-600 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('cpu_percent')}
              >
                CPU % {getSortIcon('cpu_percent')}
              </th>
              <th 
                className="px-3 py-2 text-right font-medium text-gray-600 cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('memory_percent')}
              >
                Memory % {getSortIcon('memory_percent')}
              </th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr>
                <td colSpan={4} className="px-3 py-8 text-center text-gray-500">
                  Loading processes...
                </td>
              </tr>
            ) : processes.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-3 py-8 text-center text-gray-500">
                  No processes found
                </td>
              </tr>
            ) : (
              processes.map((process) => (
                <tr key={process.pid} className="border-t border-gray-100 hover:bg-gray-50">
                  <td className="px-3 py-2 font-mono text-gray-900">{process.pid}</td>
                  <td className="px-3 py-2 text-gray-900 truncate max-w-xs" title={process.name}>
                    {process.name}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-gray-900">
                    {formatPercent(process.cpu_percent)}
                  </td>
                  <td className="px-3 py-2 text-right tabular-nums text-gray-900">
                    {formatPercent(process.memory_percent)}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            Page {page} of {totalPages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handlePageChange(page - 1)}
              disabled={page <= 1 || loading}
              className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Previous
            </button>
            
            {/* Page numbers */}
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              const pageNum = Math.max(1, Math.min(totalPages - 4, page - 2)) + i
              if (pageNum > totalPages) return null
              
              return (
                <button
                  key={pageNum}
                  onClick={() => handlePageChange(pageNum)}
                  disabled={loading}
                  className={`px-3 py-1 border rounded ${
                    pageNum === page
                      ? 'bg-blue-600 text-white border-blue-600'
                      : 'border-gray-300 hover:bg-gray-50'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  {pageNum}
                </button>
              )
            })}
            
            <button
              onClick={() => handlePageChange(page + 1)}
              disabled={page >= totalPages || loading}
              className="px-3 py-1 border border-gray-300 rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
