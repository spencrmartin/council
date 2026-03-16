/**
 * SidePanel — icon rail with popover panels.
 *
 * The sidebar is always a narrow icon rail. Each nav button opens a popover
 * panel that floats to the right of the rail. Clicking the active button
 * or clicking outside closes the popover.
 */
import { useState, useRef, useEffect } from 'react'
import useStore from '@/store/useStore'
import { motion, AnimatePresence } from 'framer-motion'
import AgentCard from './AgentCard'
import RegionCard from './RegionCard'
import MemberCard from './MemberCard'
import CreateAgentForm from './CreateAgentForm'
import CreateRegionForm from './CreateRegionForm'
import CreateIOPortForm from './CreateIOPortForm'
import ConstitutionEditor from './ConstitutionEditor'
import SettingsPanel from './SettingsPanel'
import { CouncilIcon, InputIcon, OutputIcon } from '@/lib/icons'
import { Armchair, Users, Hexagon, Cable, ScrollText, Settings, UsersRound } from 'lucide-react'

const TABS = [
  { key: 'seat', label: 'Seat', Icon: Armchair },
  { key: 'agents', label: 'Agents', Icon: Users },
  { key: 'regions', label: 'Regions', Icon: Hexagon },
  { key: 'community', label: 'Community', Icon: UsersRound },
  { key: 'io', label: 'I/O', Icon: Cable },
  { key: 'constitution', label: 'Constitution', Icon: ScrollText },
]

const COHORT_COLORS = {
  builders: '#3b82f6',
  operators: '#f59e0b',
  advocates: '#ef4444',
  pragmatists: '#10b981',
  creatives: '#a855f7',
  skeptics: '#6b7280',
}

const COHORT_LABELS = {
  builders: 'Builders',
  operators: 'Operators',
  advocates: 'Advocates',
  pragmatists: 'Pragmatists',
  creatives: 'Creatives',
  skeptics: 'Skeptics',
}

// Settings is separate — pinned at the bottom of the rail
const SETTINGS_KEY = 'settings'

// ── Community Panel (inline) ─────────────────────────────────────────────────

