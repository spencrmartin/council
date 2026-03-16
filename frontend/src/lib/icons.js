/**
 * Icon registry — maps agent icon names to Lucide icon components.
 * Used throughout the app instead of emojis.
 */
import {
  Bot,
  Brain,
  Cpu,
  Eye,
  Search,
  Target,
  Zap,
  Shield,
  BarChart3,
  Palette,
  Mic,
  Briefcase,
  UserCheck,
  ScanEye,
  ShieldCheck,
  Landmark,
  Armchair,
  Users,
  Hexagon,
  ArrowRight,
  ArrowLeft,
  AlertTriangle,
  Network,
  ScrollText,
  UsersRound,
} from 'lucide-react'

// Agent icon choices (used in CreateAgentForm picker)
export const AGENT_ICONS = [
  { name: 'bot', Icon: Bot },
  { name: 'brain', Icon: Brain },
  { name: 'cpu', Icon: Cpu },
  { name: 'eye', Icon: Eye },
  { name: 'search', Icon: Search },
  { name: 'target', Icon: Target },
  { name: 'zap', Icon: Zap },
  { name: 'shield', Icon: Shield },
  { name: 'bar-chart', Icon: BarChart3 },
  { name: 'palette', Icon: Palette },
]

// Role → icon mapping
export const ROLE_ICONS = {
  speaker: Mic,
  minister: Briefcase,
  delegate: UserCheck,
  observer: ScanEye,
  auditor: ShieldCheck,
}

// Resolve an icon name string to a Lucide component
export function getAgentIcon(iconName) {
  const entry = AGENT_ICONS.find((i) => i.name === iconName)
  return entry ? entry.Icon : Bot
}

// App-wide semantic icons
export {
  Landmark as CouncilIcon,
  Armchair as SeatIcon,
  Users as AgentIcon,
  Hexagon as RegionIcon,
  ArrowRight as InputIcon,
  ArrowLeft as OutputIcon,
  AlertTriangle as WarningIcon,
  Network as GraphIcon,
}

export { ScrollText as ConstitutionIcon } from 'lucide-react'
export { UsersRound as CommunityIcon } from 'lucide-react'
