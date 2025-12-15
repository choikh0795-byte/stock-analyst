import React, { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { METRIC_DEFINITIONS } from '../constants/metrics'
import type { StockInfo } from '../types/stock'
import { Tag, Building2, TrendingUp, Coins, DollarSign, Target, X, BookOpen, Bot, Lightbulb } from 'lucide-react'

interface MetricModalProps {
  isOpen: boolean
  onClose: () => void
  metricKey: string | null
  stockData: StockInfo | null
}

/**
 * 지표 상세 정보를 보여주는 모달 컴포넌트
 * 모바일: Bottom Sheet 형태
 * 데스크톱: 중앙 모달 형태
 */
export const MetricModal: React.FC<MetricModalProps> = ({
  isOpen,
  onClose,
  metricKey,
  stockData,
}) => {
  // ESC 키로 모달 닫기
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    document.addEventListener('keydown', handleEscape)
    return () => document.removeEventListener('keydown', handleEscape)
  }, [isOpen, onClose])

  // body 스크롤 잠금
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = 'unset'
    }
    return () => {
      document.body.style.overflow = 'unset'
    }
  }, [isOpen])

  if (!isOpen || !metricKey || !stockData) return null

  const metricDef = METRIC_DEFINITIONS[metricKey]
  if (!metricDef) return null

  // 아이콘 매핑
  const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
    pe_ratio: Tag,
    pb_ratio: Building2,
    roe: TrendingUp,
    return_on_equity: TrendingUp,
    dividend_yield: Coins,
    beta: DollarSign,
    eps: DollarSign,
    target_mean_price: Target,
  }

  const IconComponent = iconMap[metricKey] || Tag

  const normalizeDividendYield = () => {
    const raw = stockData.dividend_yield
    if (raw === null || raw === undefined) return { ratio: null, percent: null }

    const numeric = typeof raw === 'number' ? raw : parseFloat(String(raw))
    if (Number.isNaN(numeric)) return { ratio: null, percent: null }

    // 백엔드에서 이미 퍼센트 값(예: 0.11%)을 내려주므로 그대로 사용
    return {
      ratio: numeric,
      percent: numeric,
    }
  }

  const dividendYieldNormalized = normalizeDividendYield()

  // 지표 값 가져오기
  const getMetricValue = (): string => {
    switch (metricKey) {
      case 'pe_ratio':
        return stockData.pe_ratio !== null && stockData.pe_ratio !== undefined
          ? `${stockData.pe_ratio.toFixed(1)}배`
          : 'N/A'
      case 'pb_ratio':
        return stockData.pb_ratio !== null && stockData.pb_ratio !== undefined
          ? `${stockData.pb_ratio.toFixed(1)}배`
          : 'N/A'
      case 'roe':
      case 'return_on_equity': {
        // roe: 백엔드 계산(%) 우선, 없으면 구버전 소수값 사용
        const roePercent = stockData.roe ?? (stockData.return_on_equity !== undefined && stockData.return_on_equity !== null
          ? stockData.return_on_equity * 100
          : null)
        if (roePercent !== null && roePercent !== undefined) {
          return `${roePercent.toFixed(1)}%`
        }
        return stockData.roe_str || 'N/A'
      }
      case 'dividend_yield':
        return dividendYieldNormalized.percent !== null && dividendYieldNormalized.percent !== undefined
          ? `${dividendYieldNormalized.percent.toFixed(2)}%`
          : 'N/A'
      case 'beta':
        return stockData.beta !== null && stockData.beta !== undefined
          ? stockData.beta.toFixed(2)
          : 'N/A'
      case 'eps':
        return stockData.eps_str || (stockData.eps !== null && stockData.eps !== undefined
          ? (stockData.currency === 'KRW' 
            ? `${Math.floor(stockData.eps).toLocaleString()}원`
            : `$${stockData.eps.toFixed(2)}`)
          : 'N/A')
      case 'target_mean_price':
        if (stockData.target_mean_price && stockData.current_price) {
          const upside = ((stockData.target_mean_price - stockData.current_price) / stockData.current_price) * 100
          return `${upside > 0 ? '+' : ''}${upside.toFixed(1)}%`
        }
        return 'N/A'
      default:
        return 'N/A'
    }
  }

  // AI 인사이트 가져오기 (ROE는 roe 또는 return_on_equity로 매핑, EPS는 eps로 직접 접근)
  const getAIInsight = (): string | undefined => {
    if (!stockData.metric_insights) return undefined
    
    // metricKey에 따라 적절한 키로 매핑
    if (metricKey === 'roe' || metricKey === 'return_on_equity') {
      // roe 키를 먼저 확인하고, 없으면 return_on_equity로 fallback
      return stockData.metric_insights.roe || stockData.metric_insights.return_on_equity
    }
    // EPS는 그대로 사용
    else if (metricKey === 'eps') {
      return stockData.metric_insights.eps
    }
    // 다른 지표들은 metricKey 그대로 사용
    else {
      return stockData.metric_insights[metricKey as keyof typeof stockData.metric_insights] as string | undefined
    }
  }
  
  const aiInsight = getAIInsight()

  // 지표 평가 상태 및 색상 결정
  const getMetricStatus = (): { status: string; colorClass: string; bgClass: string; textColor: string } => {
    const value = getMetricValue()
    if (value === 'N/A') {
      return {
        status: '데이터 없음',
        colorClass: 'text-slate-600',
        bgClass: 'bg-slate-50',
        textColor: 'text-slate-600',
      }
    }

    switch (metricKey) {
      case 'pe_ratio':
        const pe = stockData.pe_ratio
        if (pe !== null && pe !== undefined) {
          if (pe <= 10) {
            return {
              status: '저평가',
              colorClass: 'text-emerald-600',
              bgClass: 'bg-emerald-50',
              textColor: 'text-emerald-700',
            }
          }
          if (pe <= 20) {
            return {
              status: '적정',
              colorClass: 'text-slate-600',
              bgClass: 'bg-slate-50',
              textColor: 'text-slate-700',
            }
          }
          return {
            status: '고평가',
            colorClass: 'text-rose-600',
            bgClass: 'bg-rose-50',
            textColor: 'text-rose-700',
          }
        }
        break
      case 'pb_ratio':
        const pb = stockData.pb_ratio
        if (pb !== null && pb !== undefined) {
          if (pb <= 1) {
            return {
              status: '저평가',
              colorClass: 'text-emerald-600',
              bgClass: 'bg-emerald-50',
              textColor: 'text-emerald-700',
            }
          }
          if (pb <= 2) {
            return {
              status: '적정',
              colorClass: 'text-slate-600',
              bgClass: 'bg-slate-50',
              textColor: 'text-slate-700',
            }
          }
          return {
            status: '고평가',
            colorClass: 'text-rose-600',
            bgClass: 'bg-rose-50',
            textColor: 'text-rose-700',
          }
        }
        break
      case 'roe':
      case 'return_on_equity': {
        const roePercent = stockData.roe ?? (stockData.return_on_equity !== undefined && stockData.return_on_equity !== null
          ? stockData.return_on_equity * 100
          : null)
        if (roePercent !== null && roePercent !== undefined) {
          if (roePercent >= 15) {
            return {
              status: '우수',
              colorClass: 'text-emerald-600',
              bgClass: 'bg-emerald-50',
              textColor: 'text-emerald-700',
            }
          }
          if (roePercent >= 10) {
            return {
              status: '양호',
              colorClass: 'text-slate-600',
              bgClass: 'bg-slate-50',
              textColor: 'text-slate-700',
            }
          }
          return {
            status: '개선 필요',
            colorClass: 'text-rose-600',
            bgClass: 'bg-rose-50',
            textColor: 'text-rose-700',
          }
        }
        break
      }
      case 'dividend_yield':
        // 퍼센트 값 그대로 비교 (예: 0.11% -> 0.11로 전달됨)
        const divRatio = dividendYieldNormalized.ratio
        if (divRatio !== null && divRatio !== undefined) {
          if (divRatio >= 5) {
            return {
              status: '높은 배당',
              colorClass: 'text-emerald-600',
              bgClass: 'bg-emerald-50',
              textColor: 'text-emerald-700',
            }
          }
          if (divRatio >= 2) {
            return {
              status: '적정',
              colorClass: 'text-slate-600',
              bgClass: 'bg-slate-50',
              textColor: 'text-slate-700',
            }
          }
          return {
            status: '낮은 배당',
            colorClass: 'text-slate-600',
            bgClass: 'bg-slate-50',
            textColor: 'text-slate-700',
          }
        }
        break
      case 'beta': {
        const beta = stockData.beta
        if (beta !== null && beta !== undefined) {
          if (beta <= 0.8) {
            return {
              status: '안정적',
              colorClass: 'text-emerald-600',
              bgClass: 'bg-emerald-50',
              textColor: 'text-emerald-700',
            }
          }
          if (beta <= 1.2) {
            return {
              status: '보통',
              colorClass: 'text-slate-600',
              bgClass: 'bg-slate-50',
              textColor: 'text-slate-700',
            }
          }
          return {
            status: '변동성 큼',
            colorClass: 'text-rose-600',
            bgClass: 'bg-rose-50',
            textColor: 'text-rose-700',
          }
        }
        break
      }
      case 'eps': {
        const eps = stockData.eps
        if (eps !== null && eps !== undefined) {
          // EPS는 절대적인 평가 기준이 없으므로 단순히 데이터 존재 여부만 표시
          return {
            status: '데이터 있음',
            colorClass: 'text-slate-600',
            bgClass: 'bg-slate-50',
            textColor: 'text-slate-700',
          }
        }
        break
      }
      case 'target_mean_price':
        if (stockData.target_mean_price && stockData.current_price) {
          const upside = ((stockData.target_mean_price - stockData.current_price) / stockData.current_price) * 100
          if (upside > 10) {
            return {
              status: '상승 여력 큼',
              colorClass: 'text-emerald-600',
              bgClass: 'bg-emerald-50',
              textColor: 'text-emerald-700',
            }
          }
          if (upside > 0) {
            return {
              status: '상승 여력',
              colorClass: 'text-slate-600',
              bgClass: 'bg-slate-50',
              textColor: 'text-slate-700',
            }
          }
          return {
            status: '주의',
            colorClass: 'text-rose-600',
            bgClass: 'bg-rose-50',
            textColor: 'text-rose-700',
          }
        }
        break
    }
    return {
      status: '평가 불가',
      colorClass: 'text-slate-600',
      bgClass: 'bg-slate-50',
      textColor: 'text-slate-600',
    }
  }

  const metricStatus = getMetricStatus()

  const summaryText = metricDef.summary || metricDef.definition
  const tipText = metricDef.tip

  const HIGHLIGHT_KEYWORDS = ['저평가된 우량주']

  const renderTipContent = (text: string) => {
    const regex = new RegExp(`(${HIGHLIGHT_KEYWORDS.join('|')})`, 'g')
    return text.split(regex).filter(Boolean).map((part, index) => {
      if (HIGHLIGHT_KEYWORDS.includes(part)) {
        return (
          <span key={`${part}-${index}`} className="relative inline-block mx-1 align-baseline">
            <span className="absolute inset-x-0 bottom-0 h-2.5 bg-amber-200/60 -z-10 transform -rotate-1" />
            <span className="relative font-bold text-slate-900 underline decoration-amber-400/60 decoration-4 underline-offset-2">
              {part}
            </span>
          </span>
        )
      }
      return <React.Fragment key={`${part}-${index}`}>{part}</React.Fragment>
    })
  }

  const renderDefinitionSection = () => (
    <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 space-y-3">
      <div className="flex items-start gap-3">
        <BookOpen className="w-5 h-5 text-slate-600 flex-shrink-0 mt-0.5" />
        <p className="text-sm text-slate-700 leading-relaxed">{summaryText}</p>
      </div>

      {tipText && (
        <div className="flex gap-3 bg-amber-50 border border-amber-100 p-4 rounded-xl">
          <Lightbulb className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-sm text-slate-700 leading-relaxed">
            <span className="font-bold text-amber-600 mr-1">Tip!</span>
            {renderTipContent(tipText)}
          </div>
        </div>
      )}
    </div>
  )

  // Indicator Bar 계산 함수 (적정 범위 대비 현재 위치 시각화)
  const getIndicatorBar = () => {
    const value = getMetricValue()
    if (value === 'N/A') return null

    switch (metricKey) {
      case 'pe_ratio': {
        const pe = stockData.pe_ratio
        if (pe === null || pe === undefined) return null
        // 0~50 범위를 기준으로 (0~10: 좋음, 10~20: 적정, 20~50: 나쁨)
        const percentage = Math.min((pe / 50) * 100, 100)
        const isGood = pe <= 10
        const isNeutral = pe > 10 && pe <= 20
        return { percentage, isGood, isNeutral, value: pe }
      }
      case 'pb_ratio': {
        const pb = stockData.pb_ratio
        if (pb === null || pb === undefined) return null
        // 0~5 범위를 기준으로 (0~1: 좋음, 1~2: 적정, 2~5: 나쁨)
        const percentage = Math.min((pb / 5) * 100, 100)
        const isGood = pb <= 1
        const isNeutral = pb > 1 && pb <= 2
        return { percentage, isGood, isNeutral, value: pb }
      }
      case 'roe':
      case 'return_on_equity': {
        const roePercent = stockData.roe ?? (stockData.return_on_equity !== undefined && stockData.return_on_equity !== null
          ? stockData.return_on_equity * 100
          : null)
        if (roePercent === null || roePercent === undefined) return null
        // 0~30% 범위를 기준으로 (15~30: 좋음, 10~15: 적정, 0~10: 나쁨)
        const percentage = Math.min((roePercent / 30) * 100, 100)
        const isGood = roePercent >= 15
        const isNeutral = roePercent >= 10 && roePercent < 15
        return { percentage, isGood, isNeutral, value: roePercent }
      }
      case 'dividend_yield': {
        const divRatio = dividendYieldNormalized.ratio
        if (divRatio === null || divRatio === undefined) return null
        // 0~10% 범위 기준 (5% 이상: 좋음, 2~5%: 적정, 0~2%: 낮음)
        const percentage = Math.min((divRatio / 10) * 100, 100)
        const isGood = divRatio >= 5
        const isNeutral = divRatio >= 2 && divRatio < 5
        return { percentage, isGood, isNeutral, value: divRatio }
      }
      case 'target_mean_price': {
        if (stockData.target_mean_price && stockData.current_price) {
          const upside = ((stockData.target_mean_price - stockData.current_price) / stockData.current_price) * 100
          // -20~50% 범위를 기준으로 (10~50: 좋음, 0~10: 적정, -20~0: 나쁨)
          const normalized = (upside + 20) / 70 // -20을 0으로, 50을 100%로 정규화
          const percentage = Math.max(0, Math.min(normalized * 100, 100))
          const isGood = upside > 10
          const isNeutral = upside > 0 && upside <= 10
          return { percentage, isGood, isNeutral, value: upside }
        }
        return null
      }
      default:
        return null
    }
  }

  const indicatorBar = getIndicatorBar()

  // 모바일 애니메이션 variants
  const mobileVariants = {
    initial: { y: '100%' },
    animate: { y: 0 },
    exit: { y: '100%' },
  }

  // 데스크톱 애니메이션 variants
  const desktopVariants = {
    initial: { opacity: 0, scale: 0.95, x: '-50%', y: '-50%' },
    animate: { opacity: 1, scale: 1, x: '-50%', y: '-50%' },
    exit: { opacity: 0, scale: 0.95, x: '-50%', y: '-50%' },
  }

  // 백드롭 애니메이션 variants
  const backdropVariants = {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
  }

  if (!metricKey || !stockData) return null

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop - Glassmorphism */}
          <motion.div
            variants={backdropVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Mobile: Bottom Sheet */}
          <motion.div
            variants={mobileVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="fixed bottom-0 left-0 right-0 z-50 md:hidden"
          >
            <div
              className="bg-white rounded-t-[2rem] w-full max-h-[85vh] overflow-hidden flex flex-col shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Handle Bar (모바일 전용) */}
              <div className="flex justify-center pt-3 pb-2">
                <div className="w-12 h-1.5 bg-slate-200 rounded-full" />
              </div>

              {/* Header - 아이콘 크게 + 지표명 */}
              <div className="flex items-center justify-between px-5 pb-4 border-b border-slate-200 flex-shrink-0">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl ${metricStatus.bgClass}`}>
                    <IconComponent className={`w-7 h-7 ${metricStatus.textColor}`} />
                  </div>
                  <h2 className="text-xl font-bold text-slate-900">{metricDef.label}</h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-slate-100 rounded-full transition-colors active:bg-slate-200"
                  aria-label="닫기"
                >
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>

              {/* Body - 스크롤 가능 */}
              <div className="overflow-y-auto flex-1 px-5 py-6 space-y-6">
                {/* Section A: 정의 카드 - "이게 뭔가요?" */}
                {renderDefinitionSection()}

                {/* Section B: 내 종목 분석 - "그래서 어떤가요?" */}
                <div className="text-center space-y-4">
                  {/* Visual Score: 거대한 수치 */}
                  <div className={`text-5xl font-black ${metricStatus.colorClass} mb-2`}>
                    {getMetricValue()}
                  </div>
                  
                  {/* Status Badge */}
                  <div className="inline-flex items-center mb-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${metricStatus.bgClass} ${metricStatus.textColor}`}>
                      {metricStatus.status}
                    </span>
                  </div>

                  {/* Indicator Bar: 가로 막대 그래프 */}
                  {indicatorBar && (
                    <div className="w-full max-w-xs mx-auto">
                      <div className="relative h-3 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className={`absolute top-0 left-0 h-full transition-all duration-500 ${
                            indicatorBar.isGood
                              ? 'bg-emerald-500'
                              : indicatorBar.isNeutral
                              ? 'bg-slate-400'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${indicatorBar.percentage}%` }}
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-2">
                        적정 범위 대비 현재 위치
                      </p>
                    </div>
                  )}
                </div>

                {/* Section D: AI 코멘트 - Insight Box */}
                {aiInsight && (
                  <div className="bg-blue-50 p-4 rounded-xl border border-blue-100">
                    <div className="flex items-start gap-3">
                      <Bot className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm text-slate-800 leading-relaxed font-medium">
                          {aiInsight}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {!aiInsight && (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                    <p className="text-sm text-slate-500 text-center">
                      AI 평가 데이터가 없어요
                    </p>
                  </div>
                )}
              </div>
            </div>
          </motion.div>

          {/* Desktop: Center Modal */}
          <motion.div
            variants={desktopVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="hidden md:block fixed top-1/2 left-1/2 z-50 w-full max-w-md"
            style={{ transformOrigin: 'center center' }}
          >
            <div
              className="bg-white rounded-3xl shadow-2xl max-h-[85vh] overflow-hidden flex flex-col"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Header - 아이콘 크게 + 지표명 */}
              <div className="flex items-center justify-between p-6 border-b border-slate-200 flex-shrink-0">
                <div className="flex items-center gap-4">
                  <div className={`p-3 rounded-xl ${metricStatus.bgClass}`}>
                    <IconComponent className={`w-7 h-7 ${metricStatus.textColor}`} />
                  </div>
                  <h2 className="text-xl font-bold text-slate-900">{metricDef.label}</h2>
                </div>
                <button
                  onClick={onClose}
                  className="p-2 hover:bg-slate-100 rounded-full transition-colors active:bg-slate-200"
                  aria-label="닫기"
                >
                  <X className="w-5 h-5 text-slate-500" />
                </button>
              </div>

              {/* Body - 스크롤 가능 */}
              <div className="overflow-y-auto flex-1 p-6 space-y-6">
                {/* Section A: 정의 카드 - "이게 뭔가요?" */}
                {renderDefinitionSection()}

                {/* Section B: 내 종목 분석 - "그래서 어떤가요?" */}
                <div className="text-center space-y-4">
                  {/* Visual Score: 거대한 수치 */}
                  <div className={`text-5xl font-black ${metricStatus.colorClass} mb-2`}>
                    {getMetricValue()}
                  </div>
                  
                  {/* Status Badge */}
                  <div className="inline-flex items-center mb-4">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${metricStatus.bgClass} ${metricStatus.textColor}`}>
                      {metricStatus.status}
                    </span>
                  </div>

                  {/* Indicator Bar: 가로 막대 그래프 */}
                  {indicatorBar && (
                    <div className="w-full max-w-xs mx-auto">
                      <div className="relative h-3 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className={`absolute top-0 left-0 h-full transition-all duration-500 ${
                            indicatorBar.isGood
                              ? 'bg-emerald-500'
                              : indicatorBar.isNeutral
                              ? 'bg-slate-400'
                              : 'bg-rose-500'
                          }`}
                          style={{ width: `${indicatorBar.percentage}%` }}
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-2">
                        적정 범위 대비 현재 위치
                      </p>
                    </div>
                  )}
                </div>

                {/* Section D: AI 코멘트 - Insight Box */}
                {aiInsight && (
                  <div className="bg-blue-50 p-4 rounded-xl border border-blue-100">
                    <div className="flex items-start gap-3">
                      <Bot className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                      <div className="flex-1">
                        <p className="text-sm text-slate-800 leading-relaxed font-medium">
                          {aiInsight}
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {!aiInsight && (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4">
                    <p className="text-sm text-slate-500 text-center">
                      AI 평가 데이터가 없어요
                    </p>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

