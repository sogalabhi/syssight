type Props = {
  from: string
  to: string
  onChange: (next: { from: string; to: string }) => void
}

export default function GraphFilters({ from, to, onChange }: Props) {
  return (
    <div className="flex flex-wrap items-end gap-3">
      <div>
        <label className="block text-xs text-gray-600 mb-1">From</label>
        <input
          type="datetime-local"
          value={from}
          onChange={e => onChange({ from: e.target.value, to })}
          className="border border-gray-300 rounded px-2 py-1 text-sm bg-white"
        />
      </div>
      <div>
        <label className="block text-xs text-gray-600 mb-1">To</label>
        <input
          type="datetime-local"
          value={to}
          onChange={e => onChange({ from, to: e.target.value })}
          className="border border-gray-300 rounded px-2 py-1 text-sm bg-white"
        />
      </div>
    </div>
  )
}


