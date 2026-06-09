import axios from 'axios'
import { env } from '../config/env'
import { apiClient, postData } from './client'
import { registerSourceImage } from './imageSets'
import { mockDelay } from './mock'
import type { SourceImage, UploadPresignRequest, UploadPresignResponse } from './types'

export interface UploadContext {
  userId: string
  projectId: string
  imageSetId: string
}

export interface UploadRawFileOptions {
  file: File
  context: UploadContext
  sourceImageId: string
  onProgress?: (progress: number) => void
}

export async function presignUpload(payload: UploadPresignRequest): Promise<UploadPresignResponse> {
  return postData<UploadPresignResponse, UploadPresignRequest>('/uploads/presign', payload)
}

export async function uploadRawFile(options: UploadRawFileOptions): Promise<SourceImage> {
  if (env.enableMockApi) {
    options.onProgress?.(100)
    return mockDelay(
      registerSourceImage(options.context.imageSetId, {
        image_set_id: options.context.imageSetId,
        storage_key: `mock/${options.context.imageSetId}/${options.file.name}`,
        original_filename: options.file.name,
        mime_type: options.file.type || 'application/octet-stream',
        file_size: options.file.size,
      }),
    )
  }

  if (env.uploadMode === 'presigned') return uploadPresigned(options)
  return uploadDirect(options)
}

async function uploadDirect(options: UploadRawFileOptions): Promise<SourceImage> {
  const form = new FormData()
  form.append('file', options.file)
  const response = await apiClient.post<UploadPresignResponse>('/uploads/direct', form, {
    params: {
      user_id: options.context.userId,
      project_id: options.context.projectId,
      image_set_id: options.context.imageSetId,
      source_image_id: options.sourceImageId,
    },
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    onUploadProgress: (event) => {
      if (!event.total) return
      options.onProgress?.(Math.round((event.loaded / event.total) * 100))
    },
  })

  return registerUploadedSource(options, response.data.storage_key)
}

async function uploadPresigned(options: UploadRawFileOptions): Promise<SourceImage> {
  const contentType = options.file.type || 'application/octet-stream'
  const presign = await presignUpload({
    user_id: options.context.userId,
    project_id: options.context.projectId,
    image_set_id: options.context.imageSetId,
    source_image_id: options.sourceImageId,
    filename: options.file.name,
    content_type: contentType,
    file_size: options.file.size,
    purpose: 'source_raw',
  })

  if (presign.upload_url.startsWith('local://')) {
    throw new Error('errors.presignedLocalUploadUnsupported')
  }

  await axios.put(presign.upload_url, options.file, {
    headers: presign.headers ?? { 'Content-Type': contentType },
    onUploadProgress: (event) => {
      if (!event.total) return
      options.onProgress?.(Math.round((event.loaded / event.total) * 100))
    },
  })

  return registerUploadedSource(options, presign.storage_key)
}

function registerUploadedSource(options: UploadRawFileOptions, storageKey: string): Promise<SourceImage> {
  return registerSourceImage(options.context.imageSetId, {
    image_set_id: options.context.imageSetId,
    storage_key: storageKey,
    original_filename: options.file.name,
    mime_type: options.file.type || 'application/octet-stream',
    file_size: options.file.size,
  })
}
