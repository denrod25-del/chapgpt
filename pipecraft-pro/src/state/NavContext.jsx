import { createContext, useContext, useState } from 'react'

// Tiny screen router: navigate('job-board') or navigate('service-call', { jobId }).
const NavContext = createContext(null)

export function NavProvider({ children }) {
  const [route, setRoute] = useState({ screen: 'home', params: {} })
  const navigate = (screen, params = {}) => {
    setRoute({ screen, params })
    window.scrollTo({ top: 0 })
  }
  return <NavContext.Provider value={{ route, navigate }}>{children}</NavContext.Provider>
}

export function useNav() {
  const ctx = useContext(NavContext)
  if (!ctx) throw new Error('useNav must be used inside <NavProvider>')
  return ctx
}
