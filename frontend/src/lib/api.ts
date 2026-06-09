import { getArtifactAccess } from '../api/artifacts'
import { createJob, getJob, listJobResults, listJobSteps } from '../api/jobs'
import { uploadRawFile, type UploadContext } from '../api/uploads'
import type { CreateJobPayload } from '../api/types'

export async function uploadFiles(files: File[], context: UploadContext) {
  return Promise.all(
    files.map((file) =>
      uploadRawFile({
        file,
        context,
        sourceImageId: crypto.randomUUID(),
      }),
    ),
  )
}

export function startReconstruction(payload: CreateJobPayload) {
  return createJob(payload)
}

export function getJobStatus(jobId: string) {
  return getJob(jobId)
}

export function getJobLogs(jobId: string) {
  return listJobSteps(jobId)
}

export function getResult(jobId: string) {
  return listJobResults(jobId)
}

export async function downloadResult(jobId: string) {
  const artifacts = await listJobResults(jobId)
  const final = artifacts.find((artifact) => artifact.artifact_type === 'final_jpg') ?? artifacts[0]
  if (!final) throw new Error('errors.noResultArtifact')
  return getArtifactAccess(final.id)
}
