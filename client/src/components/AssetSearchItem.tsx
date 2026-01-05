import type { Asset } from '../types/asset'

interface AssetSearchItemProps {
  asset: Asset
  isSelected: boolean
  onClick: () => void
  onMouseEnter: () => void
}

export function AssetSearchItem({
  asset,
  isSelected,
  onClick,
  onMouseEnter,
}: AssetSearchItemProps) {
  const displayName = asset.name_kr || asset.name_en
  const subText = [asset.name_en, asset.ticker, asset.exchange]
    .filter(Boolean)
    .join(' · ')

  return (
    <div
      className={`
        cursor-pointer px-4 py-3 transition-colors
        ${isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'}
      `}
      onClick={onClick}
      onMouseEnter={onMouseEnter}
    >
      <div className="text-sm font-medium text-gray-900">{displayName}</div>
      <div className="mt-1 text-xs text-gray-500">{subText}</div>
    </div>
  )
}
