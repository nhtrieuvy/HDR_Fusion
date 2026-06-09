export type JsonValue =
  | string
  | number
  | boolean
  | null
  | JsonValue[]
  | { [key: string]: JsonValue }

export type ProjectStatus = 'active' | 'archived' | string

export interface Project {
  id: string
  user_id: string | null
  name: string
  description: string | null
  status: ProjectStatus
  created_at: string
}

export interface CreateProjectPayload {
  name: string
  description?: string | null
  user_id?: string | null
}

export interface ImageSet {
  id: string
  project_id: string
  name: string | null
  capture_group: string | null
  status: string
  created_at: string
}

export interface CreateImageSetPayload {
  project_id: string
  name?: string | null
  capture_group?: string | null
}

export interface SourceImage {
  id: string
  image_set_id: string
  storage_key: string
  original_filename: string
  mime_type: string | null
  file_size: number | null
  raw_format: string | null
  camera_make: string | null
  camera_model: string | null
  lens_model: string | null
  width: number | null
  height: number | null
  iso: number | null
  aperture: number | null
  exposure_time: number | null
  exposure_bias: number | null
  focal_length: number | null
  black_level: JsonValue | null
  white_level: number | null
  cfa_pattern: JsonValue | null
  camera_wb: JsonValue | null
  measured_luminance: number | null
  exposure_order: number | null
  relative_exposure_ratio: number | null
  is_reference: boolean
  audit_status: string
  audit_warnings: JsonValue | null
  created_at: string
}

export interface RegisterSourceImagePayload {
  image_set_id: string
  storage_key: string
  original_filename: string
  mime_type?: string | null
  file_size?: number | null
  metadata?: Record<string, JsonValue> | null
}

export type JobStatus =
  | 'queued'
  | 'running'
  | 'failed'
  | 'completed'
  | 'qc_failed'
  | 'manual_review'
  | 'cancelled'
  | string

export type StepStatus = 'pending' | 'running' | 'failed' | 'completed' | 'skipped' | string

export type PresetName =
  | 'real_estate_natural'
  | 'conservative_hdr'
  | 'window_control'
  | 'bright_interior'
  | 'artifact_safe'
  | string

export type ProcessingMode = 'fast_preview' | 'quality' | 'ultra'

export interface Job {
  id: string
  image_set_id: string
  status: JobStatus
  progress: number
  pipeline_name: string
  pipeline_version: string
  preset_name: PresetName
  preset_version: string
  params: JsonValue | null
  config_snapshot: JsonValue | null
  output_artifact_id: string | null
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export interface CreateJobPayload {
  image_set_id: string
  pipeline_name?: string
  preset_name: PresetName
  mode?: ProcessingMode
  params?: Record<string, JsonValue> | null
}

export interface JobStep {
  id: string
  job_id: string
  step_name: string
  status: StepStatus
  progress: number
  metrics: JsonValue | null
  warnings: JsonValue | null
  artifacts: JsonValue | null
  started_at: string | null
  completed_at: string | null
  error_message: string | null
}

export type ArtifactType = string

export interface Artifact {
  id: string
  job_id: string | null
  image_set_id: string | null
  source_image_id: string | null
  artifact_type: ArtifactType
  storage_key: string
  mime_type: string | null
  width: number | null
  height: number | null
  file_size: number | null
  metadata_json: JsonValue | null
  created_at: string
}

export interface ArtifactAccess {
  artifact: Artifact
  url: string
  method: 'GET' | string
}

export interface UploadPresignRequest {
  user_id: string
  project_id: string
  image_set_id: string
  source_image_id: string
  filename: string
  content_type?: string | null
  file_size?: number
  purpose?: 'source_raw'
}

export interface UploadPresignResponse {
  upload_url: string
  storage_key: string
  method: 'PUT' | 'POST' | 'LOCAL' | string
  headers?: Record<string, string>
  asset_id?: string
}

export interface QCMetrics {
  final_highlight_clipping?: number
  unrecoverable_source_clipping?: number
  technical_clipping_after_processing?: number
  halo_score?: number
  ghosting_alignment_residual?: number
  blur_sharpness?: number
  shadow_noise?: number
  color_cast?: number
  magenta_green_artifact_risk?: number
  mask_leak_risk?: number
  window_exterior_detail_confidence?: number
  overall_naturalness_score?: number
  [key: string]: JsonValue | undefined
}

export interface QCReport {
  status?: 'pass' | 'warning' | 'qc_failed' | 'manual_review' | string
  selected_candidate?: string
  recommended_action?: string
  warnings?: string[]
  metrics?: QCMetrics
  [key: string]: JsonValue | QCMetrics | string[] | undefined
}

export type JobResultsResponse = Artifact[]
