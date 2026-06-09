import { useMutation, useQueryClient } from '@tanstack/react-query'
import { createJob } from '../api/jobs'
import { useAppStore } from '../store/appStore'

export function useCreateHDRJob() {
  const queryClient = useQueryClient()
  const upsertJob = useAppStore((state) => state.upsertJob)

  return useMutation({
    mutationFn: createJob,
    onSuccess: (job) => {
      upsertJob(job)
      queryClient.invalidateQueries({ queryKey: ['job', job.id] })
      queryClient.invalidateQueries({ queryKey: ['job-results', job.id] })
    },
  })
}
