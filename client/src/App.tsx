import React from 'react'
import { StockAnalysisPage } from './pages/StockAnalysisPage'
import { useStockStore } from './store/useStockStore'
import './App.css'

/**
 * 메인 App 컴포넌트
 * 레이아웃 전환 애니메이션 및 전역 설정을 담당합니다.
 */
function App() {
  const hasSearched = useStockStore((state) => state.hasSearched)

  return (
    <div
      className={`min-h-screen transition-all duration-500 ease-in-out ${
        hasSearched
          ? 'flex flex-col justify-start pt-10'
          : 'flex flex-col justify-center items-center pb-36'
      }`}
    >
      <StockAnalysisPage />
    </div>
  )
}

export default App

