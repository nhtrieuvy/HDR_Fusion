import { Download } from 'lucide-react'
import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { downloadArtifact, downloadArtifactAsPng } from '../../api/artifacts'
import type { Artifact } from '../../api/types'
import { artifactDisplayName } from '../../utils/displayNames'
import { Button } from '../common/Button'

interface DownloadButtonsProps {
  artifacts: Artifact[]
}

export function DownloadButtons({ artifacts }: DownloadButtonsProps) {
  const finalJpg = artifacts.find((artifact) => artifact.artifact_type === 'final_jpg')
  const finalPng = artifacts.find((artifact) => artifact.artifact_type === 'final_png')
  const finalWebp = artifacts.find((artifact) => artifact.artifact_type === 'final_webp')
  const finalTiff = artifacts.find((artifact) => artifact.artifact_type === 'final_tiff')
  const pngFallback = finalPng ?? finalJpg ?? finalWebp
  const items: DownloadItem[] = [
    { artifact: finalJpg, artifactType: 'final_jpg', filename: 'final.jpg' },
    { artifact: finalPng, artifactType: 'final_png', fallbackArtifact: pngFallback, filename: 'final.png' },
    { artifact: finalWebp, artifactType: 'final_webp', filename: 'final.webp' },
    { artifact: finalTiff, artifactType: 'final_tiff', filename: 'final.tiff' },
  ]

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <DownloadButton key={item.artifactType} item={item} />
      ))}
    </div>
  )
}

interface DownloadItem {
  artifact?: Artifact
  artifactType: 'final_jpg' | 'final_png' | 'final_webp' | 'final_tiff'
  fallbackArtifact?: Artifact
  filename: string
}

function DownloadButton({ item }: { item: DownloadItem }) {
  const { t } = useTranslation()
  const [isDownloading, setIsDownloading] = useState(false)
  const sourceArtifact = item.artifact ?? (item.artifactType === 'final_png' ? item.fallbackArtifact : undefined)
  const label = item.artifact ? artifactDisplayName(t, item.artifact.artifact_type) : t(`artifacts.types.${item.artifactType}`)

  async function handleDownload() {
    if (!sourceArtifact) return
    try {
      setIsDownloading(true)
      if (item.artifactType === 'final_png' && item.artifact?.artifact_type !== 'final_png') {
        await downloadArtifactAsPng(sourceArtifact, item.filename)
      } else {
        await downloadArtifact(sourceArtifact, item.filename)
      }
    } finally {
      setIsDownloading(false)
    }
  }

  return (
    <Button disabled={!sourceArtifact || isDownloading} type="button" variant="secondary" onClick={handleDownload}>
      <Download className="h-4 w-4" />
      {label}
    </Button>
  )
}
