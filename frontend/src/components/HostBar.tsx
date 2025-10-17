import HostCard from './HostCard'
import type { HostSummary } from '../types'

type Props = {
  hosts: HostSummary[]
  selectedHostId?: string
  onSelect: (hostId: string) => void
}

export default function HostBar({ hosts, selectedHostId, onSelect }: Props) {
  console.log('HostBar: Received hosts:', hosts)
  return (
    <div className="flex gap-3 overflow-x-auto p-2">
      {hosts.map(h => (
        <HostCard
          key={h.host_id}
          host_id={h.host_id}
          hostname={h.host_id}
          ip_address={h.ip_address}
          status={h.status}
          selected={h.host_id === selectedHostId}
          onClick={() => onSelect(h.host_id)}
        />
      ))}
    </div>
  )
}


