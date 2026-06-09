import { UploadCloud } from 'lucide-react'
import { motion } from 'framer-motion'
import { useDropzone } from 'react-dropzone'
import { useTranslation } from 'react-i18next'
import { RAW_EXTENSIONS } from '../../utils/file'
import { cn } from '../../utils/cn'

interface RawDropzoneProps {
  onFiles: (files: File[]) => void
  disabled?: boolean
}

export function RawDropzone({ onFiles, disabled }: RawDropzoneProps) {
  const { t } = useTranslation()
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    disabled,
    multiple: true,
    onDrop: (acceptedFiles) => onFiles(acceptedFiles),
    accept: RAW_EXTENSIONS.reduce<Record<string, string[]>>((acc, ext) => {
      acc['application/octet-stream'] = [...(acc['application/octet-stream'] ?? []), ext]
      acc['image/x-adobe-dng'] = [...(acc['image/x-adobe-dng'] ?? []), ext]
      return acc
    }, {}),
  })

  return (
    <div
      {...getRootProps()}
      className={cn(
        'focus-ring image-grid-bg grid min-h-72 place-items-center rounded-3xl border border-dashed border-white/16 bg-slate-950/45 p-8 text-center transition light:border-slate-300 light:bg-white/70',
        isDragActive && 'border-cyan-300 bg-cyan-300/10 shadow-[0_0_0_8px_rgba(34,211,238,0.08)]',
        disabled && 'opacity-60',
      )}
    >
      <input {...getInputProps()} />
      <motion.div animate={{ scale: isDragActive ? 1.01 : 1 }} transition={{ duration: 0.18 }}>
        <div className="mx-auto grid h-16 w-16 place-items-center rounded-3xl border border-cyan-300/20 bg-cyan-300/10 text-cyan-200">
          <UploadCloud className="h-8 w-8" />
        </div>
        <p className="mt-5 text-base font-semibold text-white light:text-slate-950">{t('upload.dropTitle')}</p>
        <p className="mt-2 text-sm text-slate-400 light:text-slate-600">{t('upload.dropHint')}</p>
        <p className="mt-5 inline-flex rounded-full border border-white/10 bg-white/7 px-4 py-2 text-xs font-semibold text-cyan-200 light:border-cyan-200 light:bg-cyan-50 light:text-cyan-700">
          {t('upload.browse')}
        </p>
      </motion.div>
    </div>
  )
}
