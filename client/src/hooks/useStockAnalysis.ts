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

    // 진행 단계 초기화
    const { initializeProgress, updateProgressStep } = useStockStore.getState()
    initializeProgress()

    try {
      // 1단계: 티커 변환
      updateProgressStep('ticker_conversion', 'in_progress', '종목 정보를 확인하는 중입니다')
      await new Promise(resolve => setTimeout(resolve, 300)) // UI 피드백을 위한 최소 지연
      updateProgressStep('ticker_conversion', 'completed', '종목 확인 완료')

      // 2단계: 데이터 조회
      updateProgressStep('data_fetching', 'in_progress', '주가 및 재무 데이터를 수집하는 중입니다')

      // 3단계: AI 분석 (API 호출 전에 미리 시작 상태로 표시)
      // 백엔드에서 데이터 조회 후 바로 AI 분석이 시작되므로

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

      // 데이터 조회 완료
      updateProgressStep('data_fetching', 'completed', '데이터 수집 완료')

      // AI 분석 진행 중으로 표시
      updateProgressStep('ai_analysis', 'in_progress', '투자 리포트를 작성하는 중입니다')
      await new Promise(resolve => setTimeout(resolve, 500)) // AI 분석 시뮬레이션
      updateProgressStep('ai_analysis', 'completed', 'AI 분석 완료')

      // 최종 완료
      updateProgressStep('completed', 'completed', '모든 분석이 완료되었습니다')

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

      // 에러 발생 시 현재 단계를 에러 상태로 업데이트
      const { progressSteps } = useStockStore.getState()
      const currentStep = progressSteps.find(step => step.status === 'in_progress')
      if (currentStep) {
        updateProgressStep(currentStep.id as any, 'error', errorMessage)
      }
    } finally {
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

