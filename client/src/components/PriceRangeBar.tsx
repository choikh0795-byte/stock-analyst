import React from 'react'

interface PriceRangeBarProps {
  current: number
  low: number | null | undefined
  high: number | null | undefined
  currency?: string
  // 백엔드에서 포맷팅된 문자열 (우선 사용)
  current_str?: string | null
  low_str?: string | null
  high_str?: string | null
}

/**
 * 52주 가격 범위를 시각적으로 표시하는 Progress Bar 컴포넌트
 */
export const PriceRangeBar: React.FC<PriceRangeBarProps> = ({
  current,
  low,
  high,
  currency = 'USD',
  current_str,
  low_str,
  high_str,
}) => {
  const formatPrice = (price: number, formattedStr?: string | null): string => {
    // 백엔드에서 포맷팅된 문자열이 있으면 우선 사용
    if (formattedStr) {
      return formattedStr
    }
    // Fallback: 기본 포맷팅 (백엔드에서 제공하지 않은 경우에만)
    return String(price)
  }
  // 데이터가 없으면 표시하지 않음
  if (!low || !high || low >= high) {
    return null
  }

  // 범위 계산 (52주 최저가와 최고가 기준)
  const range = high - low

  // 현재가의 위치를 퍼센트로 계산
  let position: number = ((current - low) / range) * 100

  // 현재가가 범위 내에 있는지 확인
  const isInRange = current >= low && current <= high
  const isNewHigh = current >= high  // 52주 신고가 도달/돌파
  const isNewLow = current < low     // 52주 신저가

  // 점 위치를 0~100% 범위로 제한 (항상 바 안에 표시)
  const clampedPosition = Math.max(0, Math.min(100, position))

  return (
    <div className="w-full">
      {/* 라벨: 최저가, 현재가, 최고가 */}
      <div className="flex justify-between items-center mb-4">
        <div className="text-left">
          <div className="text-xs text-slate-500 mb-1">52주 최저</div>
          <div className="text-sm sm:text-base font-semibold text-slate-700">
            {low ? formatPrice(low, low_str) : '-'}
          </div>
        </div>
        <div className="text-center flex-1 mx-4">
          <div className="text-xs text-slate-500 mb-1">현재가</div>
          <div className="text-base sm:text-lg font-bold text-slate-900">
            {formatPrice(current, current_str)}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-500 mb-1">52주 최고</div>
          <div className="text-sm sm:text-base font-semibold text-slate-700">
            {high ? formatPrice(high, high_str) : '-'}
          </div>
        </div>
      </div>

      {/* Progress Bar - 시각적 막대바 */}
      {/* 상하 패딩 추가하여 말풍선 공간 확보 */}
      <div className="relative w-full py-8 mb-3">
        {/* 실제 막대바 컨테이너 */}
        <div className="relative w-full h-10 bg-slate-200 rounded-full overflow-visible">
          {/* 배경 그라데이션 (최저가에서 최고가로) */}
          <div
            className="absolute inset-0 bg-gradient-to-r from-blue-200 via-slate-200 to-red-200 rounded-full"
            style={{ width: '100%' }}
          />

          {/* 현재가 마커 - 점 표시 (막대바 중심에 절대 위치) */}
          <div
            className={`absolute rounded-full border-2 z-10 transition-all duration-300 ${
              isNewHigh
                ? 'w-5 h-5 bg-red-500 border-red-300 shadow-[0_0_12px_rgba(239,68,68,0.6)] animate-pulse'
                : isNewLow
                ? 'w-5 h-5 bg-blue-500 border-blue-300 shadow-[0_0_12px_rgba(59,130,246,0.6)]'
                : 'w-4 h-4 bg-slate-900 border-white shadow-lg'
            }`}
            style={{
              top: '50%',
              left: `${clampedPosition}%`,
              transform: 'translate(-50%, -50%)',
            }}
          >
          {/* 마커 위에 현재가 표시 - 위치 동적 조정 */}
          <div
            className="absolute -top-12 whitespace-nowrap transition-all duration-300"
            style={{
              left: '50%',
              transform: (() => {
                // 왼쪽 끝(10% 이하)에 가까우면 말풍선을 오른쪽으로 이동
                if (clampedPosition <= 10) {
                  return 'translateX(-10%)'
                }
                // 오른쪽 끝(90% 이상)에 가까우면 말풍선을 왼쪽으로 이동
                if (clampedPosition >= 90) {
                  return 'translateX(-90%)'
                }
                // 중간 위치에서는 중앙 정렬
                return 'translateX(-50%)'
              })(),
            }}
          >
            {/* 신고가/신저가 배지 */}
            {(isNewHigh || isNewLow) && (
              <div className={`mb-1 text-[10px] font-bold px-2 py-0.5 rounded-full ${
                isNewHigh
                  ? 'bg-red-500 text-white shadow-[0_0_8px_rgba(239,68,68,0.4)]'
                  : 'bg-blue-500 text-white shadow-[0_0_8px_rgba(59,130,246,0.4)]'
              }`}>
                {isNewHigh ? '🔥 신고가 돌파' : '❄️ 신저가'}
              </div>
            )}
            <div className={`text-white text-xs font-semibold px-2 py-1 rounded-md shadow-md ${
              isNewHigh
                ? 'bg-red-600'
                : isNewLow
                ? 'bg-blue-600'
                : 'bg-slate-900'
            }`}>
              {formatPrice(current, current_str)}
            </div>
            <div
              className={`w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent ${
                isNewHigh
                  ? 'border-t-red-600'
                  : isNewLow
                  ? 'border-t-blue-600'
                  : 'border-t-slate-900'
              }`}
              style={{
                marginLeft: (() => {
                  // 말풍선 위치에 따라 삼각형도 조정
                  if (clampedPosition <= 10) {
                    return '10%'
                  }
                  if (clampedPosition >= 90) {
                    return '90%'
                  }
                  return '50%'
                })(),
                transform: 'translateX(-50%)',
              }}
            ></div>
          </div>
        </div>
      </div>
      </div>

      {/* 위치 정보 텍스트 */}
      {isInRange && (
        <div className="text-center">
          <span className="text-xs sm:text-sm text-slate-600">
            현재가가 52주 범위의{' '}
            <span className="font-semibold text-slate-900">
              {clampedPosition.toFixed(1)}%
            </span>
            {' '}위치에 있습니다
          </span>
        </div>
      )}
      {isNewHigh && (
        <div className="text-center">
          <span className="text-xs sm:text-sm font-semibold text-red-600">
            🚀 52주 최고가를 {((current - high) / high * 100).toFixed(1)}% 돌파했습니다
          </span>
        </div>
      )}
      {isNewLow && (
        <div className="text-center">
          <span className="text-xs sm:text-sm font-semibold text-blue-600">
            📉 52주 최저가 대비 {((low - current) / low * 100).toFixed(1)}% 하락했습니다
          </span>
        </div>
      )}
    </div>
  )
}
