/**
 * 주식 관련 TypeScript 타입 정의
 */

export interface StockInfo {
  name: string
  symbol: string
  current_price: number
  previous_close: number
  market_cap: string | null
  pe_ratio?: number | null
  pb_ratio?: number | null
  return_on_equity?: number | null
  sector: string
  summary: string
  // 6가지 핵심 지표
  fifty_two_week_low?: number | null
  fifty_two_week_high?: number | null
  target_mean_price?: number | null
  number_of_analyst_opinions?: number | null
  peg_ratio?: number | null
  beta?: number | null
  dividend_yield?: number | null
  // 지표별 AI 인사이트
  metric_insights?: {
    pe_ratio?: string
    pb_ratio?: string
    return_on_equity?: string
    dividend_yield?: string
    beta?: string
    target_mean_price?: string
  } | null
}

export interface AIAnalysis {
  score: number
  signal: '매수' | '중립' | '주의'
  one_line: string
  summary: string[]
  risk: string
  metric_insights?: {
    pe_ratio?: string
    pb_ratio?: string
    return_on_equity?: string
    dividend_yield?: string
    beta?: string
    target_mean_price?: string
  } | null
}

export interface StockAnalysisRequest {
  ticker: string
}

export interface StockAnalysisResponse {
  stock_data: StockInfo
  news: string[]
  ai_analysis: AIAnalysis | null
}

export type SignalType = '매수' | '중립' | '주의'

