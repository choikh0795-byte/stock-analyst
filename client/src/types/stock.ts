/**
 * 주식 관련 TypeScript 타입 정의
 */

export interface StockInfo {
  name: string
  symbol: string
  current_price: number
  previous_close: number
  // 백엔드에서 포맷팅된 가격 문자열 (완성된 문자열)
  current_price_str?: string
  previous_close_str?: string
  fifty_two_week_low_str?: string | null
  fifty_two_week_high_str?: string | null
  target_mean_price_str?: string | null
  market_cap: string | null
  market_cap_str?: string
  // 포맷팅된 지표 문자열
  pe_ratio_str?: string | null
  pb_ratio_str?: string | null
  beta_str?: string | null
  // 가격 변동 관련 (계산 및 포맷팅)
  change_value?: number | null
  change_value_str?: string | null
  change_percentage?: number | null
  change_percentage_str?: string | null
  change_status?: 'RISING' | 'FALLING' | 'NEUTRAL' | null
  // 목표가 괴리율
  target_upside?: number | null
  target_upside_str?: string | null
  currency?: string
  pe_ratio?: number | null
  pb_ratio?: number | null
  // 백엔드 계산된 ROE/EPS/부채비율 (신규)
  roe?: number | null
  roe_str?: string | null
  eps?: number | null
  eps_str?: string | null
  debt_ratio?: number | null
  debt_ratio_str?: string | null
  // 구버전 호환 필드 (yfinance 원본)
  return_on_equity?: number | null
  sector: string
  industry?: string | null
  summary: string
  // 6가지 핵심 지표 (원본 숫자 값 - 계산용)
  fifty_two_week_low?: number | null
  fifty_two_week_high?: number | null
  target_mean_price?: number | null
  number_of_analyst_opinions?: number | null
  peg_ratio?: number | null
  beta?: number | null
  // 지표별 AI 인사이트 (6개 독립 지표)
  metric_insights?: {
    per: string             // PER 지표 분석
    pbr: string             // PBR 지표 분석
    roe: string             // ROE 지표 분석
    eps: string             // EPS 지표 분석
    debt_ratio: string      // 부채비율 분석
    target_gap: string      // 목표가 괴리율 분석
  } | null
}

export interface AIAnalysis {
  score: number
  signal: '매수' | '중립' | '주의'
  one_line: string
  summary: string[]
  risk: string
  metric_insights: {
    per: string             // PER 지표 분석
    pbr: string             // PBR 지표 분석
    roe: string             // ROE 지표 분석
    eps: string             // EPS 지표 분석
    debt_ratio: string      // 부채비율 분석
    target_gap: string      // 목표가 괴리율 분석
  }
}

export interface StockAnalysisRequest {
  ticker: string
}

export interface StockAnalysisResponse {
  stock_data: StockInfo
  ai_analysis: AIAnalysis | null
}

export type SignalType = '매수' | '중립' | '주의'

export interface UpdateLog {
  id: number
  created_at: string
  version: string | null
  category: string
  content: string
}

/**
 * 분석 진행 단계 상태
 */
export type ProgressStatus = 'pending' | 'in_progress' | 'completed' | 'error'

/**
 * 분석 진행 단계 정의
 */
export interface ProgressStep {
  id: string
  label: string
  icon: string // Lucide icon name
  status: ProgressStatus
  message?: string
}

/**
 * 진행 단계 ID 타입
 */
export type ProgressStepId = 'ticker_conversion' | 'data_fetching' | 'ai_analysis' | 'completed'

