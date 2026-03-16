/**
 * Onboarding — First-run setup wizard for Council.
 *
 * Flow:
 * 1. Welcome — name + council intro
 * 2. Create Agents — add agents with roles, icons, model/provider
 * 3. Connect MCPs — configure MCP tool servers for agents
 * 4. Constitution — set governing rules/goals/constraints
 * 5. Ready — summary + launch
 */
import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import useStore from '@/store/useStore'
import { AGENT_ICONS, getAgentIcon, ROLE_ICONS } from '@/lib/icons'
import {
  ArrowRight, ArrowLeft, Check, Plus, Trash2, Loader2,
  Landmark, Users, Puzzle, ScrollText, Sparkles, FileText,
  Bot, Brain, Shield, Eye, Zap, Terminal, ChevronDown,
} from 'lucide-react'

// ── Constants ───────────────────────────────────────────────────────────────

const ROLES = [
  { key: 'speaker', label: 'Speaker', desc: 'Orchestrates decisions' },
  { key: 'minister', label: 'Minister', desc: 'Domain specialist' },
  { key: 'delegate', label: 'Delegate', desc: 'General worker' },
  { key: 'observer', label: 'Observer', desc: 'Read-only monitor' },
  { key: 'auditor', label: 'Auditor', desc: 'Reviews & compliance' },
]

const PROVIDERS = [
  { id: 'anthropic', name: 'Anthropic', model: 'claude-sonnet-4', desc: 'Claude models' },
  { id: 'openai', name: 'OpenAI', model: 'gpt-4o', desc: 'GPT-4 models' },
  { id: 'google', name: 'Google', model: 'gemini-2.0-flash', desc: 'Gemini models' },
  { id: 'ollama', name: 'Ollama (Local)', model: 'llama3.2', desc: 'Run locally' },
]

const MCP_TEMPLATES = [
  { id: 'developer', name: 'Developer Tools', desc: 'Shell, file system, code execution', command: 'goose-mcp', args: ['developer'] },
  { id: 'browser', name: 'Web Browser', desc: 'Browse and scrape web pages', command: 'goose-mcp', args: ['browser'] },
  { id: 'github', name: 'GitHub', desc: 'Issues, PRs, repos', command: 'github-mcp-server', args: [] },
  { id: 'slack', name: 'Slack', desc: 'Messages, channels, search', command: 'slack-mcp-server', args: [] },
  { id: 'postgres', name: 'PostgreSQL', desc: 'Database queries', command: 'postgres-mcp-server', args: [] },
  { id: 'custom', name: 'Custom MCP Server', desc: 'Add your own server', command: '', args: [] },
]

// ── Step Dots ───────────────────────────────────────────────────────────────

function StepDots({ total, current }) {
  return (
    <div className="flex gap-1.5">
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          className={`h-1.5 rounded-full transition-all duration-300 ${
            i === current
              ? 'w-8 bg-foreground'
              : i < current
                ? 'w-2 bg-foreground/40'
                : 'w-2 bg-foreground/15'
          }`}
        />
      ))}
    </div>
  )
}

// ── Step 1: Welcome ─────────────────────────────────────────────────────────

function WelcomeStep({ onNext }) {
  const [name, setName] = useState('')

  const handleSubmit = (e) => {
    e.preventDefault()
    if (name.trim()) onNext(name.trim())
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex flex-col items-start max-w-md"
    >
      <Landmark className="w-10 h-10 text-muted-foreground mb-8" />

      <h1 className="text-3xl font-light text-foreground">
        Welcome to Council
      </h1>
      <p className="text-base text-muted-foreground mt-3 leading-relaxed">
        Set up your agent governance parliament. Create agents, assign them tools,
        and define the rules they operate under.
      </p>

      <form onSubmit={handleSubmit} className="w-full mt-8 space-y-4">
        <div>
          <label className="text-sm text-muted-foreground mb-2 block">
            What should we call you?
          </label>
          <input
            type="text"
            placeholder="Your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            autoFocus
            className="w-full px-4 py-3 rounded-xl bg-muted/50 border border-border text-foreground text-sm placeholder:text-muted-foreground/50 focus:outline-none focus:border-foreground/30 transition-colors"
          />
        </div>
        <button
          type="submit"
          disabled={!name.trim()}
          className="w-full px-6 py-3 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-30 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          Get Started <ArrowRight className="w-4 h-4" />
        </button>
      </form>
    </motion.div>
  )
}

// ── Step 2: Create Agents ───────────────────────────────────────────────────

