/**
 * Hemicycle — D3-powered council seat visualization.
 *
 * Renders seats in concentric arcs (hemicycle layout).
 * Seats are coloured by region. Occupied seats show agent icon.
 * Click a seat to select it; hover for tooltip.
 */
import { useEffect, useRef } from 'react'
import * as d3 from 'd3'
import useStore from '@/store/useStore'

const SEAT_RADIUS = 14
const COMMUNITY_SEAT_RADIUS = 12
const COMMUNITY_GAP = 28  // visual gap between council and community rows
const TOOLTIP_OFFSET = 12

// Cohort colours — distinct, muted palette
const COHORT_COLORS = {
  builders: '#3b82f6',    // blue
  operators: '#f59e0b',   // amber
  advocates: '#ef4444',   // red
  pragmatists: '#10b981', // emerald
  creatives: '#a855f7',   // purple
  skeptics: '#6b7280',    // gray
}

const COHORT_LABELS = {
  builders: 'Builders',
  operators: 'Operators',
  advocates: 'Advocates',
  pragmatists: 'Pragmatists',
  creatives: 'Creatives',
  skeptics: 'Skeptics',
}

// Minimal SVG paths for agent icons (rendered inside D3 — can't use React components)
// These are simplified 16x16 viewBox paths from Lucide
const ICON_PATHS = {
  bot: 'M8 2a2 2 0 0 1 2 2v1h-4V4a2 2 0 0 1 2-2ZM4 6h8a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2Zm1.5 3a1 1 0 1 0 0 2 1 1 0 0 0 0-2Zm5 0a1 1 0 1 0 0 2 1 1 0 0 0 0-2Z',
  brain: 'M8 1C6.3 1 5 2.3 5 4c0 .4.1.7.2 1C3.4 5.4 2 7 2 9c0 1.7 1 3.2 2.5 3.8.3 1.3 1.5 2.2 2.8 2.2H8.7c1.3 0 2.5-.9 2.8-2.2C13 12.2 14 10.7 14 9c0-2-1.4-3.6-3.2-4 .1-.3.2-.6.2-1 0-1.7-1.3-3-3-3Z',
  cpu: 'M5 2v2H3a1 1 0 0 0-1 1v2H0v2h2v2a1 1 0 0 0 1 1h2v2h2v-2h2v2h2v-2h2a1 1 0 0 0 1-1V9h2V7h-2V5a1 1 0 0 0-1-1h-2V2H9v2H7V2H5Zm0 4h6v6H5V6Z',
  eye: 'M8 3C4.4 3 1.4 5.4.2 8c1.2 2.6 4.2 5 7.8 5s6.6-2.4 7.8-5c-1.2-2.6-4.2-5-7.8-5Zm0 8a3 3 0 1 1 0-6 3 3 0 0 1 0 6Z',
  search: 'M11.7 10.3a6 6 0 1 0-1.4 1.4l3.5 3.5 1.4-1.4-3.5-3.5ZM7 11a4 4 0 1 1 0-8 4 4 0 0 1 0 8Z',
  target: 'M8 1a7 7 0 1 0 0 14A7 7 0 0 0 8 1Zm0 2a5 5 0 1 1 0 10A5 5 0 0 1 8 3Zm0 2a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm0 2a1 1 0 1 1 0 2 1 1 0 0 1 0-2Z',
  zap: 'M9 1 3 9h4l-1 6 6-8H8l1-6Z',
  shield: 'M8 1 2 4v4c0 3.5 2.6 6.8 6 7.9 3.4-1.1 6-4.4 6-7.9V4L8 1Z',
  'bar-chart': 'M2 14V8h3v6H2Zm5 0V2h3v12H7Zm5 0V5h3v9h-3Z',
  palette: 'M8 1a7 7 0 0 0-1 13.9c.6.1.8-.2.8-.6V13c-3.3.7-4-1.4-4-1.4-.5-1.4-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.1.1 1.7 1.2 1.7 1.2 1 1.8 2.7 1.3 3.3 1 .1-.8.4-1.3.7-1.6-2.7-.3-5.5-1.3-5.5-6 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.5.1-3.2 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0C15.3 1.8 16.3 2 16.3 2c.7 1.7.3 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.7-2.8 5.7-5.5 6 .4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A7 7 0 0 0 8 1Z',
}

