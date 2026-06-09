import { useQuery } from '@tanstack/react-query'
import { Copy } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { fetchJsonArtifact } from '../../api/artifacts'
import type { Artifact } from '../../api/types'
import { artifactDisplayName } from '../../utils/displayNames'
import { Button } from '../common/Button'
import { ErrorState } from '../common/ErrorState'
import { LoadingState } from '../common/LoadingState'

interface JsonArtifactViewerProps {
  artifact: Artifact
}

export function JsonArtifactViewer({ artifact }: JsonArtifactViewerProps) {
  const { t } = useTranslation()
  const [copied, setCopied] = useState(false)
  const query = useQuery({
    queryKey: ['artifact-json', artifact.id],
    queryFn: () => fetchJsonArtifact(artifact),
    enabled: Boolean(artifact),
  })

  if (query.isLoading) return <LoadingState label={t('artifacts.jsonLoading')} />
  if (query.isError) return <ErrorState message={query.error.message} title={t('artifacts.jsonCannotLoad')} />

  const json = JSON.stringify(query.data ?? {}, null, 2)
  const artifactName = artifactDisplayName(t, artifact.artifact_type)

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold text-white light:text-slate-950">{artifactName}</div>
          <div className="text-xs text-slate-500">{artifact.storage_key}</div>
        </div>
        <Button
          type="button"
          variant="secondary"
          onClick={async () => {
            await navigator.clipboard.writeText(json)
            setCopied(true)
            window.setTimeout(() => setCopied(false), 1600)
          }}
        >
          <Copy className="h-4 w-4" />
          {copied ? t('common.copied') : t('common.copy')}
        </Button>
      </div>
      <pre className="max-h-[70vh] overflow-auto rounded-lg bg-neutral-950 p-4 text-xs text-neutral-100">{json}</pre>
    </div>
  )
}