function AgentsStep({ onNext, onBack }) {
  const { createAgent, assignSeat, seats, agents } = useStore()
  const [drafts, setDrafts] = useState([
    { name: '', role: 'delegate', icon: 'bot', provider: 'anthropic', model: 'claude-sonnet-4', description: '' },
  ])
  const [creating, setCreating] = useState(false)

  const addDraft = () => {
    setDrafts((prev) => [...prev, { name: '', role: 'delegate', icon: 'bot', provider: 'anthropic', model: 'claude-sonnet-4', description: '' }])
  }

  const updateDraft = (i, field, value) => {
    setDrafts((prev) => prev.map((d, j) => j === i ? { ...d, [field]: value } : d))
  }

  const removeDraft = (i) => {
    setDrafts((prev) => prev.filter((_, j) => j !== i))
  }

  // When selecting a provider, auto-set the model
  const handleProviderChange = (i, providerId) => {
    const provider = PROVIDERS.find((p) => p.id === providerId)
    updateDraft(i, 'provider', providerId)
    if (provider) updateDraft(i, 'model', provider.model)
  }

  const handleCreate = async () => {
    const valid = drafts.filter((d) => d.name.trim())
    if (valid.length === 0) { onNext(); return }

    setCreating(true)
    try {
      const emptySeats = seats.filter((s) => !s.agent_id)
      for (let i = 0; i < valid.length; i++) {
        const d = valid[i]
        const agent = await createAgent({
          name: d.name.trim(),
          role: d.role,
          icon: d.icon,
          model_provider: d.provider,
          model_name: d.model,
          description: d.description.trim() || undefined,
        })
        // Auto-assign to an empty seat
        if (emptySeats[i]) {
          await assignSeat(agent.id, emptySeats[i].id)
        }
      }
    } catch (err) {
      console.warn('Failed to create agents, continuing:', err)
    } finally {
      setCreating(false)
      onNext()
    }
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex flex-col max-w-lg w-full"
    >
      <Users className="w-8 h-8 text-muted-foreground mb-6" />
      <h2 className="text-2xl font-light text-foreground">Create Your Agents</h2>
      <p className="text-sm text-muted-foreground mt-2 mb-6">
        Add AI agents to your council. Each gets a seat and a role.
      </p>

      <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
        {drafts.map((draft, i) => {
          const IconComponent = getAgentIcon(draft.icon)
          return (
            <div key={i} className="bg-card/80 border border-border rounded-xl p-4 space-y-3">
              {/* Row 1: Name + Icon picker */}
              <div className="flex gap-3">
                <input
                  type="text"
                  placeholder="Agent name..."
                  value={draft.name}
                  onChange={(e) => updateDraft(i, 'name', e.target.value)}
                  autoFocus={i === 0}
                  className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-ring"
                />
                <div className="flex gap-0.5">
                  {AGENT_ICONS.slice(0, 6).map(({ name: iconName, Icon }) => (
                    <button
                      key={iconName}
                      type="button"
                      onClick={() => updateDraft(i, 'icon', iconName)}
                      className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                        draft.icon === iconName ? 'bg-primary/15 text-foreground' : 'text-muted-foreground hover:bg-muted/50'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                    </button>
                  ))}
                </div>
              </div>

              {/* Row 2: Role + Provider */}
              <div className="flex gap-3">
                <select
                  value={draft.role}
                  onChange={(e) => updateDraft(i, 'role', e.target.value)}
                  className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  {ROLES.map((r) => (
                    <option key={r.key} value={r.key}>{r.label} — {r.desc}</option>
                  ))}
                </select>
                <select
                  value={draft.provider}
                  onChange={(e) => handleProviderChange(i, e.target.value)}
                  className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-ring"
                >
                  {PROVIDERS.map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>

              {/* Row 3: Description + Delete */}
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="What does this agent do? (optional)"
                  value={draft.description}
                  onChange={(e) => updateDraft(i, 'description', e.target.value)}
                  className="flex-1 px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-ring"
                />
                {drafts.length > 1 && (
                  <button
                    onClick={() => removeDraft(i)}
                    className="px-2 text-destructive hover:bg-destructive/10 rounded-lg transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>

      <button
        onClick={addDraft}
        className="mt-3 w-full py-2.5 border border-dashed border-border rounded-xl text-sm text-muted-foreground hover:text-foreground hover:border-foreground/30 transition-colors flex items-center justify-center gap-1.5"
      >
        <Plus className="w-3.5 h-3.5" /> Add Another Agent
      </button>

      <div className="flex gap-3 mt-6">
        <button onClick={onBack} className="flex-1 py-3 rounded-xl text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center justify-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <button
          onClick={handleCreate}
          disabled={creating}
          className="flex-1 py-3 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {creating ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : <>Continue <ArrowRight className="w-4 h-4" /></>}
        </button>
      </div>
    </motion.div>
  )
}

// ── Step 3: Connect MCPs ────────────────────────────────────────────────────

const AI_TOOLS = [
  { id: 'goose', name: 'Goose', desc: "Block's open-source AI agent" },
  { id: 'claude', name: 'Claude Desktop', desc: "Anthropic's desktop assistant" },
  { id: 'cursor', name: 'Cursor', desc: 'AI-powered code editor' },
  { id: 'windsurf', name: 'Windsurf', desc: 'Codeium AI editor' },
]

function MCPStep({ onNext, onBack }) {
  const [autoConnecting, setAutoConnecting] = useState(true)
  const [results, setResults] = useState({})  // { goose: {status, ...}, ... }
  const [connecting, setConnecting] = useState(null) // tool id being manually connected
  const [error, setError] = useState(null)
  const [showMcp, setShowMcp] = useState(false)
  const [mcpInfo, setMcpInfo] = useState(null)
  const [copied, setCopied] = useState(false)

  // Auto-connect on mount
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/tools/auto-connect', { method: 'POST' })
        if (res.ok) {
          const data = await res.json()
          setResults(data.results || {})
          // Also fetch MCP info for manual config
          const infoRes = await fetch('/api/tools/mcp-info')
          if (infoRes.ok) setMcpInfo(await infoRes.json())
        }
      } catch (err) {
        console.warn('Auto-connect failed:', err)
      } finally {
        setAutoConnecting(false)
      }
    })()
  }, [])

  const handleManualConnect = async (toolId) => {
    setConnecting(toolId)
    setError(null)
    try {
      const res = await fetch('/api/tools/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool: toolId }),
      })
      if (res.ok) {
        const data = await res.json()
        setResults((prev) => ({ ...prev, [toolId]: data }))
      } else {
        const data = await res.json().catch(() => ({}))
        setError(data.detail || 'Connection failed')
      }
    } catch {
      setError('Could not reach backend')
    } finally {
      setConnecting(null)
    }
  }

  const handleCopy = () => {
    if (!mcpInfo) return
    const config = JSON.stringify({
      mcpServers: {
        council: {
          command: mcpInfo.command,
          args: mcpInfo.args,
          env: mcpInfo.env,
        }
      }
    }, null, 2)
    navigator.clipboard.writeText(config)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const connectedCount = Object.values(results).filter((r) => r.status === 'connected').length

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex flex-col max-w-lg w-full"
    >
      <Puzzle className="w-8 h-8 text-muted-foreground mb-6" />
      <h2 className="text-2xl font-light text-foreground">Connect Your AI Tools</h2>
      <p className="text-sm text-muted-foreground mt-2 mb-6">
        {autoConnecting
          ? 'Detecting installed tools and configuring Council as an MCP server...'
          : connectedCount > 0
            ? `Council has been configured for ${connectedCount} tool${connectedCount !== 1 ? 's' : ''}. Your AI assistants can now manage the parliament.`
            : 'Council works as an MCP server. Connect it to your AI tools below.'}
      </p>

      <div className="space-y-2">
        {AI_TOOLS.map((tool) => {
          const result = results[tool.id]
          const isConnected = result?.status === 'connected'
          const isSkipped = result?.status === 'skipped'
          const isError = result?.status === 'error'
          const isConnecting = connecting === tool.id || (autoConnecting && !result)

          return (
            <button
              key={tool.id}
              onClick={() => !isConnected && !autoConnecting && handleManualConnect(tool.id)}
              disabled={isConnecting || autoConnecting || isConnected}
              className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-left ${
                isConnected
                  ? 'border-emerald-500/20 bg-emerald-500/5'
                  : isSkipped
                    ? 'border-border/30 bg-card/50 opacity-60'
                    : 'border-border/50 bg-card hover:bg-muted/50 hover:border-border'
              }`}
            >
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center shrink-0 ${
                isConnected ? 'bg-emerald-500/15 text-emerald-400' : 'bg-muted text-muted-foreground'
              }`}>
                <Puzzle className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">{tool.name}</p>
                <p className="text-xs text-muted-foreground">
                  {isSkipped ? 'Not installed' : isError ? result.detail : tool.desc}
                </p>
                {isConnected && result.config_path && (
                  <p className="text-[10px] font-mono text-muted-foreground/50 mt-0.5 truncate">
                    {result.config_path}
                  </p>
                )}
              </div>
              <div className="shrink-0">
                {isConnected ? (
                  <Check className="w-5 h-5 text-emerald-400" />
                ) : isConnecting ? (
                  <Loader2 className="w-4 h-4 animate-spin text-muted-foreground" />
                ) : isSkipped ? (
                  <span className="text-[10px] text-muted-foreground/50">—</span>
                ) : isError ? (
                  <span className="text-[10px] text-destructive">retry</span>
                ) : (
                  <span className="text-[10px] text-muted-foreground">Connect</span>
                )}
              </div>
            </button>
          )
        })}

        {/* Manual MCP config toggle */}
        <button
          onClick={() => setShowMcp(!showMcp)}
          className="w-full flex items-center gap-4 p-4 rounded-xl border border-dashed border-border/50 text-left hover:bg-muted/30 transition-colors"
        >
          <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center shrink-0 text-muted-foreground">
            <Terminal className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-foreground/70">MCP Config</p>
            <p className="text-xs text-muted-foreground">Manual setup for other tools</p>
          </div>
          <ChevronDown className={`w-4 h-4 text-muted-foreground transition-transform ${showMcp ? 'rotate-180' : ''}`} />
        </button>

        <AnimatePresence>
          {showMcp && mcpInfo && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="overflow-hidden"
            >
              <div className="relative rounded-xl border border-border bg-muted/30 p-4">
                <pre className="text-xs text-foreground/70 font-mono whitespace-pre overflow-x-auto">
{JSON.stringify({
  mcpServers: {
    council: {
      command: mcpInfo.command,
      args: mcpInfo.args,
      env: mcpInfo.env,
    }
  }
}, null, 2)}
                </pre>
                <button
                  onClick={handleCopy}
                  className="absolute top-3 right-3 px-2.5 py-1 rounded-md bg-muted text-xs text-muted-foreground hover:text-foreground transition-colors"
                >
                  {copied ? 'Copied!' : 'Copy'}
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {error && (
        <p className="text-xs text-destructive mt-3">{error}</p>
      )}

      <div className="flex gap-3 mt-6">
        <button onClick={onBack} className="flex-1 py-3 rounded-xl text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center justify-center gap-1">
          <ArrowLeft className="w-4 h-4" /> Back
        </button>
        <button
          onClick={onNext}
          disabled={autoConnecting}
          className="flex-1 py-3 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
        >
          {autoConnecting ? <><Loader2 className="w-4 h-4 animate-spin" /> Detecting...</> : <>Continue <ArrowRight className="w-4 h-4" /></>}
        </button>
      </div>
    </motion.div>
  )
}

// ── Governance Sliders ──────────────────────────────────────────────────────

const GOVERNANCE_SLIDERS = [
  {
    key: 'autonomy',
    label: 'Agent Autonomy',
    description: 'How independently can agents act?',
    left: 'Supervised',
    right: 'Autonomous',
    icon: Bot,
  },
  {
    key: 'risk_tolerance',
    label: 'Risk Tolerance',
    description: 'How much risk are agents allowed to take?',
    left: 'Conservative',
    right: 'Aggressive',
    icon: Shield,
  },
  {
    key: 'consensus',
    label: 'Decision Making',
    description: 'How are decisions reached?',
    left: 'Single Agent',
    right: 'Full Consensus',
    icon: Users,
  },
  {
    key: 'transparency',
    label: 'Transparency',
    description: 'How much should agents log and explain?',
    left: 'Minimal',
    right: 'Full Audit Trail',
    icon: Eye,
  },
  {
    key: 'speed',
    label: 'Speed vs Thoroughness',
    description: 'Prioritize fast responses or deep analysis?',
    left: 'Fast',
    right: 'Thorough',
    icon: Zap,
  },
  {
    key: 'scope',
    label: 'Action Scope',
    description: 'What can agents modify?',
    left: 'Read Only',
    right: 'Full Write Access',
    icon: Shield,
  },
]

function sliderLabel(value) {
  if (value <= 20) return 'Very Low'
  if (value <= 40) return 'Low'
  if (value <= 60) return 'Moderate'
  if (value <= 80) return 'High'
  return 'Very High'
}

function generateConstitutionFromSliders(sliders) {
  const s = sliders

  // Preamble
  const autonomyDesc = s.autonomy > 60
    ? 'Agents operate with significant autonomy and are trusted to make independent decisions.'
    : s.autonomy > 30
      ? 'Agents operate semi-autonomously, escalating important decisions for review.'
      : 'Agents operate under close supervision, requiring approval for most actions.'

  const preamble = `This council is established to govern AI agent operations. ${autonomyDesc}`

  // Rules
  const rules = []

  // Consensus rules
  if (s.consensus > 70) {
    rules.push('All significant decisions require agreement from a majority of active agents.')
    rules.push('Any agent can veto an action by raising a concern.')
  } else if (s.consensus > 40) {
    rules.push('Important decisions should be reviewed by at least one other agent.')
  } else {
    rules.push('Individual agents may act on their own judgment for routine tasks.')
  }

  // Transparency rules
  if (s.transparency > 70) {
    rules.push('All agent actions must be logged with full reasoning and context.')
    rules.push('Agents must explain their decision-making process when asked.')
  } else if (s.transparency > 40) {
    rules.push('Agents should log significant actions and decisions.')
  } else {
    rules.push('Agents log outcomes but detailed reasoning is optional.')
  }

  // Risk rules
  if (s.risk_tolerance < 30) {
    rules.push('Agents must not perform destructive or irreversible actions without explicit approval.')
    rules.push('All external API calls must be rate-limited and monitored.')
  } else if (s.risk_tolerance < 60) {
    rules.push('Agents should exercise caution with destructive operations.')
  } else {
    rules.push('Agents are permitted to take calculated risks to achieve goals efficiently.')
  }

  // Scope rules
  if (s.scope < 30) {
    rules.push('Agents are restricted to read-only operations unless explicitly granted write access.')
  } else if (s.scope < 60) {
    rules.push('Agents may modify non-critical resources. Production systems require approval.')
  } else {
    rules.push('Agents have full read/write access to systems within their assigned region.')
  }

  // Speed rules
  if (s.speed < 40) {
    rules.push('Prioritize response speed. Provide quick answers and iterate if needed.')
  } else if (s.speed > 60) {
    rules.push('Prioritize thoroughness. Take time to analyze deeply before responding.')
  }

  // Goals
  const goals = []
  goals.push('Fulfill assigned responsibilities within the agent\'s region.')

  if (s.speed < 40) {
    goals.push('Minimize response latency for all incoming requests.')
  } else {
    goals.push('Provide high-quality, well-reasoned outputs.')
  }

  if (s.risk_tolerance < 50) {
    goals.push('Maintain system stability and avoid unintended side effects.')
  }

  if (s.transparency > 50) {
    goals.push('Maintain a clear audit trail for all significant actions.')
  }

  goals.push('Collaborate effectively with other agents in the council.')

  // Constraints
  const constraints = []

  if (s.autonomy < 50) {
    constraints.push('Agents must not take irreversible actions without human approval.')
  }

  if (s.risk_tolerance < 50) {
    constraints.push('Never modify production data or systems without explicit authorization.')
    constraints.push('Rate-limit all external API calls.')
  }

  if (s.scope < 50) {
    constraints.push('Agents must not access resources outside their assigned region.')
  }

  constraints.push('Agents must not impersonate humans or other agents.')
  constraints.push('All actions must comply with the council\'s constitution.')

  return {
    preamble,
    rules: rules.map((r) => `- ${r}`).join('\n'),
    goals: goals.map((g) => `- ${g}`).join('\n'),
    constraints: constraints.map((c) => `- ${c}`).join('\n'),
  }
}

function GovernanceSlider({ slider, value, onChange }) {
  const Icon = slider.icon
  const pct = value

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="w-3.5 h-3.5 text-muted-foreground" />
          <span className="text-xs font-medium text-foreground">{slider.label}</span>
        </div>
        <span className="text-[10px] font-mono text-muted-foreground">{sliderLabel(value)}</span>
      </div>
      <p className="text-[10px] text-muted-foreground/70">{slider.description}</p>
      <div className="flex items-center gap-3">
        <span className="text-[10px] text-muted-foreground w-16 text-right shrink-0">{slider.left}</span>
        <div className="relative flex-1 h-8 flex items-center">
          <input
            type="range"
            min={0}
            max={100}
            value={value}
            onChange={(e) => onChange(parseInt(e.target.value))}
            className="w-full h-1.5 rounded-full appearance-none cursor-pointer bg-border
              [&::-webkit-slider-thumb]:appearance-none
              [&::-webkit-slider-thumb]:w-4
              [&::-webkit-slider-thumb]:h-4
              [&::-webkit-slider-thumb]:rounded-full
              [&::-webkit-slider-thumb]:bg-foreground
              [&::-webkit-slider-thumb]:shadow-md
              [&::-webkit-slider-thumb]:transition-transform
              [&::-webkit-slider-thumb]:hover:scale-125
              [&::-moz-range-thumb]:w-4
              [&::-moz-range-thumb]:h-4
              [&::-moz-range-thumb]:rounded-full
              [&::-moz-range-thumb]:bg-foreground
              [&::-moz-range-thumb]:border-0
              [&::-moz-range-thumb]:shadow-md"
            style={{
              background: `linear-gradient(to right, hsl(var(--primary)) 0%, hsl(var(--primary)) ${pct}%, hsl(var(--border)) ${pct}%, hsl(var(--border)) 100%)`,
            }}
          />
        </div>
        <span className="text-[10px] text-muted-foreground w-20 shrink-0">{slider.right}</span>
      </div>
    </div>
  )
}

