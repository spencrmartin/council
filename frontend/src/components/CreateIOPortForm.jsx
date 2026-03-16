/**
 * CreateIOPortForm — inline form to create an input or output port.
 */
import { useState } from 'react'
import useStore from '@/store/useStore'
import { InputIcon, OutputIcon } from '@/lib/icons'
import { Plus } from 'lucide-react'

export default function CreateIOPortForm() {
  const { createIOPort, regions } = useStore()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [direction, setDirection] = useState('input')
  const [description, setDescription] = useState('')
  const [regionId, setRegionId] = useState('')
  const [dataType, setDataType] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      await createIOPort({
        name: name.trim(),
        direction,
        description: description.trim() || undefined,
        region_id: regionId || undefined,
        data_type: dataType.trim() || undefined,
      })
      setName('')
      setDescription('')
      setDataType('')
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
        New I/O Port
      </button>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="bg-secondary/50 rounded-lg p-3 space-y-3">
      <div className="flex gap-3">
        <div className="flex-1">
          <label className="text-xs text-muted-foreground">Port Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. user_requests"
            className="w-full mt-1 px-2 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
            autoFocus
          />
        </div>
        <div>
          <label className="text-xs text-muted-foreground">Direction</label>
          <div className="flex gap-1 mt-1">
            <button
              type="button"
              onClick={() => setDirection('input')}
              className={`flex items-center gap-1 text-xs px-2.5 py-1.5 rounded transition-colors ${
                direction === 'input'
                  ? 'bg-blue-500/20 text-blue-400 ring-1 ring-blue-500/40'
                  : 'bg-background text-muted-foreground hover:bg-muted'
              }`}
            >
              <InputIcon className="w-3 h-3" /> IN
            </button>
            <button
              type="button"
              onClick={() => setDirection('output')}
              className={`flex items-center gap-1 text-xs px-2.5 py-1.5 rounded transition-colors ${
                direction === 'output'
                  ? 'bg-emerald-500/20 text-emerald-400 ring-1 ring-emerald-500/40'
                  : 'bg-background text-muted-foreground hover:bg-muted'
              }`}
            >
              <OutputIcon className="w-3 h-3" /> OUT
            </button>
          </div>
        </div>
      </div>

      <div>
        <label className="text-xs text-muted-foreground">Assign to Region</label>
        <select
          value={regionId}
          onChange={(e) => setRegionId(e.target.value)}
          className="w-full mt-1 px-2 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
        >
          <option value="">— None —</option>
          {regions.map((r) => (
            <option key={r.id} value={r.id}>{r.name}</option>
          ))}
        </select>
      </div>

      <div className="flex gap-3">
        <div className="flex-1">
          <label className="text-xs text-muted-foreground">Description</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="What data flows here?"
            className="w-full mt-1 px-2 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
        <div className="w-24">
          <label className="text-xs text-muted-foreground">Data Type</label>
          <input
            type="text"
            value={dataType}
            onChange={(e) => setDataType(e.target.value)}
            placeholder="text"
            className="w-full mt-1 px-2 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
          />
        </div>
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
          {loading ? 'Creating...' : 'Create Port'}
        </button>
      </div>
    </form>
  )
}
