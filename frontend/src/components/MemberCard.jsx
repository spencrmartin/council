/**
 * MemberCard — displays a community member's profile in the sidebar.
 */
import { useState } from 'react'
import useStore from '@/store/useStore'
import { Trash2, ChevronDown, ChevronUp, Heart, Lightbulb, MessageCircle } from 'lucide-react'

const COHORT_COLORS = {
  builders: '#3b82f6',
  operators: '#f59e0b',
  advocates: '#ef4444',
  pragmatists: '#10b981',
  creatives: '#a855f7',
  skeptics: '#6b7280',
}

const COHORT_LABELS = {
  builders: 'Builder',
  operators: 'Operator',
  advocates: 'Advocate',
  pragmatists: 'Pragmatist',
  creatives: 'Creative',
  skeptics: 'Skeptic',
}

export default function MemberCard({ member, compact = false }) {
  const { deleteCommunityMember } = useStore()
  const [expanded, setExpanded] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const color = COHORT_COLORS[member.cohort] || '#6b7280'

  const handleDelete = async () => {
    if (!confirm(`Remove ${member.name} from the community?`)) return
    setDeleting(true)
    try {
      await deleteCommunityMember(member.id)
    } finally {
      setDeleting(false)
    }
  }

  if (compact) {
    return (
      <div className="flex items-center gap-2 py-1.5 px-2 rounded-md hover:bg-secondary/50 transition-colors">
        <span
          className="w-2.5 h-2.5 rounded-full shrink-0"
          style={{ backgroundColor: color }}
        />
        <div className="min-w-0 flex-1">
          <span className="text-sm font-medium truncate block">{member.name}</span>
          <span className="text-[10px] text-muted-foreground truncate block">{member.profession}</span>
        </div>
        <span
          className="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded"
          style={{ color, backgroundColor: `${color}15` }}
        >
          {COHORT_LABELS[member.cohort] || member.cohort}
        </span>
      </div>
    )
  }

  return (
    <div className="bg-secondary/50 rounded-lg p-3 text-sm space-y-2">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <span
            className="w-3 h-3 rounded-full shrink-0"
            style={{ backgroundColor: color }}
          />
          <div>
            <div className="font-semibold">{member.name}</div>
            <div className="text-xs text-muted-foreground">
              {member.age} · {member.profession}
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1">
          <span
            className="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded"
            style={{ color, backgroundColor: `${color}15` }}
          >
            {COHORT_LABELS[member.cohort] || member.cohort}
          </span>
          {member.is_custom && (
            <span className="text-[9px] font-semibold uppercase tracking-wider px-1.5 py-0.5 rounded bg-primary/10 text-primary">
              Custom
            </span>
          )}
        </div>
      </div>

      {/* Background */}
      <p className="text-xs text-muted-foreground leading-relaxed">{member.background}</p>

      {/* Passions */}
      {member.passions && member.passions.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {member.passions.map((p) => (
            <span
              key={p}
              className="text-[10px] px-1.5 py-0.5 rounded-full bg-muted text-muted-foreground"
            >
              {p}
            </span>
          ))}
        </div>
      )}

      {/* Expand/collapse for details */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
      >
        {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
        {expanded ? 'Less' : 'More'}
      </button>

      {expanded && (
        <div className="space-y-2 pt-1 border-t border-border">
          {/* Core values */}
          {member.core_values && member.core_values.length > 0 && (
            <div>
              <div className="flex items-center gap-1 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                <Heart className="w-3 h-3" /> Values
              </div>
              <div className="flex flex-wrap gap-1">
                {member.core_values.map((v) => (
                  <span key={v} className="text-[10px] px-1.5 py-0.5 rounded-full" style={{ backgroundColor: `${color}15`, color }}>
                    {v}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Communication style */}
          {member.communication_style && (
            <div>
              <div className="flex items-center gap-1 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                <MessageCircle className="w-3 h-3" /> Style
              </div>
              <p className="text-xs text-muted-foreground">{member.communication_style}</p>
            </div>
          )}

          {/* Perspective */}
          {member.perspective_summary && (
            <div>
              <div className="flex items-center gap-1 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                <Lightbulb className="w-3 h-3" /> Worldview
              </div>
              <p className="text-xs text-muted-foreground leading-relaxed">{member.perspective_summary}</p>
            </div>
          )}

          {/* Delete */}
          <button
            onClick={handleDelete}
            disabled={deleting}
            className="flex items-center gap-1 text-xs text-destructive hover:text-destructive/80 transition-colors mt-2"
          >
            <Trash2 className="w-3 h-3" />
            {deleting ? 'Removing...' : 'Remove member'}
          </button>
        </div>
      )}
    </div>
  )
}
