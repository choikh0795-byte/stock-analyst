import React, { useState } from 'react'
import type { StockInfo, AIAnalysis } from '../types/stock'
import { calculatePriceChange, getSignalColor } from '../utils/stockUtils'
import { PriceRangeBar } from './PriceRangeBar'
import { MetricModal } from './MetricModal'
import { Tag, Building2, TrendingUp, Coins, Activity, Target, ChevronRight } from 'lucide-react'

interface StockCardProps {
  data: StockInfo
  aiAnalysis?: AIAnalysis | null
}

/**
 * Modern Fintech Bento Grid 스타일의 Accordion 주식 카드 컴포넌트
 */
export const StockCard: React.FC<StockCardProps> = ({ data, aiAnalysis }) => {
  const [isExpanded, setIsExpanded] = useState(false)
  const [selectedMetric, setSelectedMetric] = useState<string | null>(null)
  const priceChange = calculatePriceChange(data.current_price, data.previous_close)
  const isPositive = priceChange.value >= 0

  // AI 점수 뱃지 색상
  const signalColor = aiAnalysis ? getSignalColor(aiAnalysis.signal) : '#3b82f6'

  // 목표가 괴리율 계산 ((목표가 - 현재가) / 현재가 * 100)
  const targetUpside =
    data.target_mean_price && data.current_price
      ? ((data.target_mean_price - data.current_price) / data.current_price) * 100
      : null

  // 숫자 변환 헬퍼 함수
  const toNumber = (value: any): number | null => {
    if (value === null || value === undefined) return null
    if (typeof value === 'number') return value
    if (typeof value === 'string') {
      const parsed = parseFloat(value)
      return isNaN(parsed) ? null : parsed
    }
    return null
  }

  // 지표 값 변환
  const peRatio = toNumber(data.pe_ratio)
  const pbRatio = toNumber(data.pb_ratio)
  const returnOnEquity = toNumber(data.return_on_equity)
  const dividendYield = toNumber(data.dividend_yield)
  const beta = toNumber(data.beta)

  // 6개 고정 지표 배열 생성 (항상 6개 표시, 값이 없으면 'N/A')
  const metricCards = [
    // 1. PER
    {
      key: 'pe_ratio',
      label: 'PER',
      value: peRatio !== null 
        ? `${peRatio.toFixed(1)}배` 
        : 'N/A',
      comment: peRatio !== null && peRatio <= 10 
        ? '10이하 저평가' 
        : null,
      Icon: Tag,
    },
    // 2. PBR
    {
      key: 'pb_ratio',
      label: 'PBR',
      value: pbRatio !== null 
        ? `${pbRatio.toFixed(1)}배` 
        : 'N/A',
      comment: pbRatio !== null && pbRatio <= 1 
        ? '1이하 저평가' 
        : null,
      Icon: Building2,
    },
    // 3. ROE
    {
      key: 'return_on_equity',
      label: 'ROE',
      value: returnOnEquity !== null 
        ? `${(returnOnEquity * 100).toFixed(1)}%` 
        : 'N/A',
      comment: returnOnEquity !== null && returnOnEquity >= 0.15 
        ? '15%이상 우수' 
        : null,
      Icon: TrendingUp,
    },
    // 4. 배당률
    {
      key: 'dividend_yield',
      label: '배당률',
      value: dividendYield !== null 
        ? `${(dividendYield * 100).toFixed(2)}%` 
        : 'N/A',
      comment: null,
      Icon: Coins,
    },
    // 5. 변동성 (Beta)
    {
      key: 'beta',
      label: '변동성',
      value: beta !== null 
        ? beta.toFixed(2) 
        : 'N/A',
      comment: beta !== null ? 'Beta' : null,
      Icon: Activity,
    },
    // 6. 목표가
    {
      key: 'target_mean_price',
      label: '목표가',
      value: targetUpside !== null 
        ? `${targetUpside > 0 ? '+' : ''}${targetUpside.toFixed(1)}%` 
        : 'N/A',
      comment: targetUpside !== null ? '여력' : null,
      Icon: Target,
      color: targetUpside !== null && targetUpside > 0 ? 'text-red-500' : null,
    },
  ]

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* 기본 카드 (Collapsed) - Bento Grid 스타일 */}
      <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-4">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full text-left active:bg-slate-50 transition-colors duration-200"
          aria-label={isExpanded ? '상세 분석 닫기' : '상세 분석 보기'}
        >
          {/* Bento Grid 레이아웃: 가로 배치 (모바일/데스크톱 모두) */}
          <div className="flex flex-row items-start gap-4 sm:gap-6 p-4 sm:p-6">
            {/* 좌측: 종목명 및 티커 */}
            <div className="min-w-0 flex-1">
              <h2 className="text-lg sm:text-xl font-bold text-slate-900 truncate leading-tight">
                {data.name}
              </h2>
              <p className="text-xs sm:text-sm text-slate-500 mt-1 truncate">
                {data.symbol}
              </p>
            </div>

            {/* 우측 그룹: 가격/등락률 + AI 점수 + 화살표 */}
            <div className="flex items-center gap-3 sm:gap-4 flex-shrink-0">
              {/* 가격 및 등락률 */}
              <div className="flex flex-col items-end justify-center flex-shrink-0">
                <div className="text-xl sm:text-2xl font-bold text-slate-900 mb-1 whitespace-nowrap">
                  ${data.current_price.toFixed(2)}
                </div>
                <div
                  className={`text-sm sm:text-base font-semibold whitespace-nowrap ${
                    isPositive ? 'text-red-500' : 'text-blue-500'
                  }`}
                >
                  {isPositive ? '+' : ''}
                  {priceChange.percentage.toFixed(2)}%
                </div>
              </div>

              {/* AI 점수 뱃지 */}
              {aiAnalysis && (
                <div
                  className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl text-white font-bold text-xs sm:text-sm shadow-sm whitespace-nowrap"
                  style={{ backgroundColor: signalColor }}
                >
                  {aiAnalysis.score}점
                </div>
              )}
              
              {/* 화살표 */}
              <div
                className={`transform transition-transform duration-300 flex-shrink-0 ${
                  isExpanded ? 'rotate-180' : ''
                }`}
              >
                <svg
                  className="w-5 h-5 text-slate-400"
                  fill="none"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path d="M19 9l-7 7-7-7"></path>
                </svg>
              </div>
            </div>
          </div>
        </button>
      </div>

      {/* 확장 섹션 (Expanded) - 부드러운 애니메이션 */}
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? 'max-h-[2000px] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden mb-4">
          <div className="p-5 sm:p-6 space-y-6">
            {/* 섹션 1: 52주 가격 위치 (Progress Bar) */}
            {data.fifty_two_week_low &&
              data.fifty_two_week_high &&
              data.fifty_two_week_low !== null &&
              data.fifty_two_week_high !== null && (
                <div className="pb-6 border-b border-slate-200">
                  <h3 className="text-base sm:text-lg font-semibold text-slate-900 mb-4">
                    52주 가격 위치
                  </h3>
                  <PriceRangeBar
                    current={data.current_price}
                    low={data.fifty_two_week_low}
                    high={data.fifty_two_week_high}
                  />
                </div>
              )}

            {/* 섹션 2: 주요 지표 그리드 (Bento Style - 모바일 2열, 태블릿/PC 3열) */}
            <div className="pb-6 border-b border-slate-200">
              <h3 className="text-base sm:text-lg font-semibold text-slate-900 mb-4">
                주요 지표
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {metricCards.map((metric, index) => {
                  const IconComponent = metric.Icon
                  return (
                    <button
                      key={index}
                      onClick={() => setSelectedMetric(metric.key)}
                      className="group bg-slate-50 rounded-xl p-3 border border-slate-100 hover:bg-slate-100 hover:border-slate-300 hover:-translate-y-1 hover:shadow-md active:translate-y-0 active:shadow-sm transition-all duration-200 cursor-pointer text-left relative"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <IconComponent className="w-4 h-4 text-slate-600" />
                          <span className="text-xs font-medium text-slate-500">
                            {metric.label}
                          </span>
                        </div>
                        <ChevronRight className="w-3 h-3 text-slate-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                      <div className="mb-1">
                        <span className={`text-lg font-bold ${metric.color || 'text-slate-900'}`}>
                          {metric.value}
                        </span>
                      </div>
                      {metric.comment && (
                        <div className={`text-xs mt-1 ${metric.color || 'text-slate-500'}`}>
                          {metric.comment}
                        </div>
                      )}
                      <div className="text-xs text-slate-400 mt-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        자세히 보기
                      </div>
                    </button>
                  )
                })}
              </div>
              {data.target_mean_price && data.number_of_analyst_opinions && (
                <p className="text-xs text-slate-500 mt-3 text-center">
                  목표가는 {data.number_of_analyst_opinions}명의 애널리스트 의견 기준
                </p>
              )}
            </div>

            {/* 섹션 3: AI 3줄 요약 (말풍선 스타일) */}
            {aiAnalysis && (
              <div>
                <h3 className="text-base sm:text-lg font-semibold text-slate-900 mb-4">
                  AI 3줄 요약
                </h3>
                {/* 말풍선 스타일 카드 */}
                <div className="relative bg-slate-50 rounded-2xl p-5 sm:p-6 border border-slate-200">
                  {/* 말풍선 꼬리 */}
                  <div className="absolute -top-2 left-8 w-4 h-4 bg-slate-50 border-l border-t border-slate-200 transform rotate-45"></div>

                  {/* 핵심 한 줄 요약 */}
                  <div className="mb-4 pb-4 border-b border-slate-200">
                    <p className="text-sm sm:text-base text-slate-900 font-medium leading-relaxed">
                      {aiAnalysis.one_line}
                    </p>
                  </div>

                  {/* 3줄 요약 리스트 */}
                  <div className="space-y-2.5">
                    {aiAnalysis.summary.slice(0, 3).map((point, index) => (
                      <div
                        key={index}
                        className="flex items-start gap-2.5 text-sm sm:text-base text-slate-700 leading-relaxed"
                      >
                        <span className="text-red-500 mt-0.5 font-bold">•</span>
                        <span>{point}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Metric Modal */}
      <MetricModal
        isOpen={selectedMetric !== null}
        onClose={() => setSelectedMetric(null)}
        metricKey={selectedMetric}
        stockData={data}
      />
    </div>
  )
}
