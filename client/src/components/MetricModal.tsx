import React, { useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { METRIC_DEFINITIONS } from '../constants/metrics'
import type { StockInfo } from '../types/stock'
import { Tag, Building2, TrendingUp, Coins, Activity, Target, X } from 'lucide-react'

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
    return_on_equity: TrendingUp,
    dividend_yield: Coins,
    beta: Activity,
    target_mean_price: Target,
  }

  const IconComponent = iconMap[metricKey] || Tag

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
      case 'return_on_equity':
        return stockData.return_on_equity !== null && stockData.return_on_equity !== undefined
          ? `${(stockData.return_on_equity * 100).toFixed(1)}%`
          : 'N/A'
      case 'dividend_yield':
        return stockData.dividend_yield !== null && stockData.dividend_yield !== undefined
          ? `${(stockData.dividend_yield * 100).toFixed(2)}%`
          : 'N/A'
      case 'beta':
        return stockData.beta !== null && stockData.beta !== undefined
          ? stockData.beta.toFixed(2)
          : 'N/A'
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

  // AI 인사이트 가져오기
  const aiInsight = stockData.metric_insights?.[metricKey as keyof typeof stockData.metric_insights]

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
      case 'return_on_equity':
        const roe = stockData.return_on_equity
        if (roe !== null && roe !== undefined) {
          if (roe >= 0.15) {
            return {
              status: '우수',
              colorClass: 'text-emerald-600',
              bgClass: 'bg-emerald-50',
              textColor: 'text-emerald-700',
            }
          }
          if (roe >= 0.1) {
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
      case 'dividend_yield':
        const div = stockData.dividend_yield
        if (div !== null && div !== undefined) {
          if (div >= 0.05) {
            return {
              status: '높은 배당',
              colorClass: 'text-emerald-600',
              bgClass: 'bg-emerald-50',
              textColor: 'text-emerald-700',
            }
          }
          if (div >= 0.02) {
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
      case 'beta':
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

              {/* Header */}
              <div className="flex items-center justify-between px-5 pb-4 border-b border-slate-200 flex-shrink-0">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${metricStatus.bgClass}`}>
                    <IconComponent className={`w-5 h-5 ${metricStatus.textColor}`} />
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
                {/* Section A: 정의 */}
                <div>
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                    <p className="text-sm text-slate-600 leading-relaxed">
                      {metricDef.definition}
                    </p>
                  </div>
                </div>

                {/* Section B: 현재 수치 */}
                <div className="text-center">
                  <div className={`text-4xl font-black ${metricStatus.colorClass} mb-3`}>
                    {getMetricValue()}
                  </div>
                  
                  {/* Section C: 평가 배지 */}
                  <div className="inline-flex items-center">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${metricStatus.bgClass} ${metricStatus.textColor}`}>
                      {metricStatus.status}
                    </span>
                  </div>
                </div>

                {/* Section D: AI 코멘트 */}
                {aiInsight && (
                  <div className="border-l-4 border-blue-500 bg-blue-50 rounded-r-xl p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-xs font-bold">AI</span>
                        </div>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-slate-800 leading-relaxed">
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
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-slate-200 flex-shrink-0">
                <div className="flex items-center gap-3">
                  <div className={`p-2 rounded-lg ${metricStatus.bgClass}`}>
                    <IconComponent className={`w-5 h-5 ${metricStatus.textColor}`} />
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
                {/* Section A: 정의 */}
                <div>
                  <div className="bg-slate-50 rounded-xl p-4 border border-slate-200">
                    <p className="text-sm text-slate-600 leading-relaxed">
                      {metricDef.definition}
                    </p>
                  </div>
                </div>

                {/* Section B: 현재 수치 */}
                <div className="text-center">
                  <div className={`text-5xl font-black ${metricStatus.colorClass} mb-3`}>
                    {getMetricValue()}
                  </div>
                  
                  {/* Section C: 평가 배지 */}
                  <div className="inline-flex items-center">
                    <span className={`px-3 py-1 rounded-full text-sm font-bold ${metricStatus.bgClass} ${metricStatus.textColor}`}>
                      {metricStatus.status}
                    </span>
                  </div>
                </div>

                {/* Section D: AI 코멘트 */}
                {aiInsight && (
                  <div className="border-l-4 border-blue-500 bg-blue-50 rounded-r-xl p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0">
                        <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-xs font-bold">AI</span>
                        </div>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-slate-800 leading-relaxed">
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

