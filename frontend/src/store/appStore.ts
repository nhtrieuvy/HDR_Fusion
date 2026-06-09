import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { ImageSet, Job, SourceImage } from '../api/types'

export interface ProcessingSettings {
  exposureStrength: number
  deglareStrength: number
  toneMappingIntensity: number
  enableAmaze: boolean
  enableSourceTruth: boolean
  enableCompositor: boolean
  enableDeglare: boolean
  outputFormat: 'jpg' | 'png' | 'tiff'
  quality: 'draft' | 'balanced' | 'high'
}

interface AppState {
  recentJobs: Job[]
  imageSets: ImageSet[]
  sourceImages: SourceImage[]
  selectedFiles: string[]
  currentJobId: string | null
  previewImages: {
    beforeUrl?: string
    afterUrl?: string
  }
  processingSettings: ProcessingSettings
  addImageSet: (imageSet: ImageSet) => void
  addSourceImage: (sourceImage: SourceImage) => void
  upsertJob: (job: Job) => void
  setRecentJobs: (jobs: Job[]) => void
  removeJob: (jobId: string) => void
  setCurrentJobId: (jobId: string | null) => void
  setSelectedFiles: (files: string[]) => void
  setPreviewImages: (images: AppState['previewImages']) => void
  updateProcessingSettings: (settings: Partial<ProcessingSettings>) => void
  resetProcessingSettings: () => void
  clearLocalCache: () => void
}

const defaultProcessingSettings: ProcessingSettings = {
  exposureStrength: 62,
  deglareStrength: 48,
  toneMappingIntensity: 58,
  enableAmaze: true,
  enableSourceTruth: true,
  enableCompositor: true,
  enableDeglare: true,
  outputFormat: 'jpg',
  quality: 'balanced',
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      recentJobs: [],
      imageSets: [],
      sourceImages: [],
      selectedFiles: [],
      currentJobId: null,
      previewImages: {},
      processingSettings: defaultProcessingSettings,
      addImageSet: (imageSet) =>
        set((state) => ({
          imageSets: [imageSet, ...state.imageSets.filter((item) => item.id !== imageSet.id)].slice(0, 100),
        })),
      addSourceImage: (sourceImage) =>
        set((state) => ({
          sourceImages: [
            sourceImage,
            ...state.sourceImages.filter((item) => item.id !== sourceImage.id),
          ].slice(0, 500),
        })),
      upsertJob: (job) =>
        set((state) => ({
          recentJobs: [job, ...state.recentJobs.filter((item) => item.id !== job.id)].slice(0, 100),
          currentJobId: state.currentJobId ?? job.id,
        })),
      setRecentJobs: (jobs) =>
        set((state) => ({
          recentJobs: jobs.slice(0, 100),
          currentJobId: jobs.some((job) => job.id === state.currentJobId) ? state.currentJobId : null,
        })),
      removeJob: (jobId) =>
        set((state) => ({
          recentJobs: state.recentJobs.filter((job) => job.id !== jobId),
          currentJobId: state.currentJobId === jobId ? null : state.currentJobId,
        })),
      setCurrentJobId: (jobId) => set({ currentJobId: jobId }),
      setSelectedFiles: (files) => set({ selectedFiles: files }),
      setPreviewImages: (images) => set({ previewImages: images }),
      updateProcessingSettings: (settings) =>
        set((state) => ({ processingSettings: { ...state.processingSettings, ...settings } })),
      resetProcessingSettings: () => set({ processingSettings: defaultProcessingSettings }),
      clearLocalCache: () => set({ recentJobs: [], imageSets: [], sourceImages: [], selectedFiles: [], currentJobId: null, previewImages: {} }),
    }),
    {
      name: 'hdr-fusion-frontend-cache',
      partialize: (state) => ({
        recentJobs: state.recentJobs,
        imageSets: state.imageSets,
        sourceImages: state.sourceImages,
        selectedFiles: state.selectedFiles,
        currentJobId: state.currentJobId,
        previewImages: state.previewImages,
        processingSettings: state.processingSettings,
      }),
    },
  ),
)
