/**
 * ConstitutionEditor — view active constitution, create new versions, browse history.
 */
import { useState, useEffect } from 'react'
import useStore from '@/store/useStore'
import * as api from '@/lib/api'
import {
  ScrollText, BookOpen, Target, ShieldAlert, FileText,
  Check, Loader2, Plus, History, ChevronDown, ChevronRight, RotateCcw,
} from 'lucide-react'

const SECTIONS = [
  { key: 'preamble', label: 'Preamble', Icon: ScrollText, placeholder: 'The purpose and mission of this council...' },
  { key: 'rules', label: 'Rules', Icon: BookOpen, placeholder: '- Agents must respond within 30 seconds\n- All decisions require majority vote' },
  { key: 'goals', label: 'Goals', Icon: Target, placeholder: '- Maintain system uptime above 99.9%\n- Process all incoming requests' },
  { key: 'constraints', label: 'Constraints', Icon: ShieldAlert, placeholder: '- Never modify production data without approval\n- Rate limit external API calls' },
]

export default function ConstitutionEditor() {
  const { constitution: rawConstitution, updateConstitution, loadCouncil } = useStore()
  const constitution = rawConstitution || {}

  const [view, setView] = useState('active') // 'active' | 'new' | 'history'
  const [history, setHistory] = useState([])
  const [historyLoading, setHistoryLoading] = useState(false)
  const [historyExpanded, setHistoryExpanded] = useState(null) // id of expanded version

  // New constitution draft
  const [draft, setDraft] = useState({ preamble: '', rules: '', goals: '', constraints: '' })
  const [saving, setSaving] = useState(false)
  const [activating, setActivating] = useState(null)

  const loadHistory = async () => {
    setHistoryLoading(true)
    try {
      const data = await api.listConstitutions()
      setHistory(data)
    } catch {
      setHistory([])
    } finally {
      setHistoryLoading(false)
    }
  }

  const handleCreateNew = async () => {
    setSaving(true)
    try {
      const userName = localStorage.getItem('council_user_name') || 'Unknown'
      await api.createConstitution({
        ...draft,
        created_by: userName,
        activate: true,
      })
      await loadCouncil()
      setView('active')
      setDraft({ preamble: '', rules: '', goals: '', constraints: '' })
    } catch (err) {
      console.warn('Failed to create constitution:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleActivate = async (id) => {
    setActivating(id)
    try {
      await api.activateConstitution(id)
      await loadCouncil()
      await loadHistory()
    } catch (err) {
      console.warn('Failed to activate constitution:', err)
    } finally {
      setActivating(null)
    }
  }

  const hasContent = constitution.preamble || constitution.rules || constitution.goals || constitution.constraints

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ScrollText className="w-4 h-4" />
          <h3 className="text-base font-semibold">Constitution</h3>
        </div>
      </div>

      {/* ── Active view ── */}
      {view === 'active' && (
        <div className="space-y-3">
          {hasContent ? (
            <>
              {/* Active badge */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="flex items-center gap-1 text-[10px] font-medium px-2 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400">
                    <Check className="w-3 h-3" /> Active
                  </span>
                  {constitution.version && (
                    <span className="text-[10px] text-muted-foreground font-mono">
                      v{constitution.version}
                    </span>
                  )}
                </div>
                {constitution.created_by && (
                  <span className="text-[10px] text-muted-foreground">
                    by {constitution.created_by}
                  </span>
                )}
              </div>

              {/* Content */}
              <div className="space-y-2.5">
                {SECTIONS.map(({ key, label, Icon }) => {
                  const content = constitution[key]
                  if (!content) return null
                  return (
                    <div key={key}>
                      <div className="flex items-center gap-1.5 mb-1">
                        <Icon className="w-3 h-3 text-muted-foreground" />
                        <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</span>
                      </div>
                      <pre className="text-xs text-foreground/80 whitespace-pre-wrap leading-relaxed font-mono bg-secondary/30 rounded-md p-2">
                        {content}
                      </pre>
                    </div>
                  )
                })}
              </div>

              {constitution.created_at && (
                <p className="text-[9px] text-muted-foreground/50">
                  Created {new Date(constitution.created_at).toLocaleString()}
                </p>
              )}
            </>
          ) : (
            <div className="text-center text-muted-foreground py-6">
              <ScrollText className="w-6 h-6 mx-auto mb-2 opacity-40" />
              <p className="text-sm">No active constitution</p>
              <p className="text-xs mt-1">Create one to define your council's governance.</p>
            </div>
          )}

          {/* Action buttons */}
          <div className="flex gap-2 pt-1">
            <button
              onClick={() => {
                // Pre-fill draft from active constitution for iteration
                setDraft({
                  preamble: constitution.preamble || '',
                  rules: constitution.rules || '',
                  goals: constitution.goals || '',
                  constraints: constitution.constraints || '',
                })
                setView('new')
              }}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs rounded-lg bg-primary text-primary-foreground hover:opacity-90 transition-colors"
            >
              <Plus className="w-3 h-3" />
              {hasContent ? 'New Version' : 'Create Constitution'}
            </button>
            <button
              onClick={() => { loadHistory(); setView('history') }}
              className="flex items-center justify-center gap-1.5 px-3 py-2 text-xs rounded-lg bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors"
            >
              <History className="w-3 h-3" />
              History
            </button>
          </div>
        </div>
      )}

      {/* ── New version editor ── */}
      {view === 'new' && (
        <div className="space-y-3">
          <p className="text-xs text-muted-foreground">
            This will create a new version and set it as the active constitution.
          </p>

          {SECTIONS.map(({ key, label, Icon, placeholder }) => (
            <div key={key}>
              <div className="flex items-center gap-1.5 mb-1">
                <Icon className="w-3 h-3 text-muted-foreground" />
                <label className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</label>
              </div>
              <textarea
                value={draft[key]}
                onChange={(e) => setDraft((prev) => ({ ...prev, [key]: e.target.value }))}
                placeholder={placeholder}
                rows={key === 'preamble' ? 2 : 3}
                className="w-full px-2.5 py-2 text-xs bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring resize-y font-mono leading-relaxed"
              />
            </div>
          ))}

          <div className="flex gap-2 pt-1">
            <button
              onClick={() => setView('active')}
              className="flex-1 py-2 text-xs rounded-lg text-muted-foreground hover:text-foreground transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleCreateNew}
              disabled={saving}
              className="flex-1 flex items-center justify-center gap-1.5 py-2 text-xs rounded-lg bg-primary text-primary-foreground hover:opacity-90 disabled:opacity-50 transition-colors"
            >
              {saving
                ? <><Loader2 className="w-3 h-3 animate-spin" /> Saving...</>
                : <><Check className="w-3 h-3" /> Save & Activate</>
              }
            </button>
          </div>
        </div>
      )}

      {/* ── History view ── */}
      {view === 'history' && (
        <div className="space-y-3">
          <button
            onClick={() => setView('active')}
            className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            ← Back to active
          </button>

          {historyLoading ? (
            <div className="flex items-center justify-center py-6">
              <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
            </div>
          ) : history.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-6">No constitution history.</p>
          ) : (
            <div className="space-y-1.5">
              {history.map((c) => {
                const isExpanded = historyExpanded === c.id
                return (
                  <div key={c.id} className="bg-secondary/40 rounded-lg overflow-hidden">
                    {/* Row header */}
                    <button
                      onClick={() => setHistoryExpanded(isExpanded ? null : c.id)}
                      className="w-full flex items-center gap-2 px-3 py-2 text-left hover:bg-secondary/60 transition-colors"
                    >
                      {isExpanded
                        ? <ChevronDown className="w-3 h-3 text-muted-foreground shrink-0" />
                        : <ChevronRight className="w-3 h-3 text-muted-foreground shrink-0" />
                      }
                      <span className="text-xs font-mono text-foreground">v{c.version}</span>
                      {c.is_active && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-emerald-500/15 text-emerald-400 font-medium">
                          Active
                        </span>
                      )}
                      <span className="flex-1" />
                      {c.created_by && (
                        <span className="text-[10px] text-muted-foreground">{c.created_by}</span>
                      )}
                      <span className="text-[10px] text-muted-foreground/60">
                        {c.created_at ? new Date(c.created_at).toLocaleDateString() : ''}
                      </span>
                    </button>

                    {/* Expanded content */}
                    {isExpanded && (
                      <div className="px-3 pb-3 space-y-2 border-t border-border/50 pt-2">
                        {c.preamble && (
                          <p className="text-xs text-foreground/80 italic">{c.preamble}</p>
                        )}
                        {c.rules && (
                          <div>
                            <p className="text-[9px] font-semibold text-muted-foreground uppercase">Rules</p>
                            <pre className="text-[11px] text-foreground/70 whitespace-pre-wrap font-mono">{c.rules}</pre>
                          </div>
                        )}
                        {c.goals && (
                          <div>
                            <p className="text-[9px] font-semibold text-muted-foreground uppercase">Goals</p>
                            <pre className="text-[11px] text-foreground/70 whitespace-pre-wrap font-mono">{c.goals}</pre>
                          </div>
                        )}
                        {c.constraints && (
                          <div>
                            <p className="text-[9px] font-semibold text-muted-foreground uppercase">Constraints</p>
                            <pre className="text-[11px] text-foreground/70 whitespace-pre-wrap font-mono">{c.constraints}</pre>
                          </div>
                        )}
                        {!c.is_active && (
                          <button
                            onClick={() => handleActivate(c.id)}
                            disabled={activating === c.id}
                            className="flex items-center gap-1.5 text-xs px-2.5 py-1.5 rounded-md bg-primary/10 text-primary hover:bg-primary/20 transition-colors disabled:opacity-50"
                          >
                            {activating === c.id
                              ? <><Loader2 className="w-3 h-3 animate-spin" /> Activating...</>
                              : <><RotateCcw className="w-3 h-3" /> Restore this version</>
                            }
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
