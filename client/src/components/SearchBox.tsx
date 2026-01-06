import React, { useState, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Clock } from 'lucide-react'
import { useStockStore } from '../store/useStockStore'
import { useRecentSearchesStore } from '../store/useRecentSearchesStore'
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
  const { recentSearches, addRecentSearch, removeRecentSearch } = useRecentSearchesStore()
  const [searchResults, setSearchResults] = useState<Asset[]>([])
  const [showAutocomplete, setShowAutocomplete] = useState(false)
  const [selectedAsset, setSelectedAsset] = useState<Asset | null>(null)
  const [displayValue, setDisplayValue] = useState(ticker)
  const [isFocused, setIsFocused] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)
  const debounceTimerRef = useRef<number | null>(null)
  const searchBoxRef = useRef<HTMLDivElement>(null)

  // Show recent searches when: focused AND (no input OR no search results)
  const showRecentSearches = isFocused && !displayValue.trim() && recentSearches.length > 0

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

    // Add to recent searches
    addRecentSearch(asset)

    // CRITICAL: Always use ticker for analysis requests
    // The ticker is the universal identifier for all stocks (KR, US, ETF, etc.)
    // Display shows name_kr/name_en for UX, but backend always receives ticker
    const searchQuery = asset.ticker

    // Notify parent with ticker (for internal use)
    onTickerChange(asset.ticker)

    // Close autocomplete and recent searches
    setShowAutocomplete(false)
    setSearchResults([])
    setIsFocused(false)

    // Trigger analysis immediately with ticker
    // Pass ticker directly to avoid React state update delay
    setTimeout(() => {
      onSearch(searchQuery)
    }, 100)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !loading) {
      // If autocomplete is showing and has results, select the first one
      if (showAutocomplete && searchResults.length > 0) {
        e.preventDefault() // Prevent form submission
        handleSelectAsset(searchResults[0])
      } else {
        // Otherwise, perform search with current input
        setShowAutocomplete(false)
        onSearch()
      }
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

  const handleFocus = () => {
    setIsFocused(true)
  }

  const handleBlur = () => {
    // Close autocomplete when clicking outside
    // Use setTimeout to allow click events on autocomplete items to fire first
    setTimeout(() => {
      setShowAutocomplete(false)
      setIsFocused(false)
    }, 200)
  }

  /**
   * 최근 검색 종목 클릭 핸들러
   */
  const handleRecentSearchClick = (recentAsset: typeof recentSearches[0]) => {
    // Convert RecentAsset to Asset format
    const asset: Asset = {
      id: 0, // Not used for search
      ticker: recentAsset.ticker,
      name_kr: recentAsset.name_kr,
      name_en: recentAsset.name_en,
      asset_type: recentAsset.asset_type,
      exchange: recentAsset.exchange,
      country: recentAsset.exchange.includes('KS') || recentAsset.exchange.includes('KQ') ? 'KR' : 'US',
      currency: recentAsset.exchange.includes('KS') || recentAsset.exchange.includes('KQ') ? 'KRW' : 'USD',
      search_keywords: null,
    }

    handleSelectAsset(asset)
  }

  /**
   * 최근 검색 종목 삭제 핸들러
   */
  const handleRemoveRecentSearch = (e: React.MouseEvent, ticker: string) => {
    e.stopPropagation() // Prevent triggering the click event on parent
    removeRecentSearch(ticker)
  }

  // Close autocomplete and recent searches when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchBoxRef.current && !searchBoxRef.current.contains(event.target as Node)) {
        setShowAutocomplete(false)
        setIsFocused(false)
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
          onKeyDown={handleKeyDown}
          onFocus={handleFocus}
          onBlur={handleBlur}
          disabled={loading}
        />
        <button onClick={() => onSearch()} disabled={loading}>
          {loading ? '분석 중...' : '분석하기'}
        </button>
      </div>

      {/* Recent Searches - 검색창 바로 아래에 표시 */}
      <AnimatePresence>
        {showRecentSearches && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            style={{
              overflow: 'hidden',
              marginTop: '8px',
            }}
          >
            <div
              style={{
                backgroundColor: 'white',
                borderRadius: '12px',
                padding: '12px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
              }}
            >
              {/* Header */}
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  marginBottom: '8px',
                  paddingLeft: '4px',
                }}
              >
                <Clock size={14} style={{ color: '#6b7280' }} />
                <span
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    color: '#6b7280',
                  }}
                >
                  최근 검색
                </span>
              </div>

              {/* Chips - 가로 스크롤 */}
              <div
                style={{
                  display: 'flex',
                  gap: '8px',
                  overflowX: 'auto',
                  overflowY: 'hidden',
                  paddingBottom: '4px',
                  // Hide scrollbar for cleaner look
                  scrollbarWidth: 'none',
                  msOverflowStyle: 'none',
                }}
                className="recent-searches-scroll"
              >
                <AnimatePresence mode="popLayout">
                  {recentSearches.map((recentAsset) => (
                    <motion.div
                      key={recentAsset.ticker}
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      transition={{ duration: 0.2 }}
                      onClick={() => handleRecentSearchClick(recentAsset)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '8px 12px',
                        backgroundColor: '#f3f4f6',
                        borderRadius: '20px',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                        flexShrink: 0,
                        transition: 'all 0.2s ease',
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.backgroundColor = '#e5e7eb'
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.backgroundColor = '#f3f4f6'
                      }}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                        <span
                          style={{
                            fontSize: '13px',
                            fontWeight: 600,
                            color: '#111827',
                          }}
                        >
                          {recentAsset.name_kr || recentAsset.name_en}
                        </span>
                        <span
                          style={{
                            fontSize: '11px',
                            color: '#6b7280',
                          }}
                        >
                          {recentAsset.ticker}
                        </span>
                      </div>
                      <button
                        onClick={(e) => handleRemoveRecentSearch(e, recentAsset.ticker)}
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          width: '18px',
                          height: '18px',
                          borderRadius: '50%',
                          backgroundColor: 'transparent',
                          border: 'none',
                          cursor: 'pointer',
                          padding: 0,
                          marginLeft: '2px',
                          transition: 'background-color 0.2s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.backgroundColor = '#d1d5db'
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.backgroundColor = 'transparent'
                        }}
                        aria-label={`${recentAsset.name_kr || recentAsset.name_en} 삭제`}
                      >
                        <X size={12} style={{ color: '#6b7280' }} />
                      </button>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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