function CommunityPanel({ members }) {
  const [filter, setFilter] = useState(null) // cohort filter
  const [searchQuery, setSearchQuery] = useState('')

  const filtered = members.filter((m) => {
    if (filter && m.cohort !== filter) return false
    if (searchQuery) {
      const q = searchQuery.toLowerCase()
      return (
        m.name.toLowerCase().includes(q) ||
        m.profession.toLowerCase().includes(q) ||
        (m.passions || []).some((p) => p.toLowerCase().includes(q))
      )
    }
    return true
  })

  // Group by cohort
  const cohorts = ['builders', 'operators', 'advocates', 'pragmatists', 'creatives', 'skeptics']
  const grouped = {}
  cohorts.forEach((c) => {
    const inCohort = filtered.filter((m) => m.cohort === c)
    if (inCohort.length > 0) grouped[c] = inCohort
  })

  return (
    <div className="space-y-3">
      <h3 className="text-base font-semibold flex items-center gap-2">
        <UsersRound className="w-4 h-4" />
        Community ({members.length})
      </h3>

      <p className="text-xs text-muted-foreground">
        60 diverse voices across 6 cohorts. Click a member in the outer ring to see their profile.
      </p>

      {/* Search */}
      <input
        type="text"
        placeholder="Search by name, role, or passion..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        className="w-full text-xs px-2.5 py-1.5 rounded-md bg-secondary border border-border focus:outline-none focus:ring-1 focus:ring-primary/50"
      />

      {/* Cohort filter chips */}
      <div className="flex flex-wrap gap-1">
        <button
          onClick={() => setFilter(null)}
          className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${
            !filter ? 'bg-foreground text-background' : 'bg-muted text-muted-foreground hover:bg-muted/80'
          }`}
        >
          All
        </button>
        {cohorts.map((c) => {
          const count = members.filter((m) => m.cohort === c).length
          return (
            <button
              key={c}
              onClick={() => setFilter(filter === c ? null : c)}
              className={`text-[10px] px-2 py-0.5 rounded-full transition-colors flex items-center gap-1 ${
                filter === c
                  ? 'text-background'
                  : 'text-muted-foreground hover:opacity-80'
              }`}
              style={{
                backgroundColor: filter === c ? COHORT_COLORS[c] : `${COHORT_COLORS[c]}20`,
                color: filter === c ? '#fff' : COHORT_COLORS[c],
              }}
            >
              <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: filter === c ? '#fff' : COHORT_COLORS[c] }} />
              {COHORT_LABELS[c]} ({count})
            </button>
          )
        })}
      </div>

      {/* Member list */}
      <div className="space-y-3">
        {Object.entries(grouped).map(([cohort, cohortMembers]) => (
          <div key={cohort}>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: COHORT_COLORS[cohort] }} />
              <span className="text-[10px] font-bold uppercase tracking-wider" style={{ color: COHORT_COLORS[cohort] }}>
                {COHORT_LABELS[cohort]} ({cohortMembers.length})
              </span>
            </div>
            <div className="space-y-1.5">
              {cohortMembers.map((member) => (
                <MemberCard key={member.id} member={member} compact={!filter && !searchQuery} />
              ))}
            </div>
          </div>
        ))}
        {Object.keys(grouped).length === 0 && (
          <p className="text-sm text-muted-foreground text-center py-6">
            No members match your search.
          </p>
        )}
      </div>
    </div>
  )
}

export default function SidePanel() {
  const {
    seats, agents, regions, ioPorts, communityMembers,
    selectedSeatId, selectedRegionId,
    selectSeat, selectRegion,
  } = useStore()

  const [openPanel, setOpenPanel] = useState(null)
  const popoverRef = useRef(null)
  const railRef = useRef(null)

  const selectedSeat = seats.find((s) => s.id === selectedSeatId)
  const seatAgent = selectedSeat?.agent_id
    ? agents.find((a) => a.id === selectedSeat.agent_id)
    : null
  const seatRegion = selectedSeat?.region_id
    ? regions.find((r) => r.id === selectedSeat.region_id)
    : null

  // Close popover on click outside
  useEffect(() => {
    if (!openPanel) return
    const handleClick = (e) => {
      if (
        popoverRef.current && !popoverRef.current.contains(e.target) &&
        railRef.current && !railRef.current.contains(e.target)
      ) {
        setOpenPanel(null)
      }
    }
    window.addEventListener('mousedown', handleClick)
    return () => window.removeEventListener('mousedown', handleClick)
  }, [openPanel])

  // Close on Escape
  useEffect(() => {
    if (!openPanel) return
    const handleKey = (e) => {
      if (e.key === 'Escape') setOpenPanel(null)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [openPanel])

  const togglePanel = (key) => {
    setOpenPanel((prev) => (prev === key ? null : key))
  }

  // ── Popover content by panel key ──
  const renderPanelContent = () => {
    switch (openPanel) {
      case 'seat':
        return selectedSeat ? (
          <div className="space-y-4">
            <div>
              <h3 className="text-base font-semibold">
                Seat {selectedSeat.label || selectedSeat.id.slice(0, 8)}
              </h3>
              <p className="text-xs text-muted-foreground">
                Row {selectedSeat.row + 1}, Position {selectedSeat.position + 1}
              </p>
            </div>
            {seatAgent ? (
              <AgentCard agent={seatAgent} />
            ) : (
              <div className="border border-dashed border-border rounded-lg p-4 text-center text-muted-foreground text-sm">
                <Armchair className="w-5 h-5 mx-auto mb-2 opacity-40" />
                <p>Empty seat</p>
                <p className="text-xs mt-1">Assign an agent from the Agents panel</p>
              </div>
            )}
            {seatRegion && (
              <div>
                <p className="text-xs text-muted-foreground mb-1">Region</p>
                <button
                  onClick={() => { setOpenPanel('regions') }}
                  className="flex items-center gap-2 text-sm hover:underline"
                >
                  <span className="w-3 h-3 rounded-full" style={{ backgroundColor: seatRegion.color }} />
                  {seatRegion.name}
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="text-center text-muted-foreground py-8">
            <CouncilIcon className="w-7 h-7 mx-auto mb-3 opacity-40" />
            <p className="text-sm">Click a seat to inspect it</p>
          </div>
        )

      case 'agents':
        return (
          <div className="space-y-3">
            <h3 className="text-base font-semibold flex items-center gap-2">
              <Users className="w-4 h-4" />
              Agents ({agents.length})
            </h3>
            <CreateAgentForm />
            {agents.map((agent) => (
              <AgentCard key={agent.id} agent={agent} showActions />
            ))}
            {agents.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-6">
                No agents yet. Create one above.
              </p>
            )}
          </div>
        )

      case 'regions':
        return (
          <div className="space-y-3">
            <h3 className="text-base font-semibold flex items-center gap-2">
              <Hexagon className="w-4 h-4" />
              Regions ({regions.length})
            </h3>
            <CreateRegionForm />
            {regions.map((region) => (
              <RegionCard key={region.id} region={region} />
            ))}
            {regions.length === 0 && (
              <p className="text-sm text-muted-foreground text-center py-6">
                No regions yet. Create one to group seats.
              </p>
            )}
          </div>
        )

      case 'community':
        return <CommunityPanel members={communityMembers} />

      case 'io':
        return (
          <div className="space-y-3">
            <h3 className="text-base font-semibold flex items-center gap-2">
              <Cable className="w-4 h-4" />
              I/O Ports ({ioPorts.length})
            </h3>
            <CreateIOPortForm />
            {ioPorts.map((port) => (
              <div key={port.id} className="bg-secondary/50 rounded-lg p-3 text-sm space-y-1">
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-mono px-1.5 py-0.5 rounded flex items-center gap-1 ${
                    port.direction === 'input'
                      ? 'bg-blue-500/20 text-blue-400'
                      : 'bg-emerald-500/20 text-emerald-400'
                  }`}>
                    {port.direction === 'input'
                      ? <><InputIcon className="w-3 h-3" /> IN</>
                      : <><OutputIcon className="w-3 h-3" /> OUT</>
                    }
                  </span>
                  <span className="font-medium">{port.name}</span>
                </div>
                {port.description && (
                  <p className="text-xs text-muted-foreground">{port.description}</p>
                )}
                {port.region_id && (
                  <p className="text-xs text-muted-foreground">
                    Region: {regions.find((r) => r.id === port.region_id)?.name || 'Unknown'}
                  </p>
                )}
                {port.data_type && (
                  <span className="text-xs font-mono text-muted-foreground">type: {port.data_type}</span>
                )}
              </div>
            ))}
          </div>
        )

      case 'constitution':
        return <ConstitutionEditor />

      case SETTINGS_KEY:
        return <SettingsPanel />

      default:
        return null
    }
  }

  // Wider popovers for constitution, settings, and community
  const popoverWidth =
    openPanel === 'constitution' ? 360 :
    openPanel === SETTINGS_KEY ? 340 :
    openPanel === 'community' ? 340 :
    288

  // Get the label for the popover header
  const panelLabel =
    openPanel === SETTINGS_KEY
      ? 'Settings'
      : TABS.find((t) => t.key === openPanel)?.label

  // User initial for the settings avatar
  const userName = localStorage.getItem('council_user_name') || 'U'
  const userInitial = userName.charAt(0).toUpperCase()

  return (
    <div className="relative h-full flex">
      {/* Icon rail */}
      <div
        ref={railRef}
        className="flex flex-col items-center h-full w-12 bg-card/90 backdrop-blur-xl border border-border/50 shadow-xl rounded-xl py-3 gap-1 shrink-0 z-20"
      >
        {/* Logo */}
        <div className="flex items-center justify-center w-7 h-7 mb-1">
          <CouncilIcon className="w-4 h-4 text-muted-foreground" />
        </div>

        <div className="w-5 h-px bg-border my-1" />

        {/* Nav buttons */}
        {TABS.map(({ key, label, Icon }) => (
          <button
            key={key}
            onClick={() => togglePanel(key)}
            title={label}
            className={`flex items-center justify-center w-8 h-8 rounded-lg transition-all duration-150 ${
              openPanel === key
                ? 'bg-primary/15 text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
            }`}
          >
            <Icon className="w-4 h-4" />
          </button>
        ))}

        {/* Spacer */}
        <div className="flex-1" />

        {/* Settings — pinned at bottom */}
        <div className="w-5 h-px bg-border my-1" />
        <button
          onClick={() => togglePanel(SETTINGS_KEY)}
          title="Settings"
          className={`w-8 h-8 rounded-full flex items-center justify-center transition-all duration-150 ${
            openPanel === SETTINGS_KEY
              ? 'bg-primary/15 text-foreground ring-1 ring-primary/30'
              : 'bg-muted text-muted-foreground hover:text-foreground hover:bg-muted/80'
          }`}
        >
          <span className="text-[10px] font-semibold">{userInitial}</span>
        </button>
      </div>

      {/* Popover panel — floats to the right of the rail */}
      <AnimatePresence>
        {openPanel && (
          <motion.div
            ref={popoverRef}
            key={openPanel}
            initial={{ opacity: 0, x: -8, scale: 0.97 }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{ opacity: 0, x: -8, scale: 0.97 }}
            transition={{ duration: 0.15, ease: 'easeOut' }}
            className="absolute left-14 top-0 bottom-0 z-10"
            style={{ width: popoverWidth }}
          >
            <div className="h-full bg-card/90 backdrop-blur-xl border border-border/50 shadow-2xl rounded-xl overflow-hidden flex flex-col">
              {/* Popover header */}
              <div className="flex items-center justify-between px-3 py-2.5 border-b border-border shrink-0">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  {panelLabel}
                </span>
                <button
                  onClick={() => setOpenPanel(null)}
                  className="text-muted-foreground hover:text-foreground transition-colors text-xs"
                >
                  ✕
                </button>
              </div>

              {/* Popover content */}
              <div className="flex-1 overflow-y-auto p-3">
                {renderPanelContent()}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