// Role labels for tooltip
const ROLE_LABELS = {
  speaker: 'Speaker',
  minister: 'Minister',
  delegate: 'Delegate',
  observer: 'Observer',
  auditor: 'Auditor',
}

export default function Hemicycle({ width, height }) {
  const svgRef = useRef(null)
  const tooltipRef = useRef(null)
  const {
    seats, agents, regions, communityMembers,
    selectedSeatId, selectSeat, openSeatPopover, closeSeatPopover, seatPopover,
    selectedMemberId, selectMember, openMemberPopover, closeMemberPopover, memberPopover,
    hoveredMemberId, setHoveredMember,
  } = useStore()

  // Build lookup maps
  const agentMap = Object.fromEntries(agents.map((a) => [a.id, a]))
  const regionMap = Object.fromEntries(regions.map((r) => [r.id, r]))

  useEffect(() => {
    if (!svgRef.current || seats.length === 0) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const cx = width / 2
    const cy = height * 0.85

    // Group seats by row
    const rows = {}
    seats.forEach((s) => {
      if (!rows[s.row]) rows[s.row] = []
      rows[s.row].push(s)
    })
    const rowKeys = Object.keys(rows).map(Number).sort((a, b) => a - b)

    // Compute positions: concentric arcs from π (left) to 0 (right)
    const baseRadius = Math.min(width, height) * 0.22
    const rowGap = Math.min(width, height) * 0.08

    const positioned = []
    rowKeys.forEach((rowIdx, ri) => {
      const rowSeats = rows[rowIdx].sort((a, b) => a.position - b.position)
      const radius = baseRadius + ri * rowGap
      const n = rowSeats.length
      rowSeats.forEach((seat, i) => {
        const angle = Math.PI * (i + 0.5) / n
        const x = cx + radius * Math.cos(Math.PI - angle)
        const y = cy - radius * Math.sin(angle)
        positioned.push({ ...seat, cx: x, cy: y })
      })
    })

    // Background arc guides (subtle)
    const arcGroup = svg.append('g').attr('class', 'arcs')
    rowKeys.forEach((rowIdx, ri) => {
      const radius = baseRadius + ri * rowGap
      const arc = d3.arc()
        .innerRadius(radius - 2)
        .outerRadius(radius + 2)
        .startAngle(-Math.PI / 2)
        .endAngle(Math.PI / 2)
      arcGroup.append('path')
        .attr('d', arc)
        .attr('transform', `translate(${cx}, ${cy})`)
        .attr('fill', 'hsl(217, 32%, 17%)')
        .attr('opacity', 0.3)
    })

    // Region background arcs
    regions.forEach((region) => {
      const regionSeats = positioned.filter((s) => s.region_id === region.id)
      if (regionSeats.length === 0) return

      const angles = regionSeats.map((s) => {
        return Math.atan2(cy - s.cy, s.cx - cx)
      })
      const minAngle = Math.min(...angles) - 0.06
      const maxAngle = Math.max(...angles) + 0.06

      const regionRows = [...new Set(regionSeats.map((s) => s.row))]
      const minRow = Math.min(...regionRows)
      const maxRow = Math.max(...regionRows)
      const innerR = baseRadius + (rowKeys.indexOf(minRow)) * rowGap - SEAT_RADIUS - 4
      const outerR = baseRadius + (rowKeys.indexOf(maxRow)) * rowGap + SEAT_RADIUS + 4

      const arc = d3.arc()
        .innerRadius(innerR)
        .outerRadius(outerR)
        .startAngle(-maxAngle + Math.PI / 2)
        .endAngle(-minAngle + Math.PI / 2)
        .cornerRadius(8)

      svg.append('path')
        .attr('d', arc)
        .attr('transform', `translate(${cx}, ${cy})`)
        .attr('fill', region.color)
        .attr('opacity', 0.12)
        .attr('stroke', region.color)
        .attr('stroke-width', 1.5)
        .attr('stroke-opacity', 0.3)

      // Region label
      const midAngle = (minAngle + maxAngle) / 2
      const labelR = outerR + 20
      const lx = cx + labelR * Math.cos(midAngle)
      const ly = cy - labelR * Math.sin(midAngle)
      svg.append('text')
        .attr('x', lx)
        .attr('y', ly)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('fill', region.color)
        .attr('font-size', 11)
        .attr('font-weight', 600)
        .attr('opacity', 0.8)
        .text(region.name)
    })

    // Seat circles
    const seatGroup = svg.append('g').attr('class', 'seats')

    const seatEls = seatGroup.selectAll('g.seat')
      .data(positioned, (d) => d.id)
      .join('g')
      .attr('class', 'seat')
      .attr('transform', (d) => `translate(${d.cx}, ${d.cy})`)
      .style('cursor', 'pointer')

    // Seat background circle
    seatEls.append('circle')
      .attr('r', SEAT_RADIUS)
      .attr('fill', (d) => {
        if (d.region_id && regionMap[d.region_id]) {
          return regionMap[d.region_id].color
        }
        return d.agent_id ? '#6366f1' : 'hsl(217, 32%, 17%)'
      })
      .attr('opacity', (d) => d.agent_id ? 0.85 : 0.4)
      .attr('stroke', (d) => d.id === selectedSeatId ? '#fff' : 'transparent')
      .attr('stroke-width', 2)

    // Agent icon (SVG path) or seat label text
    seatEls.each(function (d) {
      const g = d3.select(this)
      if (d.agent_id && agentMap[d.agent_id]) {
        const agent = agentMap[d.agent_id]
        const iconPath = ICON_PATHS[agent.icon] || ICON_PATHS.bot
        // Scale the 16x16 icon to fit inside the seat
        const scale = (SEAT_RADIUS * 1.2) / 16
        g.append('path')
          .attr('d', iconPath)
          .attr('transform', `translate(${-8 * scale}, ${-8 * scale}) scale(${scale})`)
          .attr('fill', '#fff')
          .attr('opacity', 0.9)
          .attr('pointer-events', 'none')
      } else {
        g.append('text')
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'central')
          .attr('font-size', 8)
          .attr('fill', 'hsl(215, 20%, 65%)')
          .attr('pointer-events', 'none')
          .text(d.label || '')
      }
    })

    // Active agent glow
    seatEls.filter((d) => {
      const agent = d.agent_id && agentMap[d.agent_id]
      return agent && agent.status === 'active'
    }).append('circle')
      .attr('r', SEAT_RADIUS + 4)
      .attr('fill', 'none')
      .attr('stroke', (d) => {
        const agent = agentMap[d.agent_id]
        return agent?.color || '#6366f1'
      })
      .attr('stroke-width', 2)
      .attr('opacity', 0.6)
      .style('animation', 'pulse 2s ease-in-out infinite')

    // Interactions
    const tooltip = d3.select(tooltipRef.current)

    seatEls
      .on('click', (event, d) => {
        event.stopPropagation()
        // Toggle: clicking same seat closes popover, clicking new seat opens it
        if (seatPopover && seatPopover.seatId === d.id) {
          closeSeatPopover()
        } else {
          openSeatPopover(d.id, event.pageX, event.pageY)
        }
      })
      .on('mouseenter', (event, d) => {
        const agent = d.agent_id ? agentMap[d.agent_id] : null
        const region = d.region_id ? regionMap[d.region_id] : null
        let html = `<div class="font-semibold">${d.label || 'Seat'}</div>`
        if (agent) {
          html += `<div class="text-xs mt-1">${agent.name}</div>`
          html += `<div class="text-xs text-gray-400">${ROLE_LABELS[agent.role] || agent.role} · ${agent.status}</div>`
        } else {
          html += `<div class="text-xs text-gray-400 mt-1">Empty seat</div>`
        }
        if (region) {
          html += `<div class="text-xs mt-1" style="color:${region.color}">${region.name}</div>`
        }
        tooltip
          .html(html)
          .style('opacity', 1)
          .style('left', `${event.pageX + TOOLTIP_OFFSET}px`)
          .style('top', `${event.pageY + TOOLTIP_OFFSET}px`)
      })
      .on('mousemove', (event) => {
        tooltip
          .style('left', `${event.pageX + TOOLTIP_OFFSET}px`)
          .style('top', `${event.pageY + TOOLTIP_OFFSET}px`)
      })
      .on('mouseleave', () => {
        tooltip.style('opacity', 0)
      })

    // Click background to deselect and close popovers
    svg.on('click', () => { selectSeat(null); closeSeatPopover(); closeMemberPopover() })

    // Podium / speaker area
    svg.append('rect')
      .attr('x', cx - 30)
      .attr('y', cy + 10)
      .attr('width', 60)
      .attr('height', 6)
      .attr('rx', 3)
      .attr('fill', 'hsl(215, 20%, 65%)')
      .attr('opacity', 0.3)

    svg.append('text')
      .attr('x', cx)
      .attr('y', cy + 30)
      .attr('text-anchor', 'middle')
      .attr('fill', 'hsl(215, 20%, 65%)')
      .attr('font-size', 10)
      .attr('font-weight', 500)
      .attr('letter-spacing', '0.1em')
      .attr('opacity', 0.5)
      .text('PODIUM')

    // ── Community Members — cohort slices ──────────────────────────────────
    //
    // Layout: the hemicycle arc (0 to π) is divided into 6 equal slices,
    // one per cohort. Each slice's members sit on concentric arcs within
    // that angular range — exactly like the council seats but scoped to
    // their wedge. Fixed grid: 5 members per arc row → 2 rows of 5 for
    // the default 10 per cohort.
    //
    if (communityMembers.length > 0) {
      const outerRow = Math.max(...rowKeys)
      const outerRadius = baseRadius + (rowKeys.indexOf(outerRow)) * rowGap

      // ── Bucket members by cohort ──
      const cohortOrder = ['builders', 'operators', 'advocates', 'pragmatists', 'creatives', 'skeptics']
      const cohortBuckets = {}
      cohortOrder.forEach((c) => { cohortBuckets[c] = [] })
      communityMembers.forEach((m) => {
        const c = m.cohort || 'builders'
        if (!cohortBuckets[c]) cohortBuckets[c] = []
        cohortBuckets[c].push(m)
      })
      cohortOrder.forEach((c) => {
        cohortBuckets[c].sort((a, b) => a.name.localeCompare(b.name))
      })
      const activeCohorts = cohortOrder.filter((c) => cohortBuckets[c].length > 0)
      const numCohorts = activeCohorts.length

      // ── Slice geometry ──
      const sliceGapAngle = 0.06          // radians between slices
      const totalGap = sliceGapAngle * Math.max(0, numCohorts - 1)
      const sliceAngle = (Math.PI - totalGap) / numCohorts
      const communityRowGapR = rowGap      // same radial spacing as council rows
      const communityStartR = outerRadius + SEAT_RADIUS + COMMUNITY_GAP
      const COLS_PER_ROW = 5               // fixed: 5 per arc row

      // ── Divider ──
      const dividerR = outerRadius + SEAT_RADIUS + COMMUNITY_GAP * 0.45
      svg.append('path')
        .attr('d', d3.arc()
          .innerRadius(dividerR - 0.5)
          .outerRadius(dividerR + 0.5)
          .startAngle(-Math.PI / 2)
          .endAngle(Math.PI / 2)())
        .attr('transform', `translate(${cx}, ${cy})`)
        .attr('fill', 'hsl(215, 20%, 65%)')
        .attr('opacity', 0.15)

      svg.append('text')
        .attr('x', cx)
        .attr('y', cy - dividerR - 8)
        .attr('text-anchor', 'middle')
        .attr('fill', 'hsl(215, 20%, 65%)')
        .attr('font-size', 9)
        .attr('font-weight', 600)
        .attr('letter-spacing', '0.15em')
        .attr('opacity', 0.35)
        .text('COMMUNITY')

      // ── Position every member ──
      const memberPositions = []

      activeCohorts.forEach((cohort, ci) => {
        const color = COHORT_COLORS[cohort] || '#6b7280'
        const members = cohortBuckets[cohort]

        // This slice spans [sliceStartAngle, sliceEndAngle] within 0..π
        const sliceStartAngle = ci * (sliceAngle + sliceGapAngle)
        const sliceEndAngle = sliceStartAngle + sliceAngle
        const sliceMidAngle = (sliceStartAngle + sliceEndAngle) / 2

        // Split members into rows of COLS_PER_ROW
        const numRows = Math.ceil(members.length / COLS_PER_ROW)

        // ── Wedge background ──
        const wedgeInner = communityStartR - COMMUNITY_SEAT_RADIUS - 6
        const wedgeOuter = communityStartR + (numRows - 1) * communityRowGapR + COMMUNITY_SEAT_RADIUS + 6
        svg.append('path')
          .attr('d', d3.arc()
            .innerRadius(wedgeInner)
            .outerRadius(wedgeOuter)
            // d3 arc angles: 0 = 12 o'clock, clockwise. Our hemicycle 0..π maps to -π/2..π/2
            .startAngle(sliceStartAngle - Math.PI / 2)
            .endAngle(sliceEndAngle - Math.PI / 2)
            .cornerRadius(5)())
          .attr('transform', `translate(${cx}, ${cy})`)
          .attr('fill', color)
          .attr('opacity', 0.06)
          .attr('stroke', color)
          .attr('stroke-width', 1)
          .attr('stroke-opacity', 0.12)

        // ── Arc guides per row ──
        for (let ri = 0; ri < numRows; ri++) {
          const r = communityStartR + ri * communityRowGapR
          svg.append('path')
            .attr('d', d3.arc()
              .innerRadius(r - 1)
              .outerRadius(r + 1)
              .startAngle(sliceStartAngle - Math.PI / 2)
              .endAngle(sliceEndAngle - Math.PI / 2)())
            .attr('transform', `translate(${cx}, ${cy})`)
            .attr('fill', 'hsl(217, 32%, 17%)')
            .attr('opacity', 0.18)
        }

        // ── Place members on arcs ──
        let idx = 0
        for (let ri = 0; ri < numRows && idx < members.length; ri++) {
          const r = communityStartR + ri * communityRowGapR
          const remaining = members.length - idx
          const cols = Math.min(COLS_PER_ROW, remaining)

          for (let col = 0; col < cols; col++) {
            // Evenly space within the slice with padding on edges
            const t = cols === 1 ? 0.5 : col / (cols - 1)
            const pad = 0.12 // fraction of slice to pad on each side
            const angle = sliceStartAngle + sliceAngle * (pad + t * (1 - 2 * pad))

            // Convert hemicycle angle (0=left, π=right) to cartesian
            const cartAngle = Math.PI - angle
            const x = cx + r * Math.cos(cartAngle)
            const y = cy - r * Math.sin(cartAngle)

            memberPositions.push({
              ...members[idx],
              cx: x,
              cy: y,
              sliceIndex: ci,
            })
            idx++
          }
        }

        // ── Cohort label ──
        const labelR = wedgeOuter + 18
        const labelCartAngle = Math.PI - sliceMidAngle
        svg.append('text')
          .attr('x', cx + labelR * Math.cos(labelCartAngle))
          .attr('y', cy - labelR * Math.sin(labelCartAngle))
          .attr('text-anchor', 'middle')
          .attr('dominant-baseline', 'middle')
          .attr('fill', color)
          .attr('font-size', 10)
          .attr('font-weight', 600)
          .attr('opacity', 0.7)
          .text(COHORT_LABELS[cohort] || cohort)
      })

      // ── Render all member nodes ──
      const memberGroup = svg.append('g').attr('class', 'community-members')

      const memberEls = memberGroup.selectAll('g.member')
        .data(memberPositions, (d) => d.id)
        .join('g')
        .attr('class', 'member')
        .attr('transform', (d) => `translate(${d.cx}, ${d.cy})`)
        .style('cursor', 'pointer')

      memberEls.append('circle')
        .attr('r', COMMUNITY_SEAT_RADIUS)
        .attr('fill', (d) => COHORT_COLORS[d.cohort] || '#6b7280')
        .attr('opacity', (d) => d.id === selectedMemberId || d.id === hoveredMemberId ? 0.95 : 0.6)
        .attr('stroke', (d) => d.id === selectedMemberId ? '#fff' : 'transparent')
        .attr('stroke-width', 2)

      memberEls.append('text')
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'central')
        .attr('font-size', 8)
        .attr('font-weight', 600)
        .attr('fill', '#fff')
        .attr('opacity', 0.9)
        .attr('pointer-events', 'none')
        .text((d) => {
          const parts = d.name.split(' ')
          return parts.length >= 2
            ? parts[0][0] + parts[parts.length - 1][0]
            : d.name[0]
        })

      memberEls.filter((d) => d.id === selectedMemberId || d.id === hoveredMemberId)
        .append('circle')
        .attr('r', COMMUNITY_SEAT_RADIUS + 4)
        .attr('fill', 'none')
        .attr('stroke', (d) => COHORT_COLORS[d.cohort] || '#6b7280')
        .attr('stroke-width', 2)
        .attr('opacity', 0.5)

      memberEls
        .on('click', (event, d) => {
          event.stopPropagation()
          if (memberPopover && memberPopover.memberId === d.id) {
            closeMemberPopover()
          } else {
            openMemberPopover(d.id, event.pageX, event.pageY)
          }
        })
        .on('mouseenter', (event, d) => {
          setHoveredMember(d.id)
          const color = COHORT_COLORS[d.cohort] || '#888'
          let html = `<div class="font-semibold">${d.name}</div>`
          html += `<div class="text-xs mt-0.5" style="color:${color}">${COHORT_LABELS[d.cohort] || d.cohort}</div>`
          html += `<div class="text-xs text-gray-400">${d.profession}</div>`
          if (d.passions && d.passions.length > 0) {
            html += `<div class="text-xs text-gray-500 mt-1">${d.passions.slice(0, 3).join(' · ')}</div>`
          }
          tooltip
            .html(html)
            .style('opacity', 1)
            .style('left', `${event.pageX + TOOLTIP_OFFSET}px`)
            .style('top', `${event.pageY + TOOLTIP_OFFSET}px`)
        })
        .on('mousemove', (event) => {
          tooltip
            .style('left', `${event.pageX + TOOLTIP_OFFSET}px`)
            .style('top', `${event.pageY + TOOLTIP_OFFSET}px`)
        })
        .on('mouseleave', () => {
          setHoveredMember(null)
          tooltip.style('opacity', 0)
        })
    }

  }, [seats, agents, regions, communityMembers, selectedSeatId, selectedMemberId, hoveredMemberId, seatPopover, memberPopover, width, height])

  return (
    <div className="relative w-full h-full">
      <svg
        ref={svgRef}
        width={width}
        height={height}
        className="select-none"
      />
      <div
        ref={tooltipRef}
        className="fixed z-50 pointer-events-none bg-card border border-border rounded-lg px-3 py-2 shadow-xl text-sm transition-opacity duration-150"
        style={{ opacity: 0 }}
      />
    </div>
  )
}
