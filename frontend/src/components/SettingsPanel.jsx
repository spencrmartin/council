/**
 * SettingsPanel — connection info, user profile, MCP config, and app metadata.
 */
import { useState, useEffect } from 'react'
import useStore from '@/store/useStore'
import * as api from '@/lib/api'
import {
  Settings, User, Server, Database, Terminal, Copy, Check,
  RotateCcw, Trash2, ExternalLink,
} from 'lucide-react'

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false)
  const handleCopy = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 text-[10px] px-2 py-1 rounded-md bg-muted text-muted-foreground hover:text-foreground transition-colors"
    >
      {copied ? <><Check className="w-3 h-3" /> Copied</> : <><Copy className="w-3 h-3" /> Copy</>}
    </button>
  )
}

function InfoRow({ label, value, mono = false, copyable = false }) {
  return (
    <div className="flex items-start justify-between gap-3 py-1.5">
      <span className="text-xs text-muted-foreground shrink-0">{label}</span>
      <div className="flex items-center gap-2 min-w-0">
        <span className={`text-xs text-foreground truncate ${mono ? 'font-mono' : ''}`}>
          {value}
        </span>
        {copyable && <CopyButton text={value} />}
      </div>
    </div>
  )
}

export default function SettingsPanel() {
  const { stats, agents, regions, loadCouncil } = useStore()
  const [serverInfo, setServerInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [mcpCopied, setMcpCopied] = useState(false)

  const userName = localStorage.getItem('council_user_name') || 'User'
  const [editingName, setEditingName] = useState(false)
  const [nameInput, setNameInput] = useState(userName)

  useEffect(() => {
    api.getSettings()
      .then(setServerInfo)
      .catch(() => setServerInfo(null))
      .finally(() => setLoading(false))
  }, [])

  const handleSaveName = () => {
    if (nameInput.trim()) {
      localStorage.setItem('council_user_name', nameInput.trim())
      setEditingName(false)
    }
  }

  const handleResetOnboarding = () => {
    if (confirm('Reset onboarding? You\'ll see the setup wizard on next reload.')) {
      localStorage.removeItem('council_onboarding_complete')
      window.location.reload()
    }
  }

  const handleClearData = () => {
    if (confirm('This will delete all agents, regions, and I/O ports. Are you sure?')) {
      // TODO: add a backend endpoint for this
      alert('Not yet implemented — delete ~/.council/council.db and restart the backend.')
    }
  }

  const mcpConfigStr = serverInfo?.mcp_config
    ? JSON.stringify(serverInfo.mcp_config, null, 2)
    : ''

  const handleCopyMcp = () => {
    navigator.clipboard.writeText(mcpConfigStr)
    setMcpCopied(true)
    setTimeout(() => setMcpCopied(false), 2000)
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Settings className="w-4 h-4" />
        <h3 className="text-base font-semibold">Settings</h3>
      </div>

      {/* ── User Profile ── */}
      <section className="space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <User className="w-3 h-3" /> Profile
        </div>
        <div className="bg-secondary/50 rounded-lg p-3">
          {editingName ? (
            <div className="flex gap-2">
              <input
                type="text"
                value={nameInput}
                onChange={(e) => setNameInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSaveName()}
                autoFocus
                className="flex-1 px-2 py-1 text-sm bg-background border border-border rounded-md focus:outline-none focus:ring-1 focus:ring-ring"
              />
              <button
                onClick={handleSaveName}
                className="text-xs px-2 py-1 rounded-md bg-primary text-primary-foreground"
              >
                Save
              </button>
              <button
                onClick={() => { setEditingName(false); setNameInput(userName) }}
                className="text-xs px-2 py-1 rounded-md text-muted-foreground hover:text-foreground"
              >
                Cancel
              </button>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-full bg-primary/15 flex items-center justify-center text-xs font-semibold text-foreground">
                  {userName.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-medium">{userName}</p>
                  <p className="text-[10px] text-muted-foreground">Council Administrator</p>
                </div>
              </div>
              <button
                onClick={() => setEditingName(true)}
                className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
              >
                Edit
              </button>
            </div>
          )}
        </div>
      </section>

      {/* ── Connection Info ── */}
      <section className="space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <Server className="w-3 h-3" /> Connection
        </div>
        <div className="bg-secondary/50 rounded-lg p-3 space-y-0.5">
          {loading ? (
            <p className="text-xs text-muted-foreground animate-pulse">Loading...</p>
          ) : serverInfo ? (
            <>
              <InfoRow label="Status" value="Connected" />
              <InfoRow label="API URL" value={serverInfo.api_url} mono copyable />
              <InfoRow label="Port" value={serverInfo.port} mono />
              <InfoRow label="Version" value={serverInfo.version} />
            </>
          ) : (
            <p className="text-xs text-destructive">Unable to reach backend</p>
          )}
        </div>
      </section>

      {/* ── Database ── */}
      <section className="space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <Database className="w-3 h-3" /> Database
        </div>
        <div className="bg-secondary/50 rounded-lg p-3 space-y-0.5">
          {serverInfo && (
            <>
              <InfoRow label="Path" value={serverInfo.db_path} mono copyable />
              <InfoRow label="Data Dir" value={serverInfo.data_dir} mono />
            </>
          )}
          <InfoRow label="Agents" value={stats.total_agents || 0} />
          <InfoRow label="Seats" value={`${stats.occupied_seats || 0} / ${stats.total_seats || 0} occupied`} />
          <InfoRow label="Regions" value={stats.total_regions || 0} />
          <InfoRow label="I/O Ports" value={(stats.total_inputs || 0) + (stats.total_outputs || 0)} />
        </div>
      </section>

      {/* ── MCP Config ── */}
      <section className="space-y-2">
        <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          <Terminal className="w-3 h-3" /> MCP Server
        </div>
        <div className="bg-secondary/50 rounded-lg p-3 space-y-2">
          <p className="text-[10px] text-muted-foreground">
            Add this to your AI tool's MCP config to connect Council.
          </p>
          {serverInfo && (
            <>
              <InfoRow label="Command" value={serverInfo.mcp_command} mono copyable />
              <div className="relative">
                <pre className="text-[10px] font-mono text-foreground/80 bg-background rounded-md p-2.5 overflow-x-auto whitespace-pre leading-relaxed">
                  {mcpConfigStr}
                </pre>
                <div className="absolute top-1.5 right-1.5">
                  <button
                    onClick={handleCopyMcp}
                    className="flex items-center gap-1 text-[10px] px-2 py-0.5 rounded bg-muted text-muted-foreground hover:text-foreground transition-colors"
                  >
                    {mcpCopied ? <><Check className="w-3 h-3" /> Copied</> : <><Copy className="w-3 h-3" /> Copy</>}
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </section>

      {/* ── Actions ── */}
      <section className="space-y-2">
        <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Actions
        </div>
        <div className="space-y-1">
          <button
            onClick={() => loadCouncil()}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-left hover:bg-muted/50 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5 text-muted-foreground" />
            Reload Council Data
          </button>
          <button
            onClick={handleResetOnboarding}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-left hover:bg-muted/50 transition-colors"
          >
            <RotateCcw className="w-3.5 h-3.5 text-muted-foreground" />
            Re-run Onboarding
          </button>
          <button
            onClick={handleClearData}
            className="flex items-center gap-2 w-full px-3 py-2 rounded-lg text-sm text-left text-destructive hover:bg-destructive/10 transition-colors"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Clear All Data
          </button>
        </div>
      </section>
    </div>
  )
}
