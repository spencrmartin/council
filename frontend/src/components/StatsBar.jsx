/**
 * StatsBar — floating stats pill at the top of the council view.
 */
import useStore from '@/store/useStore'
import {
  CouncilIcon,
  SeatIcon,
  AgentIcon,
  RegionIcon,
  InputIcon,
  OutputIcon,
} from '@/lib/icons'

export default function StatsBar() {
  const { stats } = useStore()

  const items = [
    { label: 'Seats', value: stats.total_seats || 0, Icon: SeatIcon },
    { label: 'Occupied', value: stats.occupied_seats || 0, Icon: AgentIcon },
    { label: 'Agents', value: stats.total_agents || 0, Icon: AgentIcon },
    { label: 'Regions', value: stats.total_regions || 0, Icon: RegionIcon },
    { label: 'Inputs', value: stats.total_inputs || 0, Icon: InputIcon },
    { label: 'Outputs', value: stats.total_outputs || 0, Icon: OutputIcon },
  ]

  return (
    <div className="inline-flex items-center gap-4 bg-card/80 backdrop-blur-md border border-border rounded-full px-5 py-2 shadow-lg">
      <div className="flex items-center gap-1.5">
        <CouncilIcon className="w-4 h-4 text-foreground" />
        <span className="text-sm font-semibold">Council</span>
      </div>
      <div className="w-px h-4 bg-border" />
      {items.map((item) => (
        <div key={item.label} className="flex items-center gap-1 text-xs">
          <item.Icon className="w-3 h-3 text-muted-foreground" />
          <span className="font-medium">{item.value}</span>
          <span className="text-muted-foreground">{item.label}</span>
        </div>
      ))}
    </div>
  )
}
