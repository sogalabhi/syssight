import HostCard from './HostCard'
import { MOCK_HOSTS } from '../constants/mock'
import type { HostSummary } from '../constants/mock'

type Props = {
  selectedHostId?: string
  onSelect: (hostId: string) => void
}

export default function HostBar({ selectedHostId, onSelect }: Props) {
  const hosts: HostSummary[] = MOCK_HOSTS
  return (
    <div className="flex gap-3 overflow-x-auto p-2">
      {hosts.map(h => (
        <HostCard
          key={h.host_id}
          host_id={h.host_id}
          hostname={h.hostname}
          ip_address={h.ip_address}
          status={h.status}
          selected={h.host_id === selectedHostId}
          onClick={() => onSelect(h.host_id)}
        />
      ))}
    </div>
  )
}