// ── Step 4: Constitution (multi-phase) ──────────────────────────────────────
// Phases: choose → build-0..build-5 → review → (save & advance)
//         choose → manual → (save & advance)

function ConstitutionStep({ onNext, onBack }) {
  const { updateConstitution } = useStore()
  // 'choose' | 'build' | 'manual' | 'review'
  const [phase, setPhase] = useState('choose')
  const [buildIndex, setBuildIndex] = useState(0)
  const [sliders, setSliders] = useState({
    autonomy: 50,
    risk_tolerance: 40,
    consensus: 50,
    transparency: 60,
    speed: 50,
    scope: 40,
  })
  const [preamble, setPreamble] = useState('')
  const [rules, setRules] = useState('')
  const [goals, setGoals] = useState('')
  const [constraints, setConstraints] = useState('')
  const [saving, setSaving] = useState(false)

  const generated = generateConstitutionFromSliders(sliders)
  const currentSlider = GOVERNANCE_SLIDERS[buildIndex]

  const updateSlider = (key, value) => {
    setSliders((prev) => ({ ...prev, [key]: value }))
  }

  const handleSave = async (data) => {
    setSaving(true)
    try {
      await updateConstitution(data)
    } catch (err) {
      console.warn('Failed to save constitution, continuing:', err)
    } finally {
      setSaving(false)
      onNext()
    }
  }

  // ── Choose phase ──
  if (phase === 'choose') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="flex flex-col items-center max-w-lg w-full"
      >
        <ScrollText className="w-10 h-10 text-muted-foreground mb-6" />
        <h2 className="text-2xl font-light text-foreground text-center">Set Your Constitution</h2>
        <p className="text-sm text-muted-foreground mt-2 mb-8 text-center">
          How would you like to define the rules for your council?
        </p>

        <div className="grid grid-cols-2 gap-4 w-full">
          {/* Build tile */}
          <button
            onClick={() => { setPhase('build'); setBuildIndex(0) }}
            className="group flex flex-col items-center gap-4 p-6 rounded-2xl border border-border bg-card hover:border-primary/40 hover:bg-primary/5 transition-all text-center"
          >
            <div className="w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
              <Sparkles className="w-6 h-6 text-primary" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Build It</p>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                Walk through each governance dimension with guided sliders
              </p>
            </div>
          </button>

          {/* Manual tile */}
          <button
            onClick={() => setPhase('manual')}
            className="group flex flex-col items-center gap-4 p-6 rounded-2xl border border-border bg-card hover:border-foreground/20 hover:bg-muted/50 transition-all text-center"
          >
            <div className="w-12 h-12 rounded-xl bg-muted flex items-center justify-center group-hover:bg-muted/80 transition-colors">
              <FileText className="w-6 h-6 text-muted-foreground" />
            </div>
            <div>
              <p className="text-sm font-medium text-foreground">Write Manually</p>
              <p className="text-xs text-muted-foreground mt-1 leading-relaxed">
                Write your own preamble, rules, goals, and constraints
              </p>
            </div>
          </button>
        </div>

        <div className="flex gap-3 mt-8 w-full">
          <button onClick={onBack} className="flex-1 py-3 rounded-xl text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center justify-center gap-1">
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <button
            onClick={() => handleSave({ preamble: '', rules: '', goals: '', constraints: '' })}
            className="flex-1 py-3 rounded-xl text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center justify-center gap-1"
          >
            Skip for now <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </motion.div>
    )
  }

  // ── Build phase: one slider per screen ──
  if (phase === 'build') {
    const Icon = currentSlider.icon
    const isLast = buildIndex === GOVERNANCE_SLIDERS.length - 1
    const value = sliders[currentSlider.key]

    return (
      <motion.div
        key={`build-${buildIndex}`}
        initial={{ opacity: 0, x: 30 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -30 }}
        transition={{ duration: 0.2 }}
        className="flex flex-col max-w-md w-full"
      >
        {/* Progress */}
        <div className="flex items-center gap-2 mb-8">
          {GOVERNANCE_SLIDERS.map((_, i) => (
            <div
              key={i}
              className={`h-1 rounded-full flex-1 transition-all duration-300 ${
                i < buildIndex ? 'bg-primary' : i === buildIndex ? 'bg-foreground' : 'bg-border'
              }`}
            />
          ))}
        </div>

        <Icon className="w-8 h-8 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-light text-foreground">{currentSlider.label}</h2>
        <p className="text-sm text-muted-foreground mt-2 mb-8">{currentSlider.description}</p>

        {/* Big slider */}
        <div className="space-y-4">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{currentSlider.left}</span>
            <span className="font-mono text-foreground">{sliderLabel(value)}</span>
            <span>{currentSlider.right}</span>
          </div>
          <input
            type="range"
            min={0}
            max={100}
            value={value}
            onChange={(e) => updateSlider(currentSlider.key, parseInt(e.target.value))}
            className="w-full h-2 rounded-full appearance-none cursor-pointer
              [&::-webkit-slider-thumb]:appearance-none
              [&::-webkit-slider-thumb]:w-5
              [&::-webkit-slider-thumb]:h-5
              [&::-webkit-slider-thumb]:rounded-full
              [&::-webkit-slider-thumb]:bg-foreground
              [&::-webkit-slider-thumb]:shadow-lg
              [&::-webkit-slider-thumb]:transition-transform
              [&::-webkit-slider-thumb]:hover:scale-125
              [&::-moz-range-thumb]:w-5
              [&::-moz-range-thumb]:h-5
              [&::-moz-range-thumb]:rounded-full
              [&::-moz-range-thumb]:bg-foreground
              [&::-moz-range-thumb]:border-0
              [&::-moz-range-thumb]:shadow-lg"
            style={{
              background: `linear-gradient(to right, hsl(var(--primary)) 0%, hsl(var(--primary)) ${value}%, hsl(var(--border)) ${value}%, hsl(var(--border)) 100%)`,
            }}
          />
        </div>

        <div className="flex gap-3 mt-10">
          <button
            onClick={() => buildIndex === 0 ? setPhase('choose') : setBuildIndex((i) => i - 1)}
            className="flex-1 py-3 rounded-xl text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center justify-center gap-1"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <button
            onClick={() => isLast ? setPhase('review') : setBuildIndex((i) => i + 1)}
            className="flex-1 py-3 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 flex items-center justify-center gap-2"
          >
            {isLast ? 'Review' : 'Next'} <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </motion.div>
    )
  }

  // ── Review phase ──
  if (phase === 'review') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="flex flex-col max-w-lg w-full"
      >
        <ScrollText className="w-8 h-8 text-muted-foreground mb-6" />
        <h2 className="text-2xl font-light text-foreground">Your Constitution</h2>
        <p className="text-sm text-muted-foreground mt-2 mb-6">
          Here's what was generated from your choices. You can always edit it later.
        </p>

        {/* Slider summary chips */}
        <div className="flex flex-wrap gap-2 mb-5">
          {GOVERNANCE_SLIDERS.map((s) => {
            const Icon = s.icon
            return (
              <div key={s.key} className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-muted/50 text-xs">
                <Icon className="w-3 h-3 text-muted-foreground" />
                <span className="text-muted-foreground">{s.label}:</span>
                <span className="font-medium text-foreground">{sliderLabel(sliders[s.key])}</span>
              </div>
            )
          })}
        </div>

        <div className="bg-card border border-border rounded-xl p-4 max-h-[40vh] overflow-y-auto space-y-3 text-sm font-mono leading-relaxed">
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Preamble</p>
            <p className="text-foreground/90">{generated.preamble}</p>
          </div>
          <div className="h-px bg-border" />
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Rules</p>
            <pre className="whitespace-pre-wrap text-foreground/80">{generated.rules}</pre>
          </div>
          <div className="h-px bg-border" />
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Goals</p>
            <pre className="whitespace-pre-wrap text-foreground/80">{generated.goals}</pre>
          </div>
          <div className="h-px bg-border" />
          <div>
            <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-1">Constraints</p>
            <pre className="whitespace-pre-wrap text-foreground/80">{generated.constraints}</pre>
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={() => { setPhase('build'); setBuildIndex(GOVERNANCE_SLIDERS.length - 1) }}
            className="flex-1 py-3 rounded-xl text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center justify-center gap-1"
          >
            <ArrowLeft className="w-4 h-4" /> Adjust
          </button>
          <button
            onClick={() => handleSave(generated)}
            disabled={saving}
            className="flex-1 py-3 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {saving ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</> : <>Adopt Constitution <Check className="w-4 h-4" /></>}
          </button>
        </div>
      </motion.div>
    )
  }

  // ── Manual phase ──
  if (phase === 'manual') {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className="flex flex-col max-w-lg w-full"
      >
        <ScrollText className="w-8 h-8 text-muted-foreground mb-6" />
        <h2 className="text-2xl font-light text-foreground">Write Your Constitution</h2>
        <p className="text-sm text-muted-foreground mt-2 mb-6">
          Define the governing document directly. You can always edit it later.
        </p>

        <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
          <div>
            <label className="text-xs font-medium text-foreground mb-1.5 block">Preamble</label>
            <textarea
              value={preamble}
              onChange={(e) => setPreamble(e.target.value)}
              placeholder="The purpose of this council is to..."
              rows={2}
              autoFocus
              className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-ring resize-y font-mono"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-foreground mb-1.5 block">Rules</label>
            <textarea
              value={rules}
              onChange={(e) => setRules(e.target.value)}
              placeholder="- All agents must log their actions&#10;- Decisions require consensus&#10;- ..."
              rows={4}
              className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-ring resize-y font-mono"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-foreground mb-1.5 block">Goals</label>
            <textarea
              value={goals}
              onChange={(e) => setGoals(e.target.value)}
              placeholder="- Maintain system reliability&#10;- Process requests efficiently&#10;- ..."
              rows={3}
              className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-ring resize-y font-mono"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-foreground mb-1.5 block">Constraints</label>
            <textarea
              value={constraints}
              onChange={(e) => setConstraints(e.target.value)}
              placeholder="- Never modify production data without approval&#10;- Rate limit external API calls&#10;- ..."
              rows={3}
              className="w-full px-3 py-2 text-sm bg-background border border-border rounded-lg focus:outline-none focus:ring-1 focus:ring-ring resize-y font-mono"
            />
          </div>
        </div>

        <div className="flex gap-3 mt-6">
          <button
            onClick={() => setPhase('choose')}
            className="flex-1 py-3 rounded-xl text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center justify-center gap-1"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </button>
          <button
            onClick={() => handleSave({ preamble: preamble.trim(), rules: rules.trim(), goals: goals.trim(), constraints: constraints.trim() })}
            disabled={saving}
            className="flex-1 py-3 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {saving ? <><Loader2 className="w-4 h-4 animate-spin" /> Saving...</> : <>Continue <ArrowRight className="w-4 h-4" /></>}
          </button>
        </div>
      </motion.div>
    )
  }

  return null
}

