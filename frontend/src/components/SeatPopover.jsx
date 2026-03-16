/**
 * SeatPopover — context menu that appears when clicking a seat.
 *
 * Empty seat  → pick an unseated agent to assign, or quick-create one
 * Occupied    → change role, unseat, or view agent details
 */
import { useState, useRef, useEffect } from 'react'
import { motion } from 'framer-motion'
import useStore from '@/store/useStore'
import { getAgentIcon, ROLE_ICONS } from '@/lib/icons'
import {
  Armchair, UserPlus, UserMinus, X,
  Briefcase, Mic, UserCheck, ScanEye, ShieldCheck,
} from 'lucide-react'

const ROLES = [
  { key: 'delegate', label: 'Delegate', Icon: UserCheck },
  { key: 'minister', label: 'Minister', Icon: Briefcase },
  { key: 'speaker', label: 'Speaker', Icon: Mic },
  { key: 'observer', label: 'Observer', Icon: ScanEye },
  { key: 'auditor', label: 'Auditor', Icon: ShieldCheck },
]

export default function SeatPopover() {
  const {
    seatPopover, closeSeatPopover,
    seats, agents,
    assignSeat, unseatAgent, updateAgent, createAgent,
  } = useStore()

  const popoverRef = useRef(null)
  const [view, setView] = useState('main') // 'main' | 'assign' | 'role' | 'create'
  const [creating, setCreating] = useState(false)
  const [newName, setNewName] = useState('')
  const [loading, setLoading] = useState(false)

  // Reset view when popover opens on a new seat
  useEffect(() => {
    setView('main')
    setNewName('')
  }, [seatPopover?.seatId])

  // Close on outside click
  useEffect(() => {
    if (!seatPopover) return
    const handle = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        closeSeatPopover()
      }
    }
    // Delay so the opening click doesn't immediately close it
    const timer = setTimeout(() => window.addEventListener('mousedown', handle), 0)
    return () => { clearTimeout(timer); window.removeEventListener('mousedown', handle) }
  }, [seatPopover, closeSeatPopover])

  // Close on Escape
  useEffect(() => {
    if (!seatPopover) return
    const handle = (e) => { if (e.key === 'Escape') closeSeatPopover() }
    window.addEventListener('keydown', handle)
    return () => window.removeEventListener('keydown', handle)
  }, [seatPopover, closeSeatPopover])

  if (!seatPopover) return null

  const seat = seats.find((s) => s.id === seatPopover.seatId)
  if (!seat) return null

  const agent = seat.agent_id ? agents.find((a) => a.id === seat.agent_id) : null
  const unseatedAgents = agents.filter((a) => !a.seat_id)

  // Position: clamp so popover stays on screen
  const popW = 260
  const popH = 300
  const x = Math.min(seatPopover.x, window.innerWidth - popW - 16)
  const y = Math.min(seatPopover.y + 12, window.innerHeight - popH - 16)

  const handleAssign = async (agentId) => {
    setLoading(true)
    try {
      await assignSeat(agentId, seat.id)
      closeSeatPopover()
    } finally {
      setLoading(false)
    }
  }

  const handleUnseat = async () => {
    setLoading(true)
    try {
      await unseatAgent(agent.id)
      closeSeatPopover()
    } finally {
      setLoading(false)
    }
  }

  const handleRoleChange = async (role) => {
    setLoading(true)
    try {
      await updateAgent(agent.id, { role })
      closeSeatPopover()
    } finally {
      setLoading(false)
    }
  }

  const handleQuickCreate = async () => {
    if (!newName.trim()) return
    setLoading(true)
    try {
      const created = await createAgent({ name: newName.trim() })
      await assignSeat(created.id, seat.id)
      closeSeatPopover()
    } finally {
      setLoading(false)
    }
  }

  const AgentIcon = agent ? getAgentIcon(agent.icon) : null
  const RoleIcon = agent ? ROLE_ICONS[agent.role] : null

  return (
    <motion.div
      ref={popoverRef}
      initial={{ opacity: 0, scale: 0.95, y: -4 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: -4 }}
      transition={{ duration: 0.12, ease: 'easeOut' }}
      className="fixed z-50"
      style={{ left: x, top: y, width: popW }}
    >
      <div className="bg-card/95 backdrop-blur-xl border border-border/50 rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-border">
          <div className="flex items-center gap-2">
            <Armchair className="w-3.5 h-3.5 text-muted-foreground" />
            <span className="text-xs font-semibold text-muted-foreground">
              {seat.label || `Seat ${seat.id.slice(0, 6)}`}
            </span>
            <span className="text-[10px] text-muted-foreground/60">
              Row {seat.row + 1}
            </span>
          </div>
          <button
            onClick={closeSeatPopover}
            className="text-muted-foreground hover:text-foreground transition-colors"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-2">
          {/* ── Main view ── */}
          {view === 'main' && !agent && (
            <div className="space-y-1">
              <p className="text-xs text-muted-foreground px-2 py-1">Empty seat</p>
              <button
                onClick={() => setView('assign')}
                disabled={unseatedAgents.length === 0}
                className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-sm text-left transition-colors hover:bg-muted/50 disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <UserPlus className="w-4 h-4 text-muted-foreground" />
                <div>
                  <span className="text-foreground">Assign agent</span>
                  <span className="text-[10px] text-muted-foreground ml-1.5">
                    {unseatedAgents.length} available
                  </span>
                </div>
              </button>
              <button
                onClick={() => setView('create')}
                className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-sm text-left transition-colors hover:bg-muted/50"
              >
                <UserPlus className="w-4 h-4 text-blue-400" />
                <span className="text-foreground">Create & assign new agent</span>
              </button>
            </div>
          )}

          {view === 'main' && agent && (
            <div className="space-y-1">
              {/* Agent info */}
              <div className="flex items-center gap-2.5 px-2.5 py-2">
                <div
                  className="w-8 h-8 rounded-md flex items-center justify-center shrink-0"
                  style={{ backgroundColor: agent.color + '20' }}
                >
                  {AgentIcon && <AgentIcon className="w-4 h-4" style={{ color: agent.color }} />}
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium truncate">{agent.name}</p>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    {RoleIcon && <RoleIcon className="w-3 h-3" />}
                    <span className="capitalize">{agent.role}</span>
                    <span className="text-muted-foreground/40 mx-0.5">·</span>
                    <span>{agent.status}</span>
                  </div>
                </div>
              </div>

              <div className="h-px bg-border mx-1" />

              <button
                onClick={() => setView('role')}
                className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-sm text-left transition-colors hover:bg-muted/50"
              >
                <Briefcase className="w-4 h-4 text-muted-foreground" />
                <span>Change role</span>
              </button>
              <button
                onClick={handleUnseat}
                disabled={loading}
                className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-sm text-left transition-colors hover:bg-destructive/10 text-destructive disabled:opacity-50"
              >
                <UserMinus className="w-4 h-4" />
                <span>Remove from seat</span>
              </button>
            </div>
          )}

          {/* ── Assign view: pick from unseated agents ── */}
          {view === 'assign' && (
            <div className="space-y-1">
              <button
                onClick={() => setView('main')}
                className="text-xs text-muted-foreground hover:text-foreground px-2 py-1 transition-colors"
              >
                ← Back
              </button>
              <div className="max-h-48 overflow-y-auto space-y-0.5">
                {unseatedAgents.map((a) => {
                  const Icon = getAgentIcon(a.icon)
                  return (
                    <button
                      key={a.id}
                      onClick={() => handleAssign(a.id)}
                      disabled={loading}
                      className="flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-sm text-left transition-colors hover:bg-muted/50 disabled:opacity-50"
                    >
                      <div
                        className="w-6 h-6 rounded flex items-center justify-center shrink-0"
                        style={{ backgroundColor: a.color + '20' }}
                      >
                        <Icon className="w-3 h-3" style={{ color: a.color }} />
                      </div>
                      <div className="min-w-0">
                        <p className="text-foreground truncate">{a.name}</p>
                        <p className="text-[10px] text-muted-foreground capitalize">{a.role}</p>
                      </div>
                    </button>
                  )
                })}
                {unseatedAgents.length === 0 && (
                  <p className="text-xs text-muted-foreground text-center py-4">
                    All agents are seated
                  </p>
                )}
              </div>
            </div>
          )}

          {/* ── Role view: pick a new role ── */}
          {view === 'role' && agent && (
            <div className="space-y-1">
              <button
                onClick={() => setView('main')}
                className="text-xs text-muted-foreground hover:text-foreground px-2 py-1 transition-colors"
              >
                ← Back
              </button>
              {ROLES.map(({ key, label, Icon }) => (
                <button
                  key={key}
                  onClick={() => handleRoleChange(key)}
                  disabled={loading || agent.role === key}
                  className={`flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-sm text-left transition-colors disabled:opacity-50 ${
                    agent.role === key
                      ? 'bg-primary/10 text-foreground font-medium'
                      : 'hover:bg-muted/50'
                  }`}
                >
                  <Icon className="w-4 h-4 text-muted-foreground" />
                  <span>{label}</span>
                  {agent.role === key && (
                    <span className="text-[10px] text-muted-foreground ml-auto">current</span>
                  )}
                </button>
              ))}
            </div>
          )}

          {/* ── Quick create view ── */}
          {view === 'create' && (
            <div className="space-y-2">
              <button
                onClick={() => setView('main')}
                className="text-xs text-muted-foreground hover:text-foreground px-2 py-1 transition-colors"
              >
                ← Back
              </button>
              <div className="px-1">
                <input
                  type="text"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleQuickCreate() }}
                  placeholder="Agent name..."
                  className="w-full px-2.5 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
                  autoFocus
                />
              </div>
              <div className="flex justify-end px-1">
                <button
                  onClick={handleQuickCreate}
                  disabled={!newName.trim() || loading}
                  className="text-xs px-3 py-1.5 rounded-md bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50"
                >
                  {loading ? 'Creating...' : 'Create & Assign'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
