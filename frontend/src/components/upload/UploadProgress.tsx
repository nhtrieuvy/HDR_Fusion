interface UploadProgressProps {
  value: number
}

export function UploadProgress({ value }: UploadProgressProps) {
  return (
    <div className="h-2 overflow-hidden rounded-full bg-white/10 light:bg-slate-200">
      <div
        className="h-full rounded-full bg-gradient-to-r from-cyan-300 to-violet-400 transition-all"
        style={{ width: `${Math.min(100, value)}%` }}
      />
    </div>
  )
}
