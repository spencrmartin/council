/**
 * Council API client — mirrors Brian's api pattern.
 */
const BASE = '/api'

async function request(path, options = {}) {
  const url = `${BASE}${path}`
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API ${res.status}: ${body}`)
  }
  return res.json()
}

// ── Council overview ─────────────────────────────────────────────────────
export const getCouncil = () => request('/council')

// ── Agents ──────────────────────────────────────────────────────────────────
export const listAgents = () => request('/agents')
export const getAgent = (id) => request(`/agents/${id}`)
export const createAgent = (data) => request('/agents', { method: 'POST', body: JSON.stringify(data) })
export const updateAgent = (id, data) => request(`/agents/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteAgent = (id) => request(`/agents/${id}`, { method: 'DELETE' })
export const assignSeat = (agentId, seatId) => request(`/agents/${agentId}/assign/${seatId}`, { method: 'POST' })
export const unseatAgent = (agentId) => request(`/agents/${agentId}/unseat`, { method: 'POST' })

// ── Seats ───────────────────────────────────────────────────────────────────
export const listSeats = () => request('/seats')
export const listEmptySeats = () => request('/seats/empty')

// ── Regions ─────────────────────────────────────────────────────────────────
export const listRegions = () => request('/regions')
export const getRegion = (id) => request(`/regions/${id}`)
export const createRegion = (data) => request('/regions', { method: 'POST', body: JSON.stringify(data) })
export const updateRegion = (id, data) => request(`/regions/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteRegion = (id) => request(`/regions/${id}`, { method: 'DELETE' })
export const assignSeatsToRegion = (regionId, seatIds) =>
  request(`/regions/${regionId}/seats`, { method: 'POST', body: JSON.stringify({ seat_ids: seatIds }) })

// ── IO Ports ────────────────────────────────────────────────────────────────
export const listIOPorts = (params = {}) => {
  const qs = new URLSearchParams()
  if (params.region_id) qs.set('region_id', params.region_id)
  if (params.direction) qs.set('direction', params.direction)
  const q = qs.toString()
  return request(`/io-ports${q ? '?' + q : ''}`)
}
export const createIOPort = (data) => request('/io-ports', { method: 'POST', body: JSON.stringify(data) })
export const updateIOPort = (id, data) => request(`/io-ports/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteIOPort = (id) => request(`/io-ports/${id}`, { method: 'DELETE' })

// ── Constitution ────────────────────────────────────────────────────────────
export const getConstitution = () => request('/constitution')
export const listConstitutions = () => request('/constitutions')
export const createConstitution = (data) => request('/constitutions', { method: 'POST', body: JSON.stringify(data) })
export const updateConstitution = (data) => request('/constitution', { method: 'PUT', body: JSON.stringify(data) })
export const activateConstitution = (id) => request(`/constitutions/${id}/activate`, { method: 'POST' })

// ── Community Members ────────────────────────────────────────────────────────
export const listCommunityMembers = (params = {}) => {
  const qs = new URLSearchParams()
  if (params.cohort) qs.set('cohort', params.cohort)
  if (params.active_only !== undefined) qs.set('active_only', params.active_only)
  const q = qs.toString()
  return request(`/community/members${q ? '?' + q : ''}`)
}
export const getCommunityMember = (id) => request(`/community/members/${id}`)
export const createCommunityMember = (data) => request('/community/members', { method: 'POST', body: JSON.stringify(data) })
export const updateCommunityMember = (id, data) => request(`/community/members/${id}`, { method: 'PUT', body: JSON.stringify(data) })
export const deleteCommunityMember = (id) => request(`/community/members/${id}`, { method: 'DELETE' })
export const getCommunityStats = () => request('/community/stats')
export const resetCommunityDefaults = () => request('/community/reset', { method: 'POST' })

// ── Focus Groups ────────────────────────────────────────────────────────────
export const listFocusGroups = () => request('/community/focus-groups')
export const getFocusGroup = (id) => request(`/community/focus-groups/${id}`)
export const createFocusGroup = (data) => request('/community/focus-groups', { method: 'POST', body: JSON.stringify(data) })

// ── Community Polls ─────────────────────────────────────────────────────────
export const listCommunityPolls = () => request('/community/polls')
export const createCommunityPoll = (data) => request('/community/polls', { method: 'POST', body: JSON.stringify(data) })

// ── Town Hall ───────────────────────────────────────────────────────────────
export const runTownHall = (data) => request('/community/town-hall', { method: 'POST', body: JSON.stringify(data) })

// ── Member Consultation ─────────────────────────────────────────────────────
export const consultMember = (id, data) => request(`/community/members/${id}/consult`, { method: 'POST', body: JSON.stringify(data) })

// ── Settings ────────────────────────────────────────────────────────────────
export const getSettings = () => request('/settings')
