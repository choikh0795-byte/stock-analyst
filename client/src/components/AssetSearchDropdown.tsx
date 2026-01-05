import { AssetSearchItem } from './AssetSearchItem'
import type { Asset } from '../types/asset'

interface AssetSearchDropdownProps {
  results: Asset[]
  isLoading: boolean
  error: string | null
  selectedIndex: number
  onSelect: (asset: Asset) => void
  onHover: (index: number) => void
}

export function AssetSearchDropdown({
  results,
  isLoading,
  error,
  selectedIndex,
  onSelect,
  onHover,
}: AssetSearchDropdownProps) {
  if (error) {
    return (
      <div className="absolute z-50 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg">
        <div className="px-4 py-3 text-sm text-red-600">{error}</div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="absolute z-50 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg">
        <div className="px-4 py-3 text-sm text-gray-500">검색 중...</div>
      </div>
    )
  }

  if (results.length === 0) {
    return null
  }

  return (
    <div className="absolute z-50 mt-1 w-full rounded-lg border border-gray-200 bg-white shadow-lg">
      <div className="max-h-80 overflow-y-auto">
        {results.map((asset, index) => (
          <AssetSearchItem
            key={asset.id}
            asset={asset}
            isSelected={index === selectedIndex}
            onClick={() => onSelect(asset)}
            onMouseEnter={() => onHover(index)}
          />
        ))}
      </div>
    </div>
  )
}
