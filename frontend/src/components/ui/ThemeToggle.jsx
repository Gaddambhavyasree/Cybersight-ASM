import { Sun, Moon } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'

export default function ThemeToggle({ variant = 'pill' }) {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'

  if (variant === 'icon') {
    return (
      <button
        onClick={toggleTheme}
        aria-label={`Switch to ${isDark ? 'light' : 'dark'} mode`}
        className="inline-flex h-9 w-9 items-center justify-center rounded-xl border border-[var(--border)] bg-[var(--card)] text-[var(--muted-foreground)] hover:text-[var(--foreground)] hover:bg-[var(--muted)] transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--ring)] focus:ring-offset-0"
      >
        {isDark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
      </button>
    )
  }

  // pill switch: ☀️ Light / Dark
  return (
    <div className="inline-flex items-center gap-1.5 rounded-full border border-[var(--border)] bg-[var(--muted)] p-1">
      <button
        onClick={() => isDark && toggleTheme()}
        aria-label="Light mode"
        aria-pressed={!isDark}
        className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-all ${
          !isDark
            ? 'bg-[var(--card)] text-[var(--foreground)] shadow-sm border border-[var(--border)]'
            : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
        }`}
      >
        <Sun className="h-3.5 w-3.5" />
        Light
      </button>
      <button
        onClick={() => !isDark && toggleTheme()}
        aria-label="Dark mode"
        aria-pressed={isDark}
        className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold transition-all ${
          isDark
            ? 'bg-[var(--card)] text-[var(--foreground)] shadow-sm border border-[var(--border)]'
            : 'text-[var(--muted-foreground)] hover:text-[var(--foreground)]'
        }`}
      >
        <Moon className="h-3.5 w-3.5" />
        Dark
      </button>
    </div>
  )
}

// compact switch for header
export function ThemeSwitch() {
  const { theme, toggleTheme } = useTheme()
  const isDark = theme === 'dark'
  return (
    <button
      onClick={toggleTheme}
      role="switch"
      aria-checked={isDark}
      aria-label={`Toggle theme, currently ${theme}`}
      className="relative inline-flex h-7 w-[54px] items-center rounded-full border border-[var(--border)] bg-[var(--muted)] p-1 transition-colors focus:outline-none focus:ring-2 focus:ring-[var(--ring)] focus:ring-offset-0"
    >
      <span
        className={`inline-flex h-5 w-5 items-center justify-center rounded-full bg-[var(--card)] shadow-sm border border-[var(--border)] text-[var(--foreground)] transition-transform duration-200 ${
          isDark ? 'translate-x-[26px]' : 'translate-x-0'
        }`}
      >
        {isDark ? <Moon className="h-3 w-3" /> : <Sun className="h-3 w-3" />}
      </span>
      <span className="sr-only">Toggle theme</span>
    </button>
  )
}
