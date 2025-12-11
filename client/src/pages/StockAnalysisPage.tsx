import React, { useEffect, useState } from 'react'
import { useStockAnalysis } from '../hooks/useStockAnalysis'
import { useStockStore } from '../store/useStockStore'
import {
  Header,
  SearchBox,
  StockCard,
  ErrorMessage,
  Loading,
} from '../components'
import './StockAnalysisPage.css'

/**
 * 주식 분석 메인 페이지
 */
export const StockAnalysisPage: React.FC = () => {
  const {
    ticker,
    setTicker,
    loading,
    stockData,
    aiAnalysis,
    error,
    analyzeStock,
  } = useStockAnalysis()

  const resolvedTicker = useStockStore((state) => state.resolvedTicker)
  const originalQuery = useStockStore((state) => state.originalQuery)
  const [showTickerInfo, setShowTickerInfo] = useState(false)

  // 변환된 티커가 있고 원본과 다르면 정보 표시
  useEffect(() => {
    if (
      stockData &&
      resolvedTicker &&
      originalQuery &&
      resolvedTicker.toUpperCase() !== originalQuery.toUpperCase() &&
      !loading
    ) {
      setShowTickerInfo(true)
      // 5초 후 자동으로 숨김
      const timer = setTimeout(() => {
        setShowTickerInfo(false)
      }, 5000)
      return () => clearTimeout(timer)
    } else {
      setShowTickerInfo(false)
    }
  }, [stockData, resolvedTicker, originalQuery, loading])

  return (
    <div className="w-full px-3 sm:px-4">
      <div className="w-full max-w-2xl mx-auto">
        <Header />

        <SearchBox
          ticker={ticker}
          onTickerChange={setTicker}
          onSearch={analyzeStock}
          loading={loading}
        />

        {showTickerInfo && resolvedTicker && originalQuery && (
          <div className="mt-3 px-4 py-2 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg text-sm text-blue-800 dark:text-blue-200 transition-opacity duration-300">
            <span className="font-medium">
              "{originalQuery}" 검색 결과: <strong>{resolvedTicker}</strong> (
              {stockData?.name || resolvedTicker})에 대한 분석 결과입니다.
            </span>
          </div>
        )}

        {error && <ErrorMessage message={error} />}

        {loading && <Loading ticker={ticker} />}

        {stockData && (
          <div className="results mt-5">
            <StockCard data={stockData} aiAnalysis={aiAnalysis} />
          </div>
        )}
      </div>
    </div>
  )
}

