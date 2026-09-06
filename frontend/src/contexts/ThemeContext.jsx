import { createContext, useContext, useEffect, useState, useCallback } from 'react'

const ThemeContext = createContext(null)
const STORAGE_KEY = 'cybersight-theme'

function getInitialTheme() {
  if (typeof window === 'undefined') return 'dark'
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored === 'light' || stored === 'dark') return stored
  // default to dark to preserve existing behavior, but respect system preference as fallback if no stored
  // per requirement: default can remain DARK
  return 'dark'
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(getInitialTheme)
  const [mounted, setMounted] = useState(false)

  const applyTheme = useCallback((t) => {
    const root = document.documentElement
    root.classList.remove('light', 'dark')
    root.classList.add(t)
    root.style.colorScheme = t
  }, [])

  useEffect(() => {
    setMounted(true)
    applyTheme(theme)
  }, []) // eslint-disable-line

  useEffect(() => {
    if (!mounted) return
    applyTheme(theme)
    localStorage.setItem(STORAGE_KEY, theme)
  }, [theme, mounted, applyTheme])

  const setTheme = useCallback((t) => {
    if (t !== 'light' && t !== 'dark') return
    setThemeState(t)
  }, [])

  const toggleTheme = useCallback(() => {
    setThemeState((prev) => (prev === 'dark' ? 'light' : 'dark'))
  }, [])

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme, mounted }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider')
  return ctx
}