// ── Step 5: Ready ───────────────────────────────────────────────────────────

function ReadyStep({ userName, onComplete }) {
  const { agents, regions, stats } = useStore()

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      className="flex flex-col items-center max-w-md text-center"
    >
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
      >
        <Landmark className="w-14 h-14 text-foreground mb-6" />
      </motion.div>

      <h2 className="text-3xl font-light text-foreground">
        Your Council is Ready
      </h2>
      <p className="text-base text-muted-foreground mt-3">
        Welcome, {userName}. Your parliament is set up with {agents.length} agent{agents.length !== 1 ? 's' : ''} across {stats.total_seats || 55} seats.
      </p>

      {agents.length > 0 && (
        <div className="flex flex-wrap justify-center gap-2 mt-6">
          {agents.map((agent) => {
            const Icon = getAgentIcon(agent.icon)
            return (
              <div
                key={agent.id}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-border text-sm"
              >
                <Icon className="w-3.5 h-3.5" style={{ color: agent.color }} />
                <span>{agent.name}</span>
                <span className="text-[10px] text-muted-foreground capitalize">{agent.role}</span>
              </div>
            )
          })}
        </div>
      )}

      <button
        onClick={onComplete}
        className="mt-10 px-10 py-3 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 flex items-center gap-2"
      >
        Launch Council <Sparkles className="w-4 h-4" />
      </button>
    </motion.div>
  )
}

