import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle2, Layers3, Rocket } from 'lucide-react'
import { useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import type { ImageSet, PresetName, ProcessingMode } from '../api/types'
import { createImageSet } from '../api/imageSets'
import { createProject, listProjects } from '../api/projects'
import { Button } from '../components/common/Button'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { PageHeader } from '../components/common/PageHeader'
import { RawDropzone } from '../components/upload/RawDropzone'
import { UploadFileList } from '../components/upload/UploadFileList'
import { env } from '../config/env'
import { useCreateHDRJob } from '../hooks/useCreateHDRJob'
import { useUploadRawFiles, type UploadFileItem } from '../hooks/useUploadRawFiles'
import { presetNames, processingModes } from '../lib/constants'
import { useAppStore } from '../store/appStore'
import { formatBytes } from '../utils/file'
import { validateRawFiles } from '../utils/validation'

export function UploadPage() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const queryClient = useQueryClient()
  const addImageSet = useAppStore((state) => state.addImageSet)
  const setCurrentJobId = useAppStore((state) => state.setCurrentJobId)
  const setSelectedFiles = useAppStore((state) => state.setSelectedFiles)

  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: () => listProjects() })
  const createProjectMutation = useMutation({ mutationFn: createProject })
  const createImageSetMutation = useMutation({ mutationFn: createImageSet })
  const createJobMutation = useCreateHDRJob()
  const upload = useUploadRawFiles()

  const [selectedProjectId, setSelectedProjectId] = useState(searchParams.get('projectId') ?? '')
  const [newProjectName, setNewProjectName] = useState('')
  const [imageSetName, setImageSetName] = useState(`scene-${new Date().toISOString().slice(0, 10)}`)
  const [createdImageSet, setCreatedImageSet] = useState<ImageSet | null>(null)
  const [preset, setPreset] = useState<PresetName>('real_estate_natural')
  const [mode, setMode] = useState<ProcessingMode>('quality')
  const [flowError, setFlowError] = useState<string | null>(null)

  const files = upload.items.map((item) => item.file)
  const validation = useMemo(() => validateRawFiles(files, t), [files, t])
  const totalSize = useMemo(() => files.reduce((sum, file) => sum + file.size, 0), [files])
  const canPrepareUpload = validation.valid && !upload.isUploading && Boolean(selectedProjectId || newProjectName.trim())
  const canCreateJob = upload.allUploaded && createdImageSet && !createJobMutation.isPending

  function addFiles(filesToAdd: File[]) {
    upload.addFiles(filesToAdd)
    setSelectedFiles(filesToAdd.map((file) => file.name))
  }

  async function prepareAndUpload() {
    setFlowError(null)
    try {
      let projectId = selectedProjectId
      if (!projectId) {
        const project = await createProjectMutation.mutateAsync({
          name: newProjectName.trim(),
          description: null,
          user_id: 'local',
        })
        projectId = project.id
        setSelectedProjectId(project.id)
        queryClient.invalidateQueries({ queryKey: ['projects'] })
      }

      const imageSet = await createImageSetMutation.mutateAsync({
        project_id: projectId,
        name: imageSetName.trim() || null,
      })
      setCreatedImageSet(imageSet)
      addImageSet(imageSet)
      await upload.uploadAll({ userId: 'local', projectId, imageSetId: imageSet.id })
    } catch (error) {
      setFlowError(error instanceof Error ? error.message : t('upload.uploadFailed'))
    }
  }

  async function submitJob() {
    if (!createdImageSet) return
    setFlowError(null)
    try {
      const job = await createJobMutation.mutateAsync({
        image_set_id: createdImageSet.id,
        pipeline_name: 'raw_hdr_fusion',
        preset_name: preset,
        mode,
        params: {
          save_debug_outputs: env.enableDebugArtifacts,
          candidate_generation: true,
          allow_generative_edit: false,
          mode,
        },
      })
      setCurrentJobId(job.id)
      navigate(`/jobs/${job.id}`)
    } catch (error) {
      setFlowError(error instanceof Error ? error.message : t('upload.createJobFailed'))
    }
  }

  function retryUpload(item: UploadFileItem) {
    if (!createdImageSet || !selectedProjectId) return
    upload.uploadOne(item, { userId: 'local', projectId: selectedProjectId, imageSetId: createdImageSet.id }).catch((error) => {
      setFlowError(error instanceof Error ? error.message : t('upload.retryUploadFailed'))
    })
  }

  return (
    <div className="space-y-6">
      <PageHeader title={t('upload.title')} description={t('upload.description')} eyebrow={t('upload.rawStack')} />

      {flowError ? <ErrorState title={t('upload.flowFailed')} message={flowError} /> : null}

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_390px]">
        <div className="space-y-5">
          <RawDropzone disabled={upload.isUploading || upload.allUploaded} onFiles={addFiles} />
          <div className="flex flex-wrap gap-2 text-xs">
            <span className="rounded-full border border-white/10 bg-white/7 px-3 py-1.5 text-slate-300">{t('upload.fileCount', { count: files.length })}</span>
            <span className="rounded-full border border-white/10 bg-white/7 px-3 py-1.5 text-slate-300">{formatBytes(totalSize)}</span>
            {validation.valid ? (
              <span className="inline-flex items-center gap-1 rounded-full border border-emerald-300/20 bg-emerald-400/10 px-3 py-1.5 text-emerald-200">
                <CheckCircle2 className="h-3.5 w-3.5" />
                {t('upload.validCount')}
              </span>
            ) : null}
          </div>

          {validation.errors.length ? (
            <div className="rounded-2xl border border-red-300/25 bg-red-400/10 p-4 text-sm text-red-200">
              {validation.errors.map((error) => (
                <div key={error}>{error}</div>
              ))}
            </div>
          ) : null}
          {validation.warnings.length ? (
            <div className="rounded-2xl border border-amber-300/25 bg-amber-400/10 p-4 text-sm text-amber-100">
              {validation.warnings.map((warning) => (
                <div key={warning} className="flex gap-2">
                  <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
                  {warning}
                </div>
              ))}
            </div>
          ) : null}

          <UploadFileList disabled={upload.isUploading} items={upload.items} onRemove={upload.removeFile} onRetry={retryUpload} />
        </div>

        <aside className="surface-card h-fit rounded-[2rem] p-5">
          <div className="mb-5 flex items-center gap-2">
            <Layers3 className="h-4 w-4 text-cyan-300" />
            <h2 className="text-sm font-semibold text-white light:text-slate-950">{t('common.preset')} / {t('common.mode')}</h2>
          </div>

          {projectsQuery.isLoading ? <LoadingState label={t('common.loading')} /> : null}
          <div className="space-y-4">
            <Field label={t('upload.project')}>
              <select className="field" value={selectedProjectId} onChange={(event) => setSelectedProjectId(event.target.value)}>
                <option value="">{t('upload.createProject')}</option>
                {projectsQuery.data?.map((project) => (
                  <option key={project.id} value={project.id}>
                    {project.name}
                  </option>
                ))}
              </select>
            </Field>
            {!selectedProjectId ? (
              <Field label={t('upload.newProjectName')}>
                <input className="field" value={newProjectName} onChange={(event) => setNewProjectName(event.target.value)} />
              </Field>
            ) : null}
            <Field label={t('upload.imageSetName')}>
              <input className="field" value={imageSetName} onChange={(event) => setImageSetName(event.target.value)} />
            </Field>
            <Field label={t('common.preset')}>
              <select className="field" value={preset} onChange={(event) => setPreset(event.target.value as PresetName)}>
                {presetNames.map((item) => (
                  <option key={item} value={item}>
                    {t(`preset.names.${item}`)}
                  </option>
                ))}
              </select>
              <p className="mt-2 text-xs leading-5 text-slate-400">{t(`preset.${preset}`)}</p>
            </Field>
            <div className="space-y-2">
              {processingModes.map((item) => (
                <label key={item} className={`block rounded-2xl border p-4 transition ${mode === item ? 'border-cyan-300/40 bg-cyan-300/10' : 'border-white/10 bg-white/[0.03] light:border-slate-200 light:bg-white/70'}`}>
                  <span className="flex items-start gap-3">
                    <input checked={mode === item} className="mt-1 accent-cyan-300" name="mode" type="radio" value={item} onChange={() => setMode(item)} />
                    <span>
                      <span className="block text-sm font-semibold text-white light:text-slate-950">{t(`mode.${item}`)}</span>
                      <span className="mt-1 block text-xs leading-5 text-slate-400 light:text-slate-600">{t(`mode.${item}_desc`)}</span>
                    </span>
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div className="mt-6 grid gap-3">
            <Button disabled={!canPrepareUpload} type="button" variant="secondary" onClick={prepareAndUpload}>
              {t('upload.createAndUpload')}
            </Button>
            <Button disabled={!canCreateJob} type="button" variant="primary" onClick={submitJob}>
              <Rocket className="h-4 w-4" />
              {t('upload.startJob')}
            </Button>
            <p className="text-xs leading-5 text-slate-500">{t('upload.locked')}</p>
          </div>
        </aside>
      </section>
    </div>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{label}</span>
      <div className="mt-2">{children}</div>
    </label>
  )
}
