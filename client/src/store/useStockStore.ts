import { create } from 'zustand'
import type { StockInfo, AIAnalysis } from '../types/stock'

interface StockStore {
  // State
  hasSearched: boolean
  loadingMessage: string
  stockData: StockInfo | null
  aiAnalysis: AIAnalysis | null
  isLoading: boolean
  error: string | null
  ticker: string
  resolvedTicker: string | null // 변환된 티커 (검색에 사용된 실제 티커)
  originalQuery: string | null // 사용자가 입력한 원본 검색어

  // Actions
  setSearchStatus: (status: boolean) => void
  updateLoadingMessage: (message: string) => void
  setStockData: (data: StockInfo | null) => void
  setAiAnalysis: (analysis: AIAnalysis | null) => void
  setIsLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  setTicker: (ticker: string) => void
  setResolvedTicker: (ticker: string | null) => void
  setOriginalQuery: (query: string | null) => void
  reset: () => void
}

/**
 * Zustand 전역 스토어
 * 주식 분석 관련 상태를 중앙에서 관리합니다.
 */
export const useStockStore = create<StockStore>((set) => ({
  // Initial State
  hasSearched: false,
  loadingMessage: '',
  stockData: null,
  aiAnalysis: null,
  isLoading: false,
  error: null,
  ticker: '',
  resolvedTicker: null,
  originalQuery: null,

  // Actions
  setSearchStatus: (status: boolean) => set({ hasSearched: status }),
  updateLoadingMessage: (message: string) => set({ loadingMessage: message }),
  setStockData: (data: StockInfo | null) => set({ stockData: data }),
  setAiAnalysis: (analysis: AIAnalysis | null) => set({ aiAnalysis: analysis }),
  setIsLoading: (loading: boolean) => set({ isLoading: loading }),
  setError: (error: string | null) => set({ error }),
  setTicker: (ticker: string) => set({ ticker }),
  setResolvedTicker: (ticker: string | null) => set({ resolvedTicker: ticker }),
  setOriginalQuery: (query: string | null) => set({ originalQuery: query }),
  reset: () =>
    set({
      hasSearched: false,
      loadingMessage: '',
      stockData: null,
      aiAnalysis: null,
      isLoading: false,
      error: null,
      ticker: '',
      resolvedTicker: null,
      originalQuery: null,
    }),
}))

