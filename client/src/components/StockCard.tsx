import React, { useState } from 'react'
import type { StockInfo, AIAnalysis } from '../types/stock'
import { getSignalColor } from '../utils/stockUtils'
import { PriceRangeBar } from './PriceRangeBar'
import { MetricModal } from './MetricModal'
import { Tag, Building2, TrendingUp, Coins, DollarSign, Target, ChevronRight, CheckCircle2 } from 'lucide-react'

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
  // 백엔드에서 계산된 change_status 사용
  const isPositive = data.change_status === 'RISING'

  // AI 점수 뱃지 색상
  const signalColor = aiAnalysis ? getSignalColor(aiAnalysis.signal) : '#3b82f6'

  // 숫자 변환 헬퍼 함수 (UI 로직 판단용)
  const toNumber = (value: any): number | null => {
    if (value === null || value === undefined) return null
    if (typeof value === 'number') return value
    if (typeof value === 'string') {
      const parsed = parseFloat(value)
      return isNaN(parsed) ? null : parsed
    }
    return null
  }

  // 지표 값 변환 (UI 로직 판단용)
  const peRatio = toNumber(data.pe_ratio)
  const pbRatio = toNumber(data.pb_ratio)
  // ROE: 백엔드 계산(%) 우선, 없으면 과거 필드(return_on_equity: 소수) 사용
  const roePercent = toNumber(data.roe) ?? (toNumber(data.return_on_equity) !== null
    ? (toNumber(data.return_on_equity) as number) * 100
    : null)
  const dividendYieldRaw = toNumber(data.dividend_yield)
  const epsValue = toNumber(data.eps)
  
  // 백엔드에서 포맷팅된 문자열 사용 (우선순위)
  const peRatioStr = data.pe_ratio_str ?? (peRatio !== null ? `${peRatio.toFixed(1)}배` : 'N/A')
  const pbRatioStr = data.pb_ratio_str ?? (pbRatio !== null ? `${pbRatio.toFixed(1)}배` : 'N/A')
  const roeLabel = data.roe_str ?? (roePercent !== null ? `${roePercent.toFixed(1)}%` : 'N/A')
  const dividendYieldStr = data.dividend_yield_str ?? (dividendYieldRaw !== null ? `${dividendYieldRaw.toFixed(2)}%` : 'N/A')
  const epsLabel = data.eps_str ?? (epsValue !== null ? 'N/A' : 'N/A')
  const targetUpsideStr = data.target_upside_str ?? 'N/A'

  // 지표 상태 판단 함수
  const getMetricStatus = (key: string, value: number | null): { status: string; badgeClass: string } => {
    switch (key) {
      case 'pe_ratio':
        if (value === null) return { status: 'N/A', badgeClass: 'bg-slate-100 text-slate-600' }
        if (value <= 10) return { status: '저평가', badgeClass: 'bg-emerald-100 text-emerald-700' }
        if (value <= 20) return { status: '적정', badgeClass: 'bg-slate-100 text-slate-600' }
        return { status: '고평가', badgeClass: 'bg-rose-100 text-rose-700' }
      case 'pb_ratio':
        if (value === null) return { status: 'N/A', badgeClass: 'bg-slate-100 text-slate-600' }
        if (value <= 1) return { status: '저평가', badgeClass: 'bg-emerald-100 text-emerald-700' }
        if (value <= 2) return { status: '적정', badgeClass: 'bg-slate-100 text-slate-600' }
        return { status: '고평가', badgeClass: 'bg-rose-100 text-rose-700' }
      case 'roe':
        if (value === null) return { status: 'N/A', badgeClass: 'bg-slate-100 text-slate-600' }
        if (value >= 15) return { status: '우수', badgeClass: 'bg-emerald-100 text-emerald-700' }
        if (value >= 10) return { status: '양호', badgeClass: 'bg-slate-100 text-slate-600' }
        return { status: '개선필요', badgeClass: 'bg-rose-100 text-rose-700' }
      case 'dividend_yield':
        // 백엔드에서 이미 퍼센트 값(예: 0.11%)을 내려주므로 그대로 퍼센트 단위로 비교
        if (value === null) return { status: 'N/A', badgeClass: 'bg-slate-100 text-slate-600' }
        if (value >= 5) return { status: '높은배당', badgeClass: 'bg-emerald-100 text-emerald-700' }
        if (value >= 2) return { status: '적정', badgeClass: 'bg-slate-100 text-slate-600' }
        return { status: '낮은배당', badgeClass: 'bg-slate-100 text-slate-600' }
      case 'eps':
        if (value === null) return { status: 'N/A', badgeClass: 'bg-slate-100 text-slate-600' }
        return { status: '데이터', badgeClass: 'bg-slate-100 text-slate-600' }
      case 'target_mean_price':
        if (value === null) return { status: 'N/A', badgeClass: 'bg-slate-100 text-slate-600' }
        if (value > 10) return { status: '상승여력', badgeClass: 'bg-emerald-100 text-emerald-700' }
        if (value > 0) return { status: '여력', badgeClass: 'bg-slate-100 text-slate-600' }
        return { status: '주의', badgeClass: 'bg-rose-100 text-rose-700' }
      default:
        return { status: 'N/A', badgeClass: 'bg-slate-100 text-slate-600' }
    }
  }

  // 6개 고정 지표 배열 생성 (항상 6개 표시, 값이 없으면 'N/A')
  const metricCards = [
    // 1. PER
    {
      key: 'pe_ratio',
      label: 'PER',
      value: peRatioStr,
      numericValue: peRatio,
      status: getMetricStatus('pe_ratio', peRatio),
      Icon: Tag,
    },
    // 2. PBR
    {
      key: 'pb_ratio',
      label: 'PBR',
      value: pbRatioStr,
      numericValue: pbRatio,
      status: getMetricStatus('pb_ratio', pbRatio),
      Icon: Building2,
    },
    // 3. ROE
    {
      key: 'roe',
      label: 'ROE',
      value: roeLabel,
      numericValue: roePercent,
      status: getMetricStatus('roe', roePercent),
      Icon: TrendingUp,
    },
    // 4. 배당수익률
    {
      key: 'dividend_yield',
      label: '배당수익률',
      value: dividendYieldStr,
      numericValue: dividendYieldRaw,
      status: getMetricStatus('dividend_yield', dividendYieldRaw),
      Icon: Coins,
    },
    // 5. EPS (주당순이익)
    {
      key: 'eps',
      label: 'EPS',
      value: epsLabel,
      numericValue: epsValue,
      status: getMetricStatus('eps', epsValue),
      Icon: DollarSign,
    },
    // 6. 목표가
    {
      key: 'target_mean_price',
      label: '목표가',
      value: targetUpsideStr,
      numericValue: data.target_upside,
      status: getMetricStatus('target_mean_price', data.target_upside),
      Icon: Target,
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
                  {data.current_price_str || '-'}
                </div>
                <div
                  className={`text-sm sm:text-base font-semibold whitespace-nowrap ${
                    isPositive ? 'text-red-500' : 'text-blue-500'
                  }`}
                >
                  {data.change_percentage_str || '-'}
                </div>
              </div>

              {/* AI 점수 뱃지 */}
              {aiAnalysis && (
                <div
                  className="px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl text-white font-bold text-xs sm:text-sm shadow-sm whitespace-nowrap"
                  style={{ backgroundColor: signalColor }}
                >
                  {typeof aiAnalysis.score === 'number' ? aiAnalysis.score.toFixed(1) : String(aiAnalysis.score)}점
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
                    currency={data.currency}
                    current_str={data.current_price_str}
                    low_str={data.fifty_two_week_low_str}
                    high_str={data.fifty_two_week_high_str}
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
                      className="group bg-white rounded-xl p-4 border border-slate-200 hover:bg-slate-50 hover:border-blue-500 hover:ring-2 hover:ring-blue-500 hover:ring-opacity-20 hover:-translate-y-0.5 hover:shadow-lg active:translate-y-0 active:shadow-sm transition-all duration-200 cursor-pointer text-left relative"
                    >
                      {/* 헤더: Title (좌측)과 Arrow Icon (우측) 정렬 */}
                      <div className="flex justify-between items-start w-full mb-3">
                        <div className="flex items-center gap-2">
                          <IconComponent className="w-4 h-4 text-slate-600" />
                          <span className="text-xs font-medium text-slate-500">
                            {metric.label}
                          </span>
                        </div>
                        {/* 우측 상단 ChevronRight 아이콘 */}
                        <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0 group-hover:text-blue-500 transition-colors" />
                      </div>
                      {/* Value: 크고 진하게 */}
                      <div className="mb-2">
                        <span className="text-2xl font-extrabold text-slate-900">
                          {metric.value}
                        </span>
                      </div>
                      {/* Status Badge */}
                      <div className="inline-flex">
                        <span className={`px-2 py-0.5 rounded text-xs font-bold ${metric.status.badgeClass}`}>
                          {metric.status.status}
                        </span>
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

            {/* 섹션 3: AI 3줄 요약 (그라데이션 + 아이콘 스타일) */}
            {aiAnalysis && (
              <div>
                <h3 className="text-base sm:text-lg font-semibold text-slate-900 mb-4">
                  AI 3줄 요약
                </h3>
                {/* 그라데이션 배경 카드 */}
                <div className="relative bg-gradient-to-br from-indigo-50 to-white rounded-2xl p-5 sm:p-6 border border-indigo-100 shadow-sm">
                  {/* 핵심 한 줄 요약 */}
                  <div className="mb-5 pb-4 border-b border-indigo-200">
                    <p className="text-sm sm:text-base text-slate-800 font-medium leading-relaxed">
                      {aiAnalysis.one_line}
                    </p>
                  </div>

                  {/* 3줄 요약 리스트 (CheckCircle2 아이콘) */}
                  <div className="space-y-3">
                    {aiAnalysis.summary.slice(0, 3).map((point, index) => {
                      // 핵심 키워드 하이라이트 함수
                      const highlightKeywords = (text: string) => {
                        const keywords = ['저평가', '고평가', '매수', '매도', '기회', '리스크', '위험', '우수', '개선', '적정', '높은', '낮은', '상승', '하락']
                        let highlighted = text
                        keywords.forEach(keyword => {
                          const regex = new RegExp(`(${keyword})`, 'gi')
                          highlighted = highlighted.replace(regex, '<strong class="font-bold text-slate-900">$1</strong>')
                        })
                        return highlighted
                      }

                      return (
                        <div
                          key={index}
                          className="flex items-start gap-3 text-sm sm:text-base text-slate-700 leading-relaxed"
                        >
                          <CheckCircle2 className="w-5 h-5 text-indigo-600 flex-shrink-0 mt-0.5" />
                          <span 
                            className="font-medium text-slate-800"
                            dangerouslySetInnerHTML={{ __html: highlightKeywords(point) }}
                          />
                        </div>
                      )
                    })}
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
