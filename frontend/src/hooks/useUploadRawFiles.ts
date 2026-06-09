import { useCallback, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { uploadRawFile, type UploadContext } from '../api/uploads'
import type { SourceImage } from '../api/types'
import { useAppStore } from '../store/appStore'
import { isRawFile } from '../utils/file'

export type UploadStatus = 'pending' | 'uploading' | 'uploaded' | 'failed'

export interface UploadFileItem {
  id: string
  file: File
  status: UploadStatus
  progress: number
  error?: string
  sourceImage?: SourceImage
}

export function useUploadRawFiles() {
  const { t } = useTranslation()
  const [items, setItems] = useState<UploadFileItem[]>([])
  const addSourceImage = useAppStore((state) => state.addSourceImage)

  const addFiles = useCallback((files: File[]) => {
    setItems((current) => {
      const existing = new Set(current.map((item) => `${item.file.name}-${item.file.size}`))
      const next = files
        .filter((file) => isRawFile(file))
        .filter((file) => !existing.has(`${file.name}-${file.size}`))
        .map((file) => ({
          id: crypto.randomUUID(),
          file,
          status: 'pending' as UploadStatus,
          progress: 0,
        }))
      return [...current, ...next]
    })
  }, [])

  const removeFile = useCallback((id: string) => {
    setItems((current) => current.filter((item) => item.id !== id))
  }, [])

  const reset = useCallback(() => setItems([]), [])

  const updateItem = useCallback((id: string, patch: Partial<UploadFileItem>) => {
    setItems((current) => current.map((item) => (item.id === id ? { ...item, ...patch } : item)))
  }, [])

  const uploadOne = useCallback(
    async (item: UploadFileItem, context: UploadContext) => {
      updateItem(item.id, { status: 'uploading', error: undefined, progress: Math.max(item.progress, 1) })
      try {
        const sourceImage = await uploadRawFile({
          file: item.file,
          context,
          sourceImageId: item.id,
          onProgress: (progress) => updateItem(item.id, { progress }),
        })
        addSourceImage(sourceImage)
        updateItem(item.id, { status: 'uploaded', progress: 100, sourceImage })
        return sourceImage
      } catch (error) {
        const message = error instanceof Error ? error.message : t('upload.uploadFailed')
        updateItem(item.id, { status: 'failed', error: message })
        throw error
      }
    },
    [addSourceImage, t, updateItem],
  )

  const uploadAll = useCallback(
    async (context: UploadContext) => {
      const pending = items.filter((item) => item.status === 'pending' || item.status === 'failed')
      const uploaded: SourceImage[] = []
      for (const item of pending) {
        uploaded.push(await uploadOne(item, context))
      }
      return uploaded
    },
    [items, uploadOne],
  )

  const allUploaded = useMemo(() => items.length > 0 && items.every((item) => item.status === 'uploaded'), [items])
  const isUploading = useMemo(() => items.some((item) => item.status === 'uploading'), [items])

  return {
    items,
    addFiles,
    removeFile,
    reset,
    uploadAll,
    uploadOne,
    allUploaded,
    isUploading,
  }
}
