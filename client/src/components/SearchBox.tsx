import React, { useState, useEffect, useRef } from 'react'
import { useStockStore } from '../store/useStockStore'
import { stockApi } from '../api/stockApi'
import type { Asset } from '../types/asset'
import './SearchBox.css'

interface SearchBoxProps {
  ticker: string
  onTickerChange: (ticker: string) => void
  onSearch: () => void
  loading: boolean
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
  const abortControllerRef = useRef<AbortController | null>(null)
  const debounceTimerRef = useRef<number | null>(null)

  // Debounced search effect
  useEffect(() => {
    // Clear previous timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Clear results if input is empty
    if (!ticker.trim()) {
      setSearchResults([])
      setShowAutocomplete(false)
      return
    }

    // Set new debounce timer (300ms)
    debounceTimerRef.current = window.setTimeout(() => {
      handleSearch(ticker)
    }, 300)

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [ticker])

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
    onTickerChange(asset.ticker)
    setShowAutocomplete(false)
    setSearchResults([])
    // Trigger analysis after a short delay to allow state update
    setTimeout(() => {
      onSearch()
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
    onTickerChange(value)
    if (value.trim()) {
      setShowAutocomplete(true)
    }
  }

  return (
    <div className="search-section max-w-2xl mx-auto w-full">
      <div className="search-box">
        <input
          type="text"
          placeholder="티커 또는 종목명을 입력하세요 (예: NVDA, 엔비디아, 삼성전자)"
          value={ticker}
          onChange={(e) => handleInputChange(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
        />
        <button onClick={onSearch} disabled={loading}>
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
                {asset.name_kr || asset.name_en}
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

