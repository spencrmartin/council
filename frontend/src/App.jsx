import { useEffect, useState } from 'react'
import useStore from '@/store/useStore'
import Hemicycle from '@/components/Hemicycle'
import SidePanel from '@/components/SidePanel'
import SeatPopover from '@/components/SeatPopover'
import StatsBar from '@/components/StatsBar'
import ConstitutionBadge from '@/components/ConstitutionBadge'
import Onboarding from '@/components/Onboarding'
import { AnimatePresence } from 'framer-motion'
import { Landmark, AlertTriangle, RefreshCw } from 'lucide-react'

const RAIL_WIDTH = 48
const RAIL_PADDING = 12

function App() {
  const { loading, error, loadCouncil, seatPopover } = useStore()
  const [dimensions, setDimensions] = useState({ width: window.innerWidth, height: window.innerHeight })
  const [showOnboarding, setShowOnboarding] = useState(() => {
    return !localStorage.getItem('council_onboarding_complete')
  })

  useEffect(() => { loadCouncil() }, [])

  useEffect(() => {
    const handleResize = () => setDimensions({ width: window.innerWidth, height: window.innerHeight })
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const hemicycleWidth = dimensions.width - RAIL_WIDTH - RAIL_PADDING

  const handleOnboardingComplete = async () => {
    localStorage.setItem('council_onboarding_complete', 'true')
    await loadCouncil() // Reload to pick up agents + constitution from onboarding
    setShowOnboarding(false)
  }

  if (showOnboarding && !loading) {
    return <Onboarding onComplete={handleOnboardingComplete} />
  }

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <Landmark className="w-12 h-12 mx-auto text-muted-foreground animate-pulse" />
          <p className="text-muted-foreground text-sm">Loading Council...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="h-screen flex items-center justify-center bg-background">
        <div className="text-center space-y-4 max-w-md">
          <AlertTriangle className="w-10 h-10 mx-auto text-destructive" />
          <p className="text-destructive font-medium">Failed to load Council</p>
          <p className="text-sm text-muted-foreground">{error}</p>
          <button
            onClick={loadCouncil}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm rounded-md bg-primary text-primary-foreground hover:opacity-90"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="h-screen flex overflow-hidden bg-background">
      {/* Sidebar rail wrapper — padding creates floating gap */}
      <div
        className="flex-shrink-0 h-full py-3 pl-3"
        style={{ width: RAIL_WIDTH + RAIL_PADDING }}
      >
        <SidePanel />
      </div>

      {/* Main content area */}
      <div className="relative flex-1 min-w-0 min-h-0">
        {/* Stats bar — floating top center */}
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
          <StatsBar />
        </div>

        {/* Hemicycle visualization */}
        <Hemicycle width={hemicycleWidth} height={dimensions.height} />

        {/* Constitution badge — bottom right of hemicycle */}
        <ConstitutionBadge />

        {/* Seat popover — positioned at click coordinates */}
        <AnimatePresence>
          {seatPopover && <SeatPopover />}
        </AnimatePresence>
      </div>
    </div>
  )
}

export default App
