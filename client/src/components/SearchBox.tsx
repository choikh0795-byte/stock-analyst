import React, { useState, useEffect, useRef } from 'react'
import { useStockStore } from '../store/useStockStore'
import { stockApi } from '../api/stockApi'
import type { Asset } from '../types/asset'
import './SearchBox.css'

interface SearchBoxProps {
  ticker: string
  onTickerChange: (ticker: string) => void
  onSearch: (ticker?: string) => void
  loading: boolean
}

/**
 * 검색어와 일치하는 텍스트 부분을 하이라이트 처리
 */
const highlightMatch = (text: string, query: string): React.ReactNode => {
  if (!query.trim() || !text) return text

  // Escape special regex characters
  const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

  try {
    const regex = new RegExp(`(${escapedQuery})`, 'gi')
    const parts = text.split(regex)

    return parts.map((part, index) => {
      if (part.toLowerCase() === query.toLowerCase()) {
        return (
          <mark
            key={index}
            style={{
              backgroundColor: '#fef08a',
              fontWeight: 600,
              padding: '0 2px',
              borderRadius: '2px',
            }}
          >
            {part}
          </mark>
        )
      }
      return <span key={index}>{part}</span>
    })
  } catch (error) {
    // If regex fails, return original text
    return text
  }
}

/**
 * 주식 티커 검색 입력 컴포넌트
 */
export const SearchBox: React.FC<SearchBoxProps> = ({
  ticker,
  onTickerChange,
  onSearch,
  loading,
}) => {
  const loadingMessage = useStockStore((state) => state.loadingMessage)
  const [searchResults, setSearchResults] = useState<Asset[]>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null)
  const [displayValue, setDisplayValue] = useState(ticker)
  const abortControllerRef = useRef<AbortController | null>(null)
  const debounceTimerRef = useRef<number | null>(null)
  const searchBoxRef = useRef<HTMLDivElement>(null)

  // Sync displayValue with ticker prop (for external updates)
  // BUT: Don't override displayValue if user has selected an asset from autocomplete
  useEffect(() => {
    // Only sync if no asset is selected (i.e., user is manually typing)
    if (!selectedAsset) {
      setDisplayValue(ticker)
    }
  }, [ticker, selectedAsset])

  // Debounced search effect - use displayValue for autocomplete
  useEffect(() => {
    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Clear results if input is empty
    if (!displayValue.trim()) {
      setSearchResults([])
      setShowAutocomplete(false)
      return
    }

    // Don't show autocomplete if an asset is already selected
    if (selectedAsset) {
      return
    }

    // Set new debounce timer (300ms)
    debounceTimerRef.current = window.setTimeout(() => {
      handleSearch(displayValue)
    }, 300)

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [displayValue, selectedAsset])

  const handleSearch = async (query: string) => {
    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // Create new abort controller
    abortControllerRef.current = new AbortController()

    try {
      const response = await stockApi.searchAssets(
        query,
        10,
        abortControllerRef.current.signal
      )

      // Debug log to verify response structure
      console.log('[SearchBox] API response:', {
        response,
        hasResults: response?.results !== undefined,
        resultsType: Array.isArray(response?.results) ? 'array' : typeof response?.results,
        resultsLength: response?.results?.length
      })

      // Defensive check: ensure results is an array
      const results = Array.isArray(response?.results) ? response.results : []

      setSearchResults(results)
      setShowAutocomplete(results.length > 0)
    } catch (error) {
      // Only log non-cancellation errors
      if (error instanceof Error && error.message !== 'Request cancelled') {
        console.error('Autocomplete search error:', error)
      }
      // Reset to empty array on error
      setSearchResults([])
      setShowAutocomplete(false)
    }
  }

  const handleSelectAsset = (asset: Asset) => {
    // Set display value to asset name (Korean preferred)
    const displayName = asset.name_kr || asset.name_en
    setDisplayValue(displayName)

    // Store selected asset
    setSelectedAsset(asset)

    // Determine if this is a Korean stock
    const isKoreanStock = asset.country === 'KR' || asset.name_kr !== null

    // For Korean stocks, use name_kr for analysis; otherwise use ticker
    const searchQuery = isKoreanStock && asset.name_kr ? asset.name_kr : asset.ticker

    // Notify parent with ticker (for internal use)
    onTickerChange(asset.ticker)

    // Close autocomplete
    setShowAutocomplete(false)
    setSearchResults([])

    // Trigger analysis immediately with the selected query (name_kr for Korean stocks, ticker for others)
    // Pass query directly to avoid React state update delay
    setTimeout(() => {
      onSearch(searchQuery)
    }, 100)
  }

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !loading) {
      setShowAutocomplete(false)
      onSearch()
    }
    if (e.key === 'Escape') {
      setShowAutocomplete(false)
    }
  }

  const handleInputChange = (value: string) => {
    // Update display value
    setDisplayValue(value)

    // Clear selected asset when user manually types
    setSelectedAsset(null)

    // Notify parent
    onTickerChange(value)

    // Show autocomplete if there's input
    if (value.trim()) {
      setShowAutocomplete(true)
    } else {
      setShowAutocomplete(false)
    }
  }

  const handleBlur = () => {
    // Close autocomplete when clicking outside
    // Use setTimeout to allow click events on autocomplete items to fire first
    setTimeout(() => {
      setShowAutocomplete(false)
    }, 200)
  }

  // Close autocomplete when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchBoxRef.current && !searchBoxRef.current.contains(event.target as Node)) {
        setShowAutocomplete(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => {
      document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [])

  return (
    <div className="search-section max-w-2xl mx-auto w-full" ref={searchBoxRef}>
      <div className="search-box">
        <input
          type="text"
          placeholder="티커 또는 종목명을 입력하세요 (예: NVDA, 엔비디아, 삼성전자)"
          value={displayValue}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyPress={handleKeyPress}
          onBlur={handleBlur}
          disabled={loading}
        />
        <button onClick={() => onSearch()} disabled={loading}>
          {loading ? '분석 중...' : '분석하기'}
        </button>
      </div>

      {/* Autocomplete results */}
      {showAutocomplete && searchResults.length > 0 && (
        <div
          style={{
            position: 'absolute',
            backgroundColor: 'white',
            border: '1px solid #e5e7eb',
            borderRadius: '8px',
            marginTop: '4px',
            width: '100%',
            maxWidth: '600px',
            maxHeight: '300px',
            overflowY: 'auto',
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
            zIndex: 50,
          }}
        >
          {searchResults.map((asset) => (
            <div
              key={asset.id}
              onClick={() => handleSelectAsset(asset)}
              style={{
                padding: '12px 16px',
                cursor: 'pointer',
                borderBottom: '1px solid #f3f4f6',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f9fafb'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'white'
              }}
            >
              <div style={{ fontWeight: 600, fontSize: '14px', color: '#111827' }}>
                {highlightMatch(asset.name_kr || asset.name_en, displayValue)}
              </div>
              <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '2px' }}>
                {asset.ticker} · {asset.exchange} · {asset.asset_type}
              </div>
            </div>
          ))}
        </div>
      )}

      {loading && loadingMessage && (
        <div className="loading-status animate-pulse">
          {loadingMessage}
        </div>
      )}
    </div>
  )
}

