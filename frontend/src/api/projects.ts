import { env } from '../config/env'
import { getData, postData } from './client'
import { mockDelay, mockId, mockNow, readMockState, writeMockState } from './mock'
import type { CreateProjectPayload, Project } from './types'

export async function listProjects(userId?: string): Promise<Project[]> {
  if (env.enableMockApi) {
    const state = readMockState()
    return mockDelay(userId ? state.projects.filter((project) => project.user_id === userId) : state.projects)
  }
  return getData<Project[]>('/projects', userId ? { user_id: userId } : undefined)
}

export async function createProject(payload: CreateProjectPayload): Promise<Project> {
  if (env.enableMockApi) {
    const state = readMockState()
    const project: Project = {
      id: mockId('project'),
      user_id: payload.user_id ?? 'local',
      name: payload.name,
      description: payload.description ?? null,
      status: 'active',
      created_at: mockNow(),
    }
    state.projects.unshift(project)
    writeMockState(state)
    return mockDelay(project)
  }
  return postData<Project, CreateProjectPayload>('/projects', payload)
}
