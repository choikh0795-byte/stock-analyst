import React from 'react'

interface PriceRangeBarProps {
  current: number
  low: number | null | undefined
  high: number | null | undefined
}

/**
 * 52주 가격 범위를 시각적으로 표시하는 Progress Bar 컴포넌트
 */
export const PriceRangeBar: React.FC<PriceRangeBarProps> = ({
  current,
  low,
  high,
}) => {
  // 데이터가 없으면 표시하지 않음
  if (!low || !high || low >= high) {
    return null
  }

  // 범위 계산 (52주 최저가와 최고가 기준)
  const range = high - low

  // 현재가의 위치를 퍼센트로 계산 (0~100%)
  // 현재가가 범위를 벗어나도 표시 가능하도록 계산
  let position: number
  if (current <= low) {
    position = 0
  } else if (current >= high) {
    position = 100
  } else {
    position = ((current - low) / range) * 100
  }

  // 현재가가 범위 내에 있는지 확인
  const isInRange = current >= low && current <= high

  return (
    <div className="w-full">
      {/* 라벨: 최저가, 현재가, 최고가 */}
      <div className="flex justify-between items-center mb-4">
        <div className="text-left">
          <div className="text-xs text-slate-500 mb-1">52주 최저</div>
          <div className="text-sm sm:text-base font-semibold text-slate-700">
            ${low.toFixed(2)}
          </div>
        </div>
        <div className="text-center flex-1 mx-4">
          <div className="text-xs text-slate-500 mb-1">현재가</div>
          <div className="text-base sm:text-lg font-bold text-slate-900">
            ${current.toFixed(2)}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-slate-500 mb-1">52주 최고</div>
          <div className="text-sm sm:text-base font-semibold text-slate-700">
            ${high.toFixed(2)}
          </div>
        </div>
      </div>

      {/* Progress Bar - 시각적 막대바 */}
      {/* 상하 좌우 패딩 추가하여 말풍선 공간 확보 */}
      <div className="relative w-full py-8 px-2 mb-3">
        {/* 실제 막대바 컨테이너 */}
        <div className="relative w-full h-10 bg-slate-200 rounded-full overflow-hidden">
          {/* 배경 그라데이션 (최저가에서 최고가로) */}
          <div
            className="absolute inset-0 bg-gradient-to-r from-blue-200 via-slate-200 to-red-200"
            style={{ width: '100%' }}
          />
        </div>

        {/* 현재가 마커 - 점 표시 (막대바 중앙에 절대 위치) */}
        <div
          className="absolute w-4 h-4 bg-slate-900 rounded-full border-2 border-white shadow-lg z-10 transition-all duration-300"
          style={{
            top: 'calc(2rem + 1.25rem)', // py-8 패딩(2rem) + 막대바 높이의 절반(h-10/2 = 1.25rem)
            left: `calc(0.5rem + ${Math.max(0, Math.min(100, position))}% - 8px)`, // px-2 패딩(0.5rem) + position% - 마커 반너비(8px)
            transform: 'translateY(-50%)',
          }}
        >
          {/* 마커 위에 현재가 표시 - 위치 동적 조정 */}
          <div
            className="absolute -top-8 whitespace-nowrap transition-all duration-300"
            style={{
              left: '50%',
              transform: (() => {
                // 왼쪽 끝(10% 이하)에 가까우면 말풍선을 오른쪽으로 이동
                if (position <= 10) {
                  return 'translateX(-10%)'
                }
                // 오른쪽 끝(90% 이상)에 가까우면 말풍선을 왼쪽으로 이동
                if (position >= 90) {
                  return 'translateX(-90%)'
                }
                // 중간 위치에서는 중앙 정렬
                return 'translateX(-50%)'
              })(),
            }}
          >
            <div className="bg-slate-900 text-white text-xs font-semibold px-2 py-1 rounded-md shadow-md">
              ${current.toFixed(2)}
            </div>
            <div
              className="w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-slate-900"
              style={{
                marginLeft: (() => {
                  // 말풍선 위치에 따라 삼각형도 조정
                  if (position <= 10) {
                    return '10%'
                  }
                  if (position >= 90) {
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

      {/* 위치 정보 텍스트 */}
      {isInRange && (
        <div className="text-center">
          <span className="text-xs sm:text-sm text-slate-600">
            현재가가 52주 범위의{' '} 
            <span className="font-semibold text-slate-900">
              {position.toFixed(1)}%
            </span>
             위치에 있습니다
          </span>
        </div>
      )}
      {!isInRange && (
        <div className="text-center">
          <span className="text-xs sm:text-sm text-slate-600 font-medium">
            {current < low ? '52주 최저가 이하' : '52주 최고가 이상'}
          </span>
        </div>
      )}
    </div>
  )
}
