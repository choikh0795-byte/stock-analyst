import React from 'react'
import { X } from 'lucide-react'
import { useUpdateLogStore } from '../stores/useUpdateLogStore'
import type { UpdateLog } from '../types/stock'

const formatDate = (iso: string): string => {
  const d = new Date(iso)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}.${m}.${day}`
}

const Badge: React.FC<{ label: string }> = ({ label }) => (
  <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 text-xs font-medium text-slate-700">
    {label}
  </span>
)

const TimelineItem: React.FC<{ log: UpdateLog }> = ({ log }) => {
  const contentLines = log.content.split('\\n')

  return (
    <div className="relative pb-6 pl-8">
      <span className="absolute left-[11px] top-1 h-full w-px bg-slate-200 last:hidden" aria-hidden />
      <span className="absolute left-0 top-1.5 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border-2 border-indigo-500 bg-white" />
      <div className="flex flex-col gap-2 rounded-lg bg-white/60 px-3 py-2 shadow-[0_1px_3px_rgba(0,0,0,0.04)] ring-1 ring-slate-100">
        <div className="flex flex-wrap items-center gap-2">
          <p className="text-sm font-semibold text-slate-900">{formatDate(log.created_at)}</p>
          <Badge label={log.category} />
          {log.version && (
            <span className="text-xs text-slate-500">v{log.version}</span>
          )}
        </div>
        <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
          {contentLines.map((line, index) => (
            <span key={index}>
              {line}
              {index < contentLines.length - 1 && <br />}
            </span>
          ))}
        </p>
      </div>
    </div>
  )
}

const SkeletonItem: React.FC = () => (
  <div className="relative pb-6 pl-8">
    <span className="absolute left-[11px] top-1 h-full w-px bg-slate-200 last:hidden" aria-hidden />
    <span className="absolute left-0 top-1.5 inline-flex h-3.5 w-3.5 items-center justify-center rounded-full border-2 border-indigo-200 bg-white" />
    <div className="flex flex-col gap-2 rounded-lg bg-white/60 px-3 py-2 shadow-[0_1px_3px_rgba(0,0,0,0.04)] ring-1 ring-slate-100">
      <div className="flex items-center gap-2">
        <div className="h-4 w-24 animate-pulse rounded bg-slate-200" />
        <div className="h-5 w-16 animate-pulse rounded-full bg-slate-200" />
        <div className="h-3 w-10 animate-pulse rounded bg-slate-200" />
      </div>
      <div className="h-12 w-full animate-pulse rounded bg-slate-200" />
    </div>
  </div>
)

export const UpdateLogModal: React.FC = () => {
  const { isOpen, logs, isLoading, closeModal } = useUpdateLogStore()

  if (!isOpen) return null

  const renderContent = () => {
    if (isLoading) {
      return (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, idx) => (
            <SkeletonItem key={idx} />
          ))}
        </div>
      )
    }

    if (!logs.length) {
      return (
        <div className="rounded-lg border border-dashed border-slate-200 bg-slate-50 px-4 py-6 text-center text-sm text-slate-500">
          아직 등록된 업데이트 로그가 없습니다.
        </div>
      )
    }

    return (
      <div className="space-y-3">
        {logs.map((log) => (
          <TimelineItem key={log.id} log={log} />
        ))}
      </div>
    )
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 backdrop-blur-[2px] transition"
      onClick={closeModal}
    >
      <div
        className="relative w-full max-w-2xl rounded-t-2xl bg-white shadow-2xl ring-1 ring-black/5 transition-all md:my-10 md:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-900">서비스 업데이트 노트</h2>
          <button
            type="button"
            onClick={closeModal}
            aria-label="닫기"
            className="flex h-9 w-9 items-center justify-center rounded-full text-slate-500 transition hover:bg-slate-100 hover:text-slate-700"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="max-h-[70vh] overflow-y-auto px-5 py-4 md:max-h-[75vh] md:px-6 md:py-5">
          {renderContent()}
        </div>
      </div>
    </div>
  )
}

export default UpdateLogModal