// ── Main Onboarding ─────────────────────────────────────────────────────────

const STEPS = ['welcome', 'agents', 'mcp', 'constitution', 'ready']

export default function Onboarding({ onComplete }) {
  const [step, setStep] = useState(0)
  const [userName, setUserName] = useState('')

  const handleWelcome = (name) => {
    setUserName(name)
    localStorage.setItem('council_user_name', name)
    setStep(1)
  }

  return (
    <div className="fixed inset-0 z-[9998] flex flex-col items-center justify-center bg-background">
      <div className="flex-1 flex items-center justify-center px-6 w-full">
        <AnimatePresence mode="wait">
          {step === 0 && <WelcomeStep key="welcome" onNext={handleWelcome} />}
          {step === 1 && <AgentsStep key="agents" onNext={() => setStep(2)} onBack={() => setStep(0)} />}
          {step === 2 && <MCPStep key="mcp" onNext={() => setStep(3)} onBack={() => setStep(1)} />}
          {step === 3 && <ConstitutionStep key="constitution" onNext={() => setStep(4)} onBack={() => setStep(2)} />}
          {step === 4 && <ReadyStep key="ready" userName={userName} onComplete={onComplete} />}
        </AnimatePresence>
      </div>

      <div className="pb-10">
        <StepDots total={STEPS.length} current={step} />
      </div>
    </div>
  )
}
