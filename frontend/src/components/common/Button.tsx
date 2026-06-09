import type { ButtonHTMLAttributes } from 'react'
import { cn } from '../../utils/cn'

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger' | 'soft'
type ButtonSize = 'sm' | 'md' | 'lg' | 'icon'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant
  size?: ButtonSize
}

const variants: Record<ButtonVariant, string> = {
  primary:
    'border-cyan-400/40 bg-cyan-400 text-slate-950 shadow-[0_12px_32px_rgba(34,211,238,0.22)] hover:bg-cyan-300',
  secondary:
    'border-white/10 bg-white/8 text-slate-100 hover:bg-white/12 light:border-slate-200 light:bg-white light:text-slate-900 light:hover:bg-slate-50',
  ghost:
    'border-transparent bg-transparent text-slate-300 hover:bg-white/8 hover:text-white light:text-slate-600 light:hover:bg-slate-100 light:hover:text-slate-950',
  danger: 'border-red-400/40 bg-red-500 text-white hover:bg-red-400',
  soft:
    'border-violet-400/20 bg-violet-400/12 text-violet-100 hover:bg-violet-400/18 light:bg-violet-50 light:text-violet-800',
}

const sizes: Record<ButtonSize, string> = {
  sm: 'min-h-9 rounded-lg px-3 text-xs',
  md: 'min-h-10 rounded-xl px-4 text-sm',
  lg: 'min-h-12 rounded-2xl px-5 text-sm',
  icon: 'h-10 w-10 rounded-xl p-0',
}

export function Button({ className, variant = 'primary', size = 'md', ...props }: ButtonProps) {
  return (
    <button
      {...props}
      className={cn(
        'focus-ring inline-flex items-center justify-center gap-2 border font-semibold transition duration-200 disabled:pointer-events-none disabled:opacity-45',
        variants[variant],
        sizes[size],
        className,
      )}
    />
  )
}
