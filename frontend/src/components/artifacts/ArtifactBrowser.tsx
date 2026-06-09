import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Artifact } from '../../api/types'
import { artifactGroupKey, isJsonArtifact } from '../../api/artifacts'
import { EmptyState } from '../common/EmptyState'
import { ArtifactCard } from './ArtifactCard'
import { JsonArtifactViewer } from './JsonArtifactViewer'

interface ArtifactBrowserProps {
  artifacts: Artifact[]
}

export function ArtifactBrowser({ artifacts }: ArtifactBrowserProps) {
  const { t } = useTranslation()
  const [openArtifact, setOpenArtifact] = useState<Artifact | null>(null)

  if (!artifacts.length) {
    return (
      <EmptyState
        title={t('artifacts.noneTitle')}
        description={t('artifacts.noneDesc')}
      />
    )
  }

  const groups = artifacts.reduce<Record<string, Artifact[]>>((acc, artifact) => {
    const group = artifactGroupKey(artifact.artifact_type)
    acc[group] = [...(acc[group] ?? []), artifact]
    return acc
  }, {})

  return (
    <div className="space-y-6">
      {Object.entries(groups).map(([group, items]) => (
        <section key={group}>
          <h3 className="mb-3 text-sm font-semibold text-white light:text-slate-950">{t(`artifacts.groups.${group}`)}</h3>
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {items.map((artifact) => (
              <ArtifactCard key={artifact.id} artifact={artifact} onOpen={setOpenArtifact} />
            ))}
          </div>
        </section>
      ))}

      {openArtifact ? (
        <div className="fixed inset-0 z-50 bg-black/70 p-4 backdrop-blur-sm" onClick={() => setOpenArtifact(null)}>
          <div
            className="mx-auto max-h-[92vh] max-w-5xl overflow-auto rounded-3xl border border-white/10 bg-slate-950 p-4 light:bg-white"
            onClick={(event) => event.stopPropagation()}
          >
            {isJsonArtifact(openArtifact) ? (
              <JsonArtifactViewer artifact={openArtifact} />
            ) : (
              <ArtifactCard artifact={openArtifact} />
            )}
          </div>
        </div>
      ) : null}
    </div>
  )
}
