import React from 'react'
import { useStockStore } from '../store/useStockStore'
import { useUpdateLogStore } from '../stores/useUpdateLogStore'
import './Header.css'

/**
 * 페이지 헤더 컴포넌트
 */
export const Header: React.FC = () => {
  const hasSearched = useStockStore((state) => state.hasSearched)
  const openUpdateModal = useUpdateLogStore((state) => state.openModal)

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
        <div className="subtitle mt-3 flex flex-wrap items-center justify-center gap-3 text-sm text-slate-600">
          <span className="flex items-center gap-1">
            <span className="text-base">개발자 블로그:</span>
            <a
              href="https://blog.naver.com/cjhol2107"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 underline hover:text-blue-700 transition-colors"
            >
              https://blog.naver.com/cjhol2107
            </a>
          </span>
          <button
            type="button"
            onClick={openUpdateModal}
            className="flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1 text-[13px] font-medium text-indigo-700 transition hover:border-indigo-200 hover:bg-indigo-100"
          >
            <span className="inline-flex h-2.5 w-2.5 rounded-full bg-indigo-500" aria-hidden />
            업데이트
            <span className="rounded-full bg-indigo-600 px-1.5 py-0.5 text-[11px] font-semibold text-white">
              New
            </span>
          </button>
        </div>
      )}
    </header>
  )
}

