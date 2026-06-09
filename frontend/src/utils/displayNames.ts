import type { TFunction } from 'i18next'

export function artifactDisplayName(t: TFunction, artifactType: string): string {
  return t(`artifacts.types.${artifactType}`, { defaultValue: humanizeIdentifier(artifactType) })
}

export function candidateDisplayName(t: TFunction, candidateName: string): string {
  return t(`results.candidates.${candidateName}`, { defaultValue: humanizeIdentifier(candidateName) })
}

function humanizeIdentifier(value: string): string {
  return value
    .replace(/^candidate_/, '')
    .split('_')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}
