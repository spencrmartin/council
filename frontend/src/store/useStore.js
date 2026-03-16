/**
 * Zustand store — single source of truth for council state.
 */
import { create } from 'zustand'
import * as api from '@/lib/api'

const useStore = create((set, get) => ({
  // ── State ─────────────────────────────────────────────────────────────────
  seats: [],
  agents: [],
  regions: [],
  ioPorts: [],
  stats: {},
  constitution: { preamble: '', rules: '', goals: '', constraints: '', updated_at: null },
  loading: true,
  error: null,

  selectedSeatId: null,
  selectedAgentId: null,
  selectedRegionId: null,
  view: 'council', // 'council' | 'regions' | 'agents'

  // Seat popover — { seatId, x, y } or null
  seatPopover: null,

  // ── Actions ───────────────────────────────────────────────────────────────

  setView: (view) => set({ view }),
  selectSeat: (id) => set({ selectedSeatId: id }),
  selectAgent: (id) => set({ selectedAgentId: id }),
  selectRegion: (id) => set({ selectedRegionId: id }),
  openSeatPopover: (seatId, x, y) => set({ seatPopover: { seatId, x, y }, selectedSeatId: seatId }),
  closeSeatPopover: () => set({ seatPopover: null }),

  // Load full council state
  loadCouncil: async () => {
    set({ loading: true, error: null })
    try {
      const data = await api.getCouncil()
      set({
        seats: data.seats,
        agents: data.agents,
        regions: data.regions,
        ioPorts: data.io_ports,
        constitution: data.constitution,
        stats: data.stats,
        loading: false,
      })
    } catch (err) {
      set({ error: err.message, loading: false })
    }
  },

  // ── Agent actions ──
  createAgent: async (data) => {
    const agent = await api.createAgent(data)
    set((s) => ({ agents: [...s.agents, agent] }))
    return agent
  },

  updateAgent: async (id, data) => {
    const agent = await api.updateAgent(id, data)
    set((s) => ({ agents: s.agents.map((a) => (a.id === id ? agent : a)) }))
    return agent
  },

  deleteAgent: async (id) => {
    await api.deleteAgent(id)
    set((s) => ({
      agents: s.agents.filter((a) => a.id !== id),
      seats: s.seats.map((seat) =>
        seat.agent_id === id ? { ...seat, agent_id: null, agent: null } : seat
      ),
    }))
  },

  assignSeat: async (agentId, seatId) => {
    const agent = await api.assignSeat(agentId, seatId)
    // Reload to get consistent seat/agent state
    await get().loadCouncil()
    return agent
  },

  unseatAgent: async (agentId) => {
    await api.unseatAgent(agentId)
    await get().loadCouncil()
  },

  // ── Region actions ──
  createRegion: async (data) => {
    const region = await api.createRegion(data)
    await get().loadCouncil()
    return region
  },

  updateRegion: async (id, data) => {
    const region = await api.updateRegion(id, data)
    await get().loadCouncil()
    return region
  },

  deleteRegion: async (id) => {
    await api.deleteRegion(id)
    await get().loadCouncil()
  },

  // ── IO Port actions ──
  createIOPort: async (data) => {
    const port = await api.createIOPort(data)
    set((s) => ({ ioPorts: [...s.ioPorts, port] }))
    return port
  },

  updateIOPort: async (id, data) => {
    const port = await api.updateIOPort(id, data)
    set((s) => ({ ioPorts: s.ioPorts.map((p) => (p.id === id ? port : p)) }))
    return port
  },

  deleteIOPort: async (id) => {
    await api.deleteIOPort(id)
    set((s) => ({ ioPorts: s.ioPorts.filter((p) => p.id !== id) }))
  },

  // ── Constitution actions ──
  updateConstitution: async (data) => {
    const constitution = await api.updateConstitution(data)
    set({ constitution })
    return constitution
  },
}))

export default useStore
