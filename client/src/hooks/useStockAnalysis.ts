import { useCallback } from 'react'
import { stockApi } from '../api/stockApi'
import { useStockStore } from '../store/useStockStore'
import type { StockInfo, AIAnalysis } from '../types/stock'

interface UseStockAnalysisReturn {
  ticker: string
  setTicker: (ticker: string) => void
  loading: boolean
  stockData: StockInfo | null
  aiAnalysis: AIAnalysis | null
  error: string | null
  analyzeStock: () => Promise<void>
  reset: () => void
}

/**
 * 주식 분석을 위한 커스텀 훅
 * API 호출 로직을 담당하며, 상태는 Zustand 스토어에서 관리합니다.
 */
export const useStockAnalysis = (): UseStockAnalysisReturn => {
  const {
    ticker,
    setTicker,
    isLoading,
    stockData,
    aiAnalysis,
    error,
    setSearchStatus,
    setIsLoading,
    setStockData,
    setAiAnalysis,
    setError,
    updateLoadingMessage,
    reset,
  } = useStockStore()

  const analyzeStock = useCallback(async () => {
    if (!ticker.trim()) {
      setError('티커를 입력해주세요.')
      return
    }

    // 검색 시작
    setSearchStatus(true)
    setIsLoading(true)
    setError(null)
    setStockData(null)
    setAiAnalysis(null)

    // 동적 로딩 메시지 시퀀스
    const loadingMessages = [
      '데이터 수집 중...',
      '재무제표 분석 중...',
      'AI 리포트 작성 중...',
    ]

    let messageIndex = 0
    updateLoadingMessage(loadingMessages[0])

    const messageInterval = setInterval(() => {
      messageIndex = (messageIndex + 1) % loadingMessages.length
      updateLoadingMessage(loadingMessages[messageIndex])
    }, 1500)

    try {
      const response = await stockApi.getStockAnalysis({ ticker })
      setStockData(response.stock_data)
      setAiAnalysis(response.ai_analysis)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.'
      setError(errorMessage)
      console.error('Stock analysis error:', err)
    } finally {
      clearInterval(messageInterval)
      updateLoadingMessage('')
      setIsLoading(false)
    }
  }, [ticker, setSearchStatus, setIsLoading, setError, setStockData, setAiAnalysis, updateLoadingMessage])

  return {
    ticker,
    setTicker,
    loading: isLoading,
    stockData,
    aiAnalysis,
    error,
    analyzeStock,
    reset,
  }
}

