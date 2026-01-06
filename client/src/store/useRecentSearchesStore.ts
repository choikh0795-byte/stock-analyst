import { create } from 'zustand'
import type { Asset } from '../types/asset'

/**
 * 최근 검색 종목 타입
 */
export interface RecentAsset {
  ticker: string
  name_kr: string | null
  name_en: string
  asset_type: string
  exchange: string
  searchedAt: number  // timestamp for sorting
}

/**
 * localStorage 키
 */
const RECENT_SEARCHES_KEY = 'stock-analyst-recent-searches'

/**
 * 최대 저장 개수
 */
const MAX_RECENT_SEARCHES = 10

/**
 * localStorage에서 최근 검색 종목 불러오기 (안전하게)
 */
const loadRecentSearches = (): RecentAsset[] => {
  try {
    // SSR 환경 체크
    if (typeof window === 'undefined') {
      return []
    }

    const stored = localStorage.getItem(RECENT_SEARCHES_KEY)
    if (!stored) {
      return []
    }

    const parsed = JSON.parse(stored)

    // 배열인지 검증
    if (!Array.isArray(parsed)) {
      console.warn('[RecentSearches] Invalid data format in localStorage, resetting...')
      localStorage.removeItem(RECENT_SEARCHES_KEY)
      return []
    }

    // 최신순으로 정렬 (searchedAt 기준)
    return parsed.sort((a, b) => (b.searchedAt || 0) - (a.searchedAt || 0))
  } catch (error) {
    console.error('[RecentSearches] Failed to load from localStorage:', error)
    // 에러 발생 시 localStorage 초기화
    try {
      localStorage.removeItem(RECENT_SEARCHES_KEY)
    } catch (e) {
      // localStorage 접근 불가 시 무시
    }
    return []
  }
}

/**
 * localStorage에 최근 검색 종목 저장하기 (안전하게)
 */
const saveRecentSearches = (searches: RecentAsset[]): void => {
  try {
    // SSR 환경 체크
    if (typeof window === 'undefined') {
      return
    }

    localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(searches))
  } catch (error) {
    console.error('[RecentSearches] Failed to save to localStorage:', error)
    // localStorage quota 초과 등의 에러 발생 시, 오래된 항목 삭제 후 재시도
    if (searches.length > 5) {
      try {
        const trimmed = searches.slice(0, 5)
        localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(trimmed))
      } catch (retryError) {
        console.error('[RecentSearches] Retry save failed:', retryError)
      }
    }
  }
}

/**
 * 최근 검색 종목 관리 스토어
 */
interface RecentSearchesStore {
  recentSearches: RecentAsset[]
  addRecentSearch: (asset: Asset) => void
  removeRecentSearch: (ticker: string) => void
  clearRecentSearches: () => void
}

/**
 * Zustand 스토어 생성
 */
export const useRecentSearchesStore = create<RecentSearchesStore>((set) => ({
  // 초기 상태: localStorage에서 불러오기
  recentSearches: loadRecentSearches(),

  /**
   * 최근 검색 종목 추가
   * - 중복 제거 (동일 ticker는 맨 앞으로 이동)
   * - 최대 10개 유지
   * - localStorage 자동 동기화
   */
  addRecentSearch: (asset: Asset) => {
    set((state) => {
      // 새로운 RecentAsset 객체 생성
      const newSearch: RecentAsset = {
        ticker: asset.ticker,
        name_kr: asset.name_kr,
        name_en: asset.name_en,
        asset_type: asset.asset_type,
        exchange: asset.exchange,
        searchedAt: Date.now(),
      }

      // 기존 목록에서 동일 ticker 제거
      const filtered = state.recentSearches.filter(
        (item) => item.ticker !== asset.ticker
      )

      // 새 항목을 맨 앞에 추가
      const updated = [newSearch, ...filtered]

      // 최대 개수 제한
      const trimmed = updated.slice(0, MAX_RECENT_SEARCHES)

      // localStorage 저장
      saveRecentSearches(trimmed)

      return { recentSearches: trimmed }
    })
  },

  /**
   * 특정 종목 삭제
   */
  removeRecentSearch: (ticker: string) => {
    set((state) => {
      const filtered = state.recentSearches.filter(
        (item) => item.ticker !== ticker
      )

      // localStorage 저장
      saveRecentSearches(filtered)

      return { recentSearches: filtered }
    })
  },

  /**
   * 전체 삭제
   */
  clearRecentSearches: () => {
    try {
      if (typeof window !== 'undefined') {
        localStorage.removeItem(RECENT_SEARCHES_KEY)
      }
    } catch (error) {
      console.error('[RecentSearches] Failed to clear localStorage:', error)
    }

    set({ recentSearches: [] })
  },
}))
