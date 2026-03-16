/**
 * CreateAgentForm — inline form to add a new agent with Lucide icon picker.
 */
import { useState } from 'react'
import useStore from '@/store/useStore'
import { AGENT_ICONS } from '@/lib/icons'
import { Plus } from 'lucide-react'

const ROLES = ['delegate', 'minister', 'speaker', 'observer', 'auditor']

export default function CreateAgentForm() {
  const { createAgent } = useStore()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [role, setRole] = useState('delegate')
  const [icon, setIcon] = useState('bot')
  const [description, setDescription] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      await createAgent({
        name: name.trim(),
        role,
        icon,
        description: description.trim() || undefined,
      })
      setName('')
      setDescription('')
      setOpen(false)
    } finally {
      setLoading(false)
    }
  }

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="w-full py-2 border border-dashed border-border rounded-lg text-sm text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors flex items-center justify-center gap-1.5"
      >
        <Plus className="w-3.5 h-3.5" />
        New Agent
      </button>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="bg-secondary/50 rounded-lg p-3 space-y-3">
      <div>
        <label className="text-xs text-muted-foreground">Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Agent name..."
          className="w-full mt-1 px-2 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
          autoFocus
        />
      </div>

      <div className="flex gap-3">
        <div className="flex-1">
          <label className="text-xs text-muted-foreground">Role</label>
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="w-full mt-1 px-2 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
          >
            {ROLES.map((r) => (
              <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Icon</label>
          <div className="flex gap-1 mt-1 flex-wrap">
            {AGENT_ICONS.map(({ name: iconName, Icon }) => (
              <button
                key={iconName}
                type="button"
                onClick={() => setIcon(iconName)}
                className={`w-7 h-7 rounded flex items-center justify-center transition-colors ${
                  icon === iconName ? 'bg-primary text-primary-foreground' : 'bg-background hover:bg-muted text-muted-foreground'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
              </button>
            ))}
          </div>
        </div>
      </div>

      <div>
        <label className="text-xs text-muted-foreground">Description (optional)</label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What does this agent do?"
          className="w-full mt-1 px-2 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={() => setOpen(false)}
          className="text-xs px-3 py-1.5 rounded text-muted-foreground hover:text-foreground"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!name.trim() || loading}
          className="text-xs px-3 py-1.5 rounded bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {loading ? 'Creating...' : 'Create Agent'}
        </button>
      </div>
    </form>
  )
}
