import { zodResolver } from '@hookform/resolvers/zod'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { FolderPlus } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'
import { z } from 'zod'
import { useTranslation } from 'react-i18next'
import { createProject, listProjects } from '../api/projects'
import { Button } from '../components/common/Button'
import { EmptyState } from '../components/common/EmptyState'
import { ErrorState } from '../components/common/ErrorState'
import { LoadingState } from '../components/common/LoadingState'
import { PageHeader } from '../components/common/PageHeader'
import { formatDateTime } from '../utils/format'

interface ProjectForm {
  name: string
  description?: string
}

export function ProjectsPage() {
  const { t } = useTranslation()
  const projectSchema = z.object({
    name: z.string().min(2, t('projects.projectNameRequired')),
    description: z.string().optional(),
  })
  const queryClient = useQueryClient()
  const projectsQuery = useQuery({ queryKey: ['projects'], queryFn: () => listProjects() })
  const form = useForm<ProjectForm>({
    resolver: zodResolver(projectSchema),
    defaultValues: { name: '', description: '' },
  })

  const mutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      form.reset()
      queryClient.invalidateQueries({ queryKey: ['projects'] })
    },
  })

  return (
    <div className="space-y-6">
      <PageHeader title={t('projects.title')} description={t('projects.description')} eyebrow={t('projects.workspace')} />
      <div className="grid gap-6 xl:grid-cols-[390px_1fr]">
        <section className="surface-card rounded-[2rem] p-6">
          <h2 className="text-base font-semibold text-white light:text-slate-950">{t('projects.createTitle')}</h2>
          <form className="mt-5 space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{t('projects.projectName')}</span>
              <input className="field mt-2" {...form.register('name')} />
              {form.formState.errors.name ? <span className="mt-1 block text-xs text-red-300">{form.formState.errors.name.message}</span> : null}
            </label>
            <label className="block">
              <span className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">{t('projects.descriptionLabel')}</span>
              <textarea className="field mt-2 min-h-28" {...form.register('description')} />
            </label>
            <Button disabled={mutation.isPending} type="submit">
              <FolderPlus className="h-4 w-4" />
              {t('projects.createProject')}
            </Button>
          </form>
          {mutation.isError ? <div className="mt-4"><ErrorState message={mutation.error.message} /></div> : null}
        </section>

        <section className="surface-card rounded-[2rem] p-6">
          <h2 className="text-base font-semibold text-white light:text-slate-950">{t('projects.title')}</h2>
          <div className="mt-4">
            {projectsQuery.isLoading ? <LoadingState label={t('projects.loading')} /> : null}
            {projectsQuery.isError ? <ErrorState message={projectsQuery.error.message} /> : null}
            {projectsQuery.data?.length ? (
              <div className="grid gap-3 md:grid-cols-2">
                {projectsQuery.data.map((project) => (
                  <Link key={project.id} className="rounded-3xl border border-white/10 bg-white/[0.04] p-5 transition hover:bg-white/[0.07] light:border-slate-200 light:bg-white/80" to={`/projects/${project.id}`}>
                    <div className="text-sm font-semibold text-white light:text-slate-950">{project.name}</div>
                    <div className="mt-1 text-xs text-slate-500">{formatDateTime(project.created_at)}</div>
                    {project.description ? <p className="mt-3 line-clamp-2 text-sm text-slate-400 light:text-slate-600">{project.description}</p> : null}
                  </Link>
                ))}
              </div>
            ) : !projectsQuery.isLoading ? (
              <EmptyState title={t('projects.noProjectsTitle')} description={t('projects.noProjectsDesc')} />
            ) : null}
          </div>
        </section>
      </div>
    </div>
  )
}
