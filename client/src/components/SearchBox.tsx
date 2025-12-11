import React from 'react'
import { useStockStore } from '../store/useStockStore'
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

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !loading) {
      onSearch()
    }
  }

  return (
    <div className="search-section max-w-2xl mx-auto w-full">
      <div className="search-box">
        <input
          type="text"
          placeholder="티커 또는 종목명을 입력하세요 (예: NVDA, 엔비디아, 삼성전자)"
          value={ticker}
          onChange={(e) => onTickerChange(e.target.value)}
          onKeyPress={handleKeyPress}
          disabled={loading}
        />
        <button onClick={onSearch} disabled={loading}>
          {loading ? '분석 중...' : '분석하기'}
        </button>
      </div>
      {loading && loadingMessage && (
        <div className="loading-status animate-pulse">
          {loadingMessage}
        </div>
      )}
    </div>
  )
}

