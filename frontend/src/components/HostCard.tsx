type Props = {
  host_id: string
  hostname: string
  ip_address: string
  status: 'online' | 'offline'
  selected?: boolean
  onClick?: () => void
}

export default function HostCard({ host_id, hostname, ip_address, status, selected, onClick }: Props) {
  const statusColor = status === 'online' ? 'bg-green-500' : 'bg-gray-400'
  const ring = selected ? 'ring-2 ring-blue-500' : 'ring-1 ring-gray-200'
  return (
    <button onClick={onClick} className={`text-left p-3 rounded-md ${ring} hover:shadow transition bg-white`}> 
      <div className="flex items-center justify-between">
        <div className="font-semibold">{host_id}</div>
        <span className={`inline-block w-2 h-2 rounded-full ${statusColor}`} />
      </div>
      <div className="text-sm text-gray-600">{hostname}</div>
      <div className="text-xs text-gray-500">{ip_address}</div>
    </button>
  )
}


