import { motion } from 'framer-motion'

interface JobProgressProps {
  value: number
}

export function JobProgress({ value }: JobProgressProps) {
  return (
    <div className="h-3 overflow-hidden rounded-full bg-white/10 light:bg-slate-200">
      <motion.div
        className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400"
        initial={{ width: 0 }}
        animate={{ width: `${Math.min(100, Math.max(0, value))}%` }}
        transition={{ duration: 0.35 }}
      />
    </div>
  )
}
