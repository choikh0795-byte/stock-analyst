import { create } from 'zustand'
import type { StockInfo, AIAnalysis, ProgressStep, ProgressStepId } from '../types/stock'

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
  progressSteps: ProgressStep[] // 진행 단계 배열
  currentStepIndex: number // 현재 진행 중인 단계 인덱스

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
  initializeProgress: () => void // 진행 단계 초기화
  updateProgressStep: (stepId: ProgressStepId, status: 'in_progress' | 'completed' | 'error', message?: string) => void // 진행 단계 업데이트
  reset: () => void
}

/**
 * 진행 단계 초기 상태
 */
const INITIAL_PROGRESS_STEPS: ProgressStep[] = [
  {
    id: 'ticker_conversion',
    label: '티커 변환',
    icon: 'Search',
    status: 'pending',
    message: '종목 정보를 확인하는 중입니다'
  },
  {
    id: 'data_fetching',
    label: '데이터 조회',
    icon: 'Database',
    status: 'pending',
    message: '주가 및 재무 데이터를 수집하는 중입니다'
  },
  {
    id: 'ai_analysis',
    label: 'AI 분석',
    icon: 'Bot',
    status: 'pending',
    message: '투자 리포트를 작성하는 중입니다'
  },
  {
    id: 'completed',
    label: '완료',
    icon: 'CheckCircle2',
    status: 'pending',
    message: '분석이 완료되었습니다'
  }
]

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
  progressSteps: INITIAL_PROGRESS_STEPS,
  currentStepIndex: 0,

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

  /**
   * 진행 단계 초기화
   */
  initializeProgress: () => set({
    progressSteps: INITIAL_PROGRESS_STEPS.map(step => ({ ...step })),
    currentStepIndex: 0
  }),

  /**
   * 진행 단계 업데이트
   */
  updateProgressStep: (stepId: ProgressStepId, status: 'in_progress' | 'completed' | 'error', message?: string) =>
    set((state) => {
      const stepIndex = state.progressSteps.findIndex(step => step.id === stepId)
      if (stepIndex === -1) return state

      const updatedSteps = [...state.progressSteps]
      updatedSteps[stepIndex] = {
        ...updatedSteps[stepIndex],
        status,
        ...(message && { message })
      }

      return {
        progressSteps: updatedSteps,
        currentStepIndex: status === 'completed' ? stepIndex + 1 : stepIndex
      }
    }),

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
      progressSteps: INITIAL_PROGRESS_STEPS.map(step => ({ ...step })),
      currentStepIndex: 0,
    }),
}))

