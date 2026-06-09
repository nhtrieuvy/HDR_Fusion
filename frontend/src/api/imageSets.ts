import { env } from '../config/env'
import { getData, postData } from './client'
import { mockDelay, mockId, mockNow, readMockState, writeMockState } from './mock'
import type { CreateImageSetPayload, ImageSet, RegisterSourceImagePayload, SourceImage } from './types'

export async function createImageSet(payload: CreateImageSetPayload): Promise<ImageSet> {
  if (env.enableMockApi) {
    const state = readMockState()
    const imageSet: ImageSet = {
      id: mockId('image-set'),
      project_id: payload.project_id,
      name: payload.name ?? null,
      capture_group: payload.capture_group ?? null,
      status: 'created',
      created_at: mockNow(),
    }
    state.imageSets.unshift(imageSet)
    writeMockState(state)
    return mockDelay(imageSet)
  }
  return postData<ImageSet, CreateImageSetPayload>('/image-sets', payload)
}

export async function getImageSet(imageSetId: string): Promise<ImageSet> {
  if (env.enableMockApi) {
    const imageSet = readMockState().imageSets.find((item) => item.id === imageSetId)
  if (!imageSet) throw new Error('errors.imageSetNotFound')
    return mockDelay(imageSet)
  }
  return getData<ImageSet>(`/image-sets/${imageSetId}`)
}

export async function registerSourceImage(
  imageSetId: string,
  payload: RegisterSourceImagePayload,
): Promise<SourceImage> {
  if (env.enableMockApi) {
    const state = readMockState()
    const source: SourceImage = {
      id: mockId('source'),
      image_set_id: imageSetId,
      storage_key: payload.storage_key,
      original_filename: payload.original_filename,
      mime_type: payload.mime_type ?? null,
      file_size: payload.file_size ?? null,
      raw_format: payload.original_filename.split('.').pop()?.toLowerCase() ?? null,
      camera_make: null,
      camera_model: null,
      lens_model: null,
      width: null,
      height: null,
      iso: null,
      aperture: null,
      exposure_time: null,
      exposure_bias: null,
      focal_length: null,
      black_level: null,
      white_level: null,
      cfa_pattern: null,
      camera_wb: null,
      measured_luminance: null,
      exposure_order: null,
      relative_exposure_ratio: null,
      is_reference: false,
      audit_status: 'pending',
      audit_warnings: null,
      created_at: mockNow(),
    }
    state.sourceImages.unshift(source)
    writeMockState(state)
    return mockDelay(source)
  }
  return postData<SourceImage, RegisterSourceImagePayload>(`/image-sets/${imageSetId}/source-images`, payload)
}
