import React from 'react'
import { useStockAnalysis } from '../hooks/useStockAnalysis'
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

