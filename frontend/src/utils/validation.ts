import { fileExtension, isRawFile, totalFileSize } from './file'

export interface RawFileValidation {
  valid: boolean
  errors: string[]
  warnings: string[]
}

type Translate = (key: string, values?: Record<string, unknown>) => string

const fallbackTranslate: Translate = (key, values) => {
  if (values?.files) return `${key}: ${String(values.files)}`
  return key
}

export function validateRawFiles(files: File[], translate: Translate = fallbackTranslate): RawFileValidation {
  const errors: string[] = []
  const warnings: string[] = []
  const rawFiles = files.filter(isRawFile)
  const invalidFiles = files.filter((file) => !isRawFile(file))

  if (files.length < 3) errors.push(translate('upload.validation.minFiles'))
  if (files.length > 7) errors.push(translate('upload.validation.maxFiles'))
  if (invalidFiles.length > 0) {
    errors.push(translate('upload.validation.unsupportedType', { files: invalidFiles.map((file) => file.name).join(', ') }))
  }
  if (rawFiles.length !== files.length) errors.push(translate('upload.validation.rawOnly'))

  const extensions = new Set(files.map((file) => fileExtension(file.name)))
  if (extensions.size > 1) warnings.push(translate('upload.validation.mixedExtensions'))

  if (totalFileSize(files) > 2_000_000_000) {
    warnings.push(translate('upload.validation.largeUpload'))
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  }
}
