import React from 'react'
import './Loading.css'

interface LoadingProps {
  ticker: string
}

/**
 * 로딩 상태 표시 컴포넌트
 */
export const Loading: React.FC<LoadingProps> = ({ ticker }) => {
  return (
    <div className="loading">
      {/* 🔍 '{ticker}' 데이터를 분석하고 있습니다... */}
    </div>
  )
}

