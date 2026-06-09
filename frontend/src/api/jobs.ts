import { env } from '../config/env'
import { getData, postData } from './client'
import { mockDelay, mockId, mockNow, readMockState, writeMockState } from './mock'
import type { CreateJobPayload, Job, JobResultsResponse, JobStep, PresetName, ProcessingMode } from './types'

export interface RetryJobPayload {
  strategy: 'same_params' | 'conservative_fallback'
  preset_name?: PresetName
}

export interface ReenhanceJobPayload {
  image_set_id: string
  preset_name: PresetName
  mode: ProcessingMode
  params?: Record<string, unknown>
}

export async function createJob(payload: CreateJobPayload): Promise<Job> {
  if (env.enableMockApi) {
    const state = readMockState()
    const now = mockNow()
    const job: Job = {
      id: mockId('job'),
      image_set_id: payload.image_set_id,
      status: 'completed',
      progress: 100,
      pipeline_name: 'raw_hdr_fusion',
      pipeline_version: 'mock',
      preset_name: payload.preset_name,
      preset_version: 'mock',
      params: payload.params ?? null,
      config_snapshot: null,
      output_artifact_id: null,
      error_message: null,
      created_at: now,
      started_at: now,
      completed_at: now,
    }
    state.jobs.unshift(job)
    state.steps[job.id] = mockSteps(job.id)
    state.artifacts[job.id] = []
    writeMockState(state)
    return mockDelay(job)
  }
  return postData<Job, CreateJobPayload>('/jobs', payload)
}

export async function listJobs(limit = 100): Promise<Job[]> {
  if (env.enableMockApi) {
    return mockDelay(readMockState().jobs.slice(0, limit))
  }
  return getData<Job[]>('/jobs', { limit })
}

export async function getJob(jobId: string): Promise<Job> {
  if (env.enableMockApi) {
    const job = readMockState().jobs.find((item) => item.id === jobId)
  if (!job) throw new Error('errors.jobNotFound')
    return mockDelay(job)
  }
  return getData<Job>(`/jobs/${jobId}`)
}

export async function listJobSteps(jobId: string): Promise<JobStep[]> {
  if (env.enableMockApi) return mockDelay(readMockState().steps[jobId] ?? [])
  return getData<JobStep[]>(`/jobs/${jobId}/steps`)
}

export async function listJobResults(jobId: string): Promise<JobResultsResponse> {
  if (env.enableMockApi) return mockDelay(readMockState().artifacts[jobId] ?? [])
  return getData<JobResultsResponse>(`/jobs/${jobId}/results`)
}

export async function retryJob(jobId: string, payload: RetryJobPayload): Promise<Job> {
  if (env.enableMockApi) {
    const state = readMockState()
    const job = state.jobs.find((item) => item.id === jobId)
  if (!job) throw new Error('errors.jobNotFound')
    job.status = 'completed'
    job.progress = 100
    job.error_message = null
    writeMockState(state)
    return mockDelay(job)
  }
  return postData<Job, RetryJobPayload>(`/jobs/${jobId}/retry`, payload)
}

export async function reenhanceJob(jobId: string, payload: ReenhanceJobPayload): Promise<Job> {
  const backendPayload: CreateJobPayload = {
    image_set_id: payload.image_set_id,
    preset_name: payload.preset_name,
    mode: payload.mode,
    params: {
      save_debug_outputs: true,
      ...(payload.params ?? {}),
      mode: payload.mode,
      source_job_id: jobId,
    },
  }

  if (env.enableMockApi) return createJob(backendPayload)
  return postData<Job, CreateJobPayload>(`/jobs/${jobId}/reenhance`, backendPayload)
}

function mockSteps(jobId: string): JobStep[] {
  return [
    'input_audit',
    'raw_decode_and_black_white_normalization',
    'reference_and_exposure_order',
    'alignment_proxy_ecc_audit',
    'typed_source_truth_masks',
    'raw_domain_weighted_merge',
    'valid_exposure_source_compositor',
    'radiance_safety_before_amaze',
    'candidate_finishing_and_tonemap',
    'rule_based_qc',
    'export_final_outputs',
  ].map((stepName, index) => ({
    id: `${jobId}-step-${index}`,
    job_id: jobId,
    step_name: stepName,
    status: 'completed',
    progress: 100,
    metrics: { mock: true },
    warnings: [],
    artifacts: null,
    started_at: mockNow(),
    completed_at: mockNow(),
    error_message: null,
  }))
}
