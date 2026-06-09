import type { Artifact, ImageSet, Job, JobStep, Project, SourceImage } from './types'

interface MockState {
  projects: Project[]
  imageSets: ImageSet[]
  sourceImages: SourceImage[]
  jobs: Job[]
  steps: Record<string, JobStep[]>
  artifacts: Record<string, Artifact[]>
}

const STORAGE_KEY = 'hdr-fusion-frontend-mock'

function defaultState(): MockState {
  return {
    projects: [],
    imageSets: [],
    sourceImages: [],
    jobs: [],
    steps: {},
    artifacts: {},
  }
}

export function readMockState(): MockState {
  const raw = window.localStorage.getItem(STORAGE_KEY)
  if (!raw) return defaultState()
  try {
    return JSON.parse(raw) as MockState
  } catch {
    return defaultState()
  }
}

export function writeMockState(state: MockState): void {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

export function mockId(prefix: string): string {
  return `${prefix}-${crypto.randomUUID()}`
}

export function mockNow(): string {
  return new Date().toISOString()
}

export async function mockDelay<T>(value: T): Promise<T> {
  await new Promise((resolve) => window.setTimeout(resolve, 250))
  return value
}
