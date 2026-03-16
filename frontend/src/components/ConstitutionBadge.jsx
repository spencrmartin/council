/**
 * ConstitutionBadge — floating card showing the active constitution.
 *
 * Collapsed: pill with "Active" badge + version + preamble preview.
 * Expanded: full readable constitution.
 */
import { useState } from 'react'
import useStore from '@/store/useStore'
import { motion, AnimatePresence } from 'framer-motion'
import { ScrollText, ChevronDown, ChevronUp, Check } from 'lucide-react'

function Section({ label, content }) {
  if (!content) return null
  return (
    <div>
      <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground mb-1">{label}</p>
      <pre className="text-xs text-foreground/80 whitespace-pre-wrap leading-relaxed font-mono">{content}</pre>
    </div>
  )
}

export default function ConstitutionBadge() {
  const { constitution: raw } = useStore()
  const constitution = raw || {}
  const [expanded, setExpanded] = useState(false)

  const hasContent = constitution.preamble || constitution.rules || constitution.goals || constitution.constraints
  if (!hasContent) return null

  const preview = (constitution.preamble || constitution.rules || '').slice(0, 50)

  return (
    <div className="absolute bottom-4 right-4 z-10" style={{ maxWidth: expanded ? 380 : 300 }}>
      <motion.div
        layout
        className="bg-card/85 backdrop-blur-xl border border-border/50 rounded-xl shadow-lg overflow-hidden"
      >
        {/* Header */}
        <button
          onClick={() => setExpanded((v) => !v)}
          className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-muted/30 transition-colors"
        >
          <ScrollText className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="flex items-center gap-1 text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 shrink-0">
              <Check className="w-2.5 h-2.5" /> Active
            </span>
            {constitution.version && (
              <span className="text-[10px] text-muted-foreground font-mono shrink-0">v{constitution.version}</span>
            )}
            {!expanded && preview && (
              <span className="text-[10px] text-muted-foreground/60 truncate">
                {preview}...
              </span>
            )}
          </div>
          {expanded
            ? <ChevronDown className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
            : <ChevronUp className="w-3.5 h-3.5 text-muted-foreground shrink-0" />
          }
        </button>

        {/* Expanded */}
        <AnimatePresence>
          {expanded && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="overflow-hidden"
            >
              <div className="px-3 pb-3 space-y-2.5 max-h-64 overflow-y-auto border-t border-border pt-2">
                {constitution.preamble && (
                  <p className="text-xs text-foreground/90 leading-relaxed italic">{constitution.preamble}</p>
                )}
                <Section label="Rules" content={constitution.rules} />
                <Section label="Goals" content={constitution.goals} />
                <Section label="Constraints" content={constitution.constraints} />
                <div className="flex items-center justify-between pt-1">
                  {constitution.created_by && (
                    <span className="text-[9px] text-muted-foreground/50">by {constitution.created_by}</span>
                  )}
                  {constitution.created_at && (
                    <span className="text-[9px] text-muted-foreground/50">
                      {new Date(constitution.created_at).toLocaleDateString()}
                    </span>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}
