import { useQuery } from '@tanstack/react-query'
import { Download, Eye, FileJson } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import type { Artifact } from '../../api/types'
import { downloadArtifact, getArtifactAccess, isImageArtifact, isJsonArtifact } from '../../api/artifacts'
import { artifactDisplayName } from '../../utils/displayNames'
import { formatBytes } from '../../utils/file'
import { Button } from '../common/Button'

interface ArtifactCardProps {
  artifact: Artifact
  onOpen?: (artifact: Artifact) => void
}

export function ArtifactCard({ artifact, onOpen }: ArtifactCardProps) {
  const { t } = useTranslation()
  const accessQuery = useQuery({
    queryKey: ['artifact-access', artifact.id],
    queryFn: () => getArtifactAccess(artifact.id),
    enabled: isImageArtifact(artifact),
    staleTime: 5 * 60 * 1000,
  })

  const imageUrl = accessQuery.data?.url
  const artifactName = artifactDisplayName(t, artifact.artifact_type)

  return (
    <div className="overflow-hidden rounded-3xl border border-white/10 bg-slate-950/50 light:border-slate-200 light:bg-white">
      <div className="grid aspect-video place-items-center bg-white/[0.04] light:bg-slate-100">
        {isImageArtifact(artifact) && imageUrl && !imageUrl.startsWith('local://') ? (
          <img className="h-full w-full object-contain" src={imageUrl} alt={artifactName} />
        ) : isJsonArtifact(artifact) ? (
          <FileJson className="h-10 w-10 text-slate-500" />
        ) : (
          <span className="text-xs text-slate-500">{artifact.mime_type ?? t('common.artifact')}</span>
        )}
      </div>
      <div className="space-y-3 p-3">
        <div>
          <div className="truncate text-sm font-semibold text-white light:text-slate-950">{artifactName}</div>
          <div className="mt-1 truncate text-xs text-slate-500">{artifact.storage_key}</div>
          <div className="mt-1 text-xs text-slate-500">{formatBytes(artifact.file_size)}</div>
        </div>
        <div className="flex gap-2">
          <Button className="flex-1" type="button" variant="secondary" onClick={() => onOpen?.(artifact)}>
            <Eye className="h-4 w-4" />
            {t('common.open')}
          </Button>
          {imageUrl && !imageUrl.startsWith('local://') ? (
            <Button
              aria-label={t('common.download')}
              size="icon"
              type="button"
              variant="secondary"
              onClick={() => void downloadArtifact(artifact, artifact.storage_key.split('/').pop() ?? artifact.artifact_type)}
            >
              <Download className="h-4 w-4" />
            </Button>
          ) : null}
        </div>
      </div>
    </div>
  )
}
