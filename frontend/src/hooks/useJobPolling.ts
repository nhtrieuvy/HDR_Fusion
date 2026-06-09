import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { getJob, listJobResults, listJobSteps } from '../api/jobs'
import { env } from '../config/env'
import { useAppStore } from '../store/appStore'
import { isTerminalJobStatus } from '../utils/status'

export function useJobPolling(jobId: string | undefined) {
  const upsertJob = useAppStore((state) => state.upsertJob)
  const removeJob = useAppStore((state) => state.removeJob)

  const jobQuery = useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJob(jobId!),
    enabled: Boolean(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status && isTerminalJobStatus(status) ? false : env.pollIntervalMs
    },
  })

  useEffect(() => {
    if (jobQuery.data) upsertJob(jobQuery.data)
  }, [jobQuery.data, upsertJob])

  useEffect(() => {
    if (jobId && jobQuery.isError) {
      removeJob(jobId)
    }
  }, [jobId, jobQuery.isError, removeJob])

  const isRunning = Boolean(jobQuery.data && !isTerminalJobStatus(jobQuery.data.status))

  const stepsQuery = useQuery({
    queryKey: ['job-steps', jobId],
    queryFn: () => listJobSteps(jobId!),
    enabled: Boolean(jobId),
    refetchInterval: isRunning ? env.pollIntervalMs : false,
  })

  const resultsQuery = useQuery({
    queryKey: ['job-results', jobId],
    queryFn: () => listJobResults(jobId!),
    enabled: Boolean(jobId) && Boolean(jobQuery.data && isTerminalJobStatus(jobQuery.data.status)),
  })

  return { jobQuery, stepsQuery, resultsQuery, isRunning }
}
