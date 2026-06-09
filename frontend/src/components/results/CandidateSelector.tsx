import { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import type { Artifact } from '../../api/types'
import { candidateDisplayName } from '../../utils/displayNames'
import { ArtifactCard } from '../artifacts/ArtifactCard'

interface CandidateSelectorProps {
  artifacts: Artifact[]
  selectedCandidate?: string
}

export function CandidateSelector({ artifacts, selectedCandidate }: CandidateSelectorProps) {
  const { t } = useTranslation()
  const candidates = useMemo(
    () => artifacts.filter((artifact) => artifact.artifact_type.startsWith('candidate_')),
    [artifacts],
  )
  const [activeId, setActiveId] = useState<string | null>(null)

  if (!candidates.length) return null

  const active = candidates.find((artifact) => artifact.id === activeId) ?? candidates[0]

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {candidates.map((artifact) => {
          const name = artifact.artifact_type.replace('candidate_', '')
          const selected = selectedCandidate === name || active.id === artifact.id
          return (
            <button
              key={artifact.id}
              className={`focus-ring rounded-full border px-3 py-1.5 text-xs font-semibold ${
                selected ? 'border-cyan-300/40 bg-cyan-300/15 text-cyan-100' : 'border-white/10 bg-white/7 text-slate-300 light:border-slate-200 light:bg-white light:text-slate-700'
              }`}
              type="button"
              onClick={() => setActiveId(artifact.id)}
            >
              {candidateDisplayName(t, name)}
            </button>
          )
        })}
      </div>
      <ArtifactCard artifact={active} />
    </div>
  )
}
