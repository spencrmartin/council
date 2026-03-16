/**
 * RegionCard — displays a region with its I/O ports and seat count.
 */
import { useState } from 'react'
import useStore from '@/store/useStore'
import { InputIcon, OutputIcon } from '@/lib/icons'
import { Trash2 } from 'lucide-react'

export default function RegionCard({ region }) {
  const { ioPorts, seats, deleteRegion, selectRegion, selectedRegionId } = useStore()
  const [loading, setLoading] = useState(false)

  const regionInputs = ioPorts.filter(
    (p) => p.region_id === region.id && p.direction === 'input'
  )
  const regionOutputs = ioPorts.filter(
    (p) => p.region_id === region.id && p.direction === 'output'
  )
  const regionSeats = seats.filter((s) => s.region_id === region.id)
  const occupiedSeats = regionSeats.filter((s) => s.agent_id)

  const isSelected = selectedRegionId === region.id

  const handleDelete = async () => {
    if (!confirm(`Delete region "${region.name}"?`)) return
    setLoading(true)
    try {
      await deleteRegion(region.id)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      className={`rounded-lg p-3 text-sm space-y-2 cursor-pointer transition-all ${
        isSelected
          ? 'ring-2 ring-offset-1 ring-offset-background'
          : 'bg-secondary/50 hover:bg-secondary/70'
      }`}
      style={{
        borderLeft: `3px solid ${region.color}`,
        ...(isSelected ? { ringColor: region.color } : {}),
      }}
      onClick={() => selectRegion(isSelected ? null : region.id)}
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: region.color }}
          />
          <p className="font-medium">{region.name}</p>
        </div>
        <span className="text-xs text-muted-foreground">
          {occupiedSeats.length}/{regionSeats.length} seats
        </span>
      </div>

      {region.description && (
        <p className="text-xs text-muted-foreground">{region.description}</p>
      )}

      {/* I/O summary */}
      <div className="flex gap-3">
        {regionInputs.length > 0 && (
          <div className="flex items-center gap-1">
            <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-400 flex items-center gap-1">
              <InputIcon className="w-3 h-3" /> {regionInputs.length} IN
            </span>
          </div>
        )}
        {regionOutputs.length > 0 && (
          <div className="flex items-center gap-1">
            <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-400 flex items-center gap-1">
              <OutputIcon className="w-3 h-3" /> {regionOutputs.length} OUT
            </span>
          </div>
        )}
        {regionInputs.length === 0 && regionOutputs.length === 0 && (
          <span className="text-xs text-muted-foreground">No I/O ports</span>
        )}
      </div>

      {/* I/O port names */}
      {(regionInputs.length > 0 || regionOutputs.length > 0) && (
        <div className="text-xs text-muted-foreground space-y-0.5">
          {regionInputs.map((p) => (
            <div key={p.id} className="flex items-center gap-1">
              <InputIcon className="w-3 h-3 text-blue-400" /> {p.name}
              {p.data_type && <span className="font-mono opacity-60">({p.data_type})</span>}
            </div>
          ))}
          {regionOutputs.map((p) => (
            <div key={p.id} className="flex items-center gap-1">
              <OutputIcon className="w-3 h-3 text-emerald-400" /> {p.name}
              {p.data_type && <span className="font-mono opacity-60">({p.data_type})</span>}
            </div>
          ))}
        </div>
      )}

      <div className="flex justify-end pt-1">
        <button
          onClick={(e) => { e.stopPropagation(); handleDelete() }}
          disabled={loading}
          className="flex items-center gap-1 text-xs px-2 py-1 rounded text-destructive hover:bg-destructive/10 disabled:opacity-50"
        >
          <Trash2 className="w-3 h-3" />
          Delete
        </button>
      </div>
    </div>
  )
}
