import axios, { AxiosError } from 'axios'
import { env } from '../config/env'

export interface ApiErrorShape {
  message: string
  status?: number
  detail?: unknown
}

export class ApiError extends Error {
  status?: number
  detail?: unknown

  constructor(shape: ApiErrorShape) {
    super(shape.message)
    this.name = 'ApiError'
    this.status = shape.status
    this.detail = shape.detail
  }
}

export const apiClient = axios.create({
  baseURL: env.apiBaseUrl,
  timeout: 120_000,
})

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    const detail = error.response?.data
    const message =
      typeof detail === 'object' && detail !== null && 'detail' in detail
        ? String((detail as { detail: unknown }).detail)
        : error.message || 'errors.apiRequestFailed'

    return Promise.reject(
      new ApiError({
        message,
        status: error.response?.status,
        detail,
      }),
    )
  },
)

export async function getData<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  const response = await apiClient.get<T>(url, { params })
  return response.data
}

export async function postData<TResponse, TPayload = unknown>(
  url: string,
  payload?: TPayload,
  params?: Record<string, unknown>,
): Promise<TResponse> {
  const response = await apiClient.post<TResponse>(url, payload, { params })
  return response.data
}
