/**
 * CreateRegionForm — inline form to create a region and assign seats.
 */
import { useState } from 'react'
import useStore from '@/store/useStore'
import { Plus } from 'lucide-react'

const COLORS = [
  '#8b5cf6', '#6366f1', '#3b82f6', '#06b6d4',
  '#10b981', '#f59e0b', '#ef4444', '#ec4899',
]

export default function CreateRegionForm() {
  const { createRegion, seats } = useStore()
  const [open, setOpen] = useState(false)
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [color, setColor] = useState('#8b5cf6')
  const [selectedSeats, setSelectedSeats] = useState([])
  const [loading, setLoading] = useState(false)

  // Seats not already in a region
  const availableSeats = seats.filter((s) => !s.region_id)

  const toggleSeat = (seatId) => {
    setSelectedSeats((prev) =>
      prev.includes(seatId)
        ? prev.filter((id) => id !== seatId)
        : [...prev, seatId]
    )
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setLoading(true)
    try {
      await createRegion({
        name: name.trim(),
        description: description.trim() || undefined,
        color,
        seat_ids: selectedSeats,
      })
      setName('')
      setDescription('')
      setSelectedSeats([])
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
        New Region
      </button>
    )
  }

  return (
    <form onSubmit={handleSubmit} className="bg-secondary/50 rounded-lg p-3 space-y-3">
      <div>
        <label className="text-xs text-muted-foreground">Region Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="e.g. Security Committee"
          className="w-full mt-1 px-2 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
          autoFocus
        />
      </div>

      <div>
        <label className="text-xs text-muted-foreground">Color</label>
        <div className="flex gap-1.5 mt-1">
          {COLORS.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setColor(c)}
              className={`w-6 h-6 rounded-full transition-transform ${
                color === c ? 'scale-125 ring-2 ring-white ring-offset-1 ring-offset-background' : 'hover:scale-110'
              }`}
              style={{ backgroundColor: c }}
            />
          ))}
        </div>
      </div>

      <div>
        <label className="text-xs text-muted-foreground">Description (optional)</label>
        <input
          type="text"
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="What is this region responsible for?"
          className="w-full mt-1 px-2 py-1.5 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
        />
      </div>

      <div>
        <label className="text-xs text-muted-foreground">
          Assign Seats ({selectedSeats.length} selected, {availableSeats.length} available)
        </label>
        <div className="mt-1 max-h-32 overflow-y-auto border border-border rounded-md p-2 grid grid-cols-5 gap-1">
          {availableSeats.map((seat) => (
            <button
              key={seat.id}
              type="button"
              onClick={() => toggleSeat(seat.id)}
              className={`text-xs py-1 rounded transition-colors ${
                selectedSeats.includes(seat.id)
                  ? 'text-white'
                  : 'bg-background text-muted-foreground hover:bg-muted'
              }`}
              style={selectedSeats.includes(seat.id) ? { backgroundColor: color } : {}}
            >
              {seat.label || seat.id.slice(0, 4)}
            </button>
          ))}
          {availableSeats.length === 0 && (
            <p className="col-span-5 text-xs text-muted-foreground text-center py-2">
              All seats are assigned to regions
            </p>
          )}
        </div>
      </div>

      <div className="flex gap-2 justify-end">
        <button
          type="button"
          onClick={() => { setOpen(false); setSelectedSeats([]) }}
          className="text-xs px-3 py-1.5 rounded text-muted-foreground hover:text-foreground"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={!name.trim() || loading}
          className="text-xs px-3 py-1.5 rounded bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {loading ? 'Creating...' : 'Create Region'}
        </button>
      </div>
    </form>
  )
}
