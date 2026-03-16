/**
 * AgentCard — displays an agent with optional seat-assignment actions.
 */
import { useState } from 'react'
import useStore from '@/store/useStore'
import { getAgentIcon, ROLE_ICONS } from '@/lib/icons'
import { Trash2 } from 'lucide-react'

const STATUS_COLORS = {
  active: 'bg-green-500',
  idle: 'bg-yellow-500',
  suspended: 'bg-orange-500',
  offline: 'bg-gray-500',
}

const ROLE_LABELS = {
  speaker: 'Speaker',
  minister: 'Minister',
  delegate: 'Delegate',
  observer: 'Observer',
  auditor: 'Auditor',
}

export default function AgentCard({ agent, showActions = false }) {
  const { selectedSeatId, assignSeat, unseatAgent, deleteAgent } = useStore()
  const [loading, setLoading] = useState(false)

  const AgentIconComponent = getAgentIcon(agent.icon)
  const RoleIcon = ROLE_ICONS[agent.role]

  const handleAssign = async () => {
    if (!selectedSeatId) return
    setLoading(true)
    try {
      await assignSeat(agent.id, selectedSeatId)
    } finally {
      setLoading(false)
    }
  }

  const handleUnseat = async () => {
    setLoading(true)
    try {
      await unseatAgent(agent.id)
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (!confirm(`Delete agent "${agent.name}"?`)) return
    setLoading(true)
    try {
      await deleteAgent(agent.id)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className="bg-secondary/50 rounded-lg p-3 text-sm space-y-2"
      style={{ borderLeft: `3px solid ${agent.color}` }}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div
            className="w-8 h-8 rounded-md flex items-center justify-center"
            style={{ backgroundColor: agent.color + '20' }}
          >
            <AgentIconComponent className="w-4 h-4" style={{ color: agent.color }} />
          </div>
          <div>
            <p className="font-medium">{agent.name}</p>
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              {RoleIcon && <RoleIcon className="w-3 h-3" />}
              <span>{ROLE_LABELS[agent.role] || agent.role}</span>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          <span className={`w-2 h-2 rounded-full ${STATUS_COLORS[agent.status] || STATUS_COLORS.offline}`} />
          <span className="text-xs text-muted-foreground">{agent.status}</span>
        </div>
      </div>

      {agent.description && (
        <p className="text-xs text-muted-foreground">{agent.description}</p>
      )}

      {agent.model_name && (
        <p className="text-xs font-mono text-muted-foreground">
          {agent.model_provider}/{agent.model_name}
        </p>
      )}

      {showActions && (
        <div className="flex gap-2 pt-1">
          {!agent.seat_id && selectedSeatId && (
            <button
              onClick={handleAssign}
              disabled={loading}
              className="text-xs px-2 py-1 rounded bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              Assign to selected seat
            </button>
          )}
          {agent.seat_id && (
            <button
              onClick={handleUnseat}
              disabled={loading}
              className="text-xs px-2 py-1 rounded bg-secondary text-secondary-foreground hover:bg-secondary/80 disabled:opacity-50"
            >
              Unseat
            </button>
          )}
          <button
            onClick={handleDelete}
            disabled={loading}
            className="flex items-center gap-1 text-xs px-2 py-1 rounded text-destructive hover:bg-destructive/10 disabled:opacity-50 ml-auto"
          >
            <Trash2 className="w-3 h-3" />
            Delete
          </button>
        </div>
      )}
    </div>
  )
}
