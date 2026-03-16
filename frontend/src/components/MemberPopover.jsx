/**
 * MemberPopover — floating card that appears when clicking a community member dot.
 */
import { motion } from 'framer-motion'
import useStore from '@/store/useStore'
import { X, Heart, Lightbulb, MessageCircle } from 'lucide-react'

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

export default function MemberPopover() {
  const { memberPopover, communityMembers, closeMemberPopover } = useStore()

  if (!memberPopover) return null

  const member = communityMembers.find((m) => m.id === memberPopover.memberId)
  if (!member) return null

  const color = COHORT_COLORS[member.cohort] || '#6b7280'

  // Position the popover near the click, but keep it on screen
  const style = {
    left: Math.min(memberPopover.x, window.innerWidth - 320),
    top: Math.min(memberPopover.y - 20, window.innerHeight - 400),
  }

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95, y: 4 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: 4 }}
      transition={{ duration: 0.12 }}
      className="fixed z-50"
      style={style}
    >
      <div className="w-72 bg-card/95 backdrop-blur-xl border border-border rounded-xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 border-b border-border" style={{ borderTopColor: color, borderTopWidth: 3 }}>
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-sm">{member.name}</h3>
              <p className="text-xs text-muted-foreground">{member.age} · {member.profession}</p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className="text-[9px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full"
                style={{ color, backgroundColor: `${color}20` }}
              >
                {COHORT_LABELS[member.cohort] || member.cohort}
              </span>
              <button
                onClick={closeMemberPopover}
                className="text-muted-foreground hover:text-foreground transition-colors"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Body */}
        <div className="px-4 py-3 space-y-3 max-h-64 overflow-y-auto">
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

          {/* Values */}
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
                <MessageCircle className="w-3 h-3" /> Communication Style
              </div>
              <p className="text-[11px] text-muted-foreground">{member.communication_style}</p>
            </div>
          )}

          {/* Worldview */}
          {member.perspective_summary && (
            <div>
              <div className="flex items-center gap-1 text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-1">
                <Lightbulb className="w-3 h-3" /> Worldview
              </div>
              <p className="text-[11px] text-muted-foreground leading-relaxed">{member.perspective_summary}</p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}
