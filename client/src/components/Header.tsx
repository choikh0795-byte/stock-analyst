import React from 'react'
import { useStockStore } from '../store/useStockStore'
import './Header.css'

/**
 * 페이지 헤더 컴포넌트
 */
export const Header: React.FC = () => {
  const hasSearched = useStockStore((state) => state.hasSearched)

  return (
    <header
      className={`transition-all duration-500 ease-in-out text-center ${
        hasSearched ? 'scale-75 mb-4' : 'mb-8'
      }`}
    >
      <h1 className="text-5xl sm:text-7xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-900 to-slate-600 mb-2 pb-2 leading-normal">
        Stock Insight
      </h1>
      <p className="text-lg sm:text-xl text-slate-600 font-light">
        복잡한 주식 정보, 3초 만에 핵심만
      </p>
      {hasSearched && (
        <p className="subtitle text-base text-slate-600 mt-2">
          개발자 블로그:{' '}
          <a
            href="https://blog.naver.com/cjhol2107"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 underline hover:text-blue-700 transition-colors"
          >
            https://blog.naver.com/cjhol2107
          </a>
        </p>
      )}
    </header>
  )
}

