import type { SignalType } from '../types/stock'

/**
 * 신호 타입에 따른 색상 반환
 */
export const getSignalColor = (signal: SignalType): string => {
  const colorMap: Record<SignalType, string> = {
    '매수': '#10b981',
    '중립': '#f59e0b',
    '주의': '#ef4444',
  }
  return colorMap[signal] || '#3b82f6'
}

/**
 * 가격 변동률 계산
 */
export const calculatePriceChange = (
  current: number,
  previous: number
): { value: number; percentage: number } => {
  const value = current - previous
  const percentage = previous !== 0 ? (value / previous) * 100 : 0
  return { value, percentage }
}

