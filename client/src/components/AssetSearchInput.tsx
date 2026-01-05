import { useState, useRef, useEffect } from 'react'
import { useAssetSearch } from '../hooks/useAssetSearch'
import { AssetSearchDropdown } from './AssetSearchDropdown'
import type { Asset } from '../types/asset'

interface AssetSearchInputProps {
  placeholder?: string
  onSelect: (asset: Asset) => void
  className?: string
}

export function AssetSearchInput({
  placeholder = '자산 검색...',
  onSelect,
  className = '',
}: AssetSearchInputProps) {
  const [inputValue, setInputValue] = useState('')
  const [selectedIndex, setSelectedIndex] = useState(-1)
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)

  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const { results, isLoading, error, search, clearResults } = useAssetSearch()

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        containerRef.current &&
        !containerRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    setIsDropdownOpen(
      results.length > 0 || isLoading || error !== null
    )
  }, [results, isLoading, error])

  useEffect(() => {
    setSelectedIndex(-1)
  }, [results])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value
    setInputValue(value)
    search(value)
  }

  const handleSelect = (asset: Asset) => {
    setInputValue(asset.name_kr || asset.name_en)
    setIsDropdownOpen(false)
    clearResults()
    onSelect(asset)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isDropdownOpen || results.length === 0) {
      return
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setSelectedIndex((prev) =>
          prev < results.length - 1 ? prev + 1 : prev
        )
        break

      case 'ArrowUp':
        e.preventDefault()
        setSelectedIndex((prev) => (prev > 0 ? prev - 1 : -1))
        break

      case 'Enter':
        e.preventDefault()
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleSelect(results[selectedIndex])
        }
        break

      case 'Escape':
        e.preventDefault()
        setIsDropdownOpen(false)
        inputRef.current?.blur()
        break
    }
  }

  const handleFocus = () => {
    if (results.length > 0 || isLoading || error !== null) {
      setIsDropdownOpen(true)
    }
  }

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onFocus={handleFocus}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-300 px-4 py-2 text-base focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
        autoComplete="off"
      />

      {isDropdownOpen && (
        <AssetSearchDropdown
          results={results}
          isLoading={isLoading}
          error={error}
          selectedIndex={selectedIndex}
          onSelect={handleSelect}
          onHover={setSelectedIndex}
        />
      )}
    </div>
  )
}
