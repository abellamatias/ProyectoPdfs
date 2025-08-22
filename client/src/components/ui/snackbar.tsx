import { useEffect, useRef } from 'react'

type SnackbarVariant = 'success' | 'error'

interface SnackbarProps {
  open: boolean
  message: string
  variant?: SnackbarVariant
  duration?: number
  onClose?: () => void
}

export function Snackbar({ open, message, variant = 'success', duration = 3000, onClose }: SnackbarProps) {
  const timerRef = useRef<number | null>(null)

  useEffect(() => {
    if (!open) return
    if (timerRef.current) window.clearTimeout(timerRef.current)
    timerRef.current = window.setTimeout(() => {
      onClose?.()
    }, duration)
    return () => {
      if (timerRef.current) window.clearTimeout(timerRef.current)
    }
  }, [open, duration, onClose])

  if (!open) return null

  const base = 'fixed left-1/2 -translate-x-1/2 bottom-6 z-50 px-4 py-3 rounded-md shadow-lg text-sm'
  const color = variant === 'success'
    ? 'bg-emerald-600 text-white'
    : 'bg-red-600 text-white'

  return (
    <div role="alert" className={`${base} ${color}`}>
      {message}
    </div>
  )
}


