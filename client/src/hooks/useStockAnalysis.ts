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
    setOriginalQuery,
    setResolvedTicker,
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

    const originalQuery = ticker.trim()
    setOriginalQuery(originalQuery)
    setResolvedTicker(null)

    // 동적 로딩 메시지 시퀀스
    const loadingMessages = [
      '종목 검색 중...',
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
      // 성능 최적화: 백엔드가 자동으로 티커 변환을 처리하므로
      // search API를 별도로 호출하지 않고 바로 analyze API 호출
      updateLoadingMessage('데이터 수집 중...')

      // 분석 요청 (백엔드에서 티커 변환 자동 처리)
      const response = await stockApi.getStockAnalysis({ ticker: originalQuery })

      console.info('[useStockAnalysis] setStockData payload', {
        symbol: response.stock_data?.symbol,
        roe: response.stock_data?.roe,
        roe_str: response.stock_data?.roe_str,
        return_on_equity: response.stock_data?.return_on_equity,
        eps: response.stock_data?.eps,
        eps_str: response.stock_data?.eps_str,
        beta: response.stock_data?.beta,
      })

      setStockData(response.stock_data)
      setAiAnalysis(response.ai_analysis)

      // 응답에서 실제 사용된 티커 확인 (백엔드가 변환한 경우)
      if (response.stock_data?.symbol) {
        setResolvedTicker(response.stock_data.symbol)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.'
      setError(errorMessage)
      console.error('Stock analysis error:', err)
    } finally {
      clearInterval(messageInterval)
      updateLoadingMessage('')
      setIsLoading(false)
    }
  }, [ticker, setSearchStatus, setIsLoading, setError, setStockData, setAiAnalysis, updateLoadingMessage, setOriginalQuery, setResolvedTicker])

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

