import React from 'react'
import { motion } from 'framer-motion'
import { Search, Database, Bot, CheckCircle2, Loader2, AlertCircle, XCircle } from 'lucide-react'
import type { ProgressStep } from '../types/stock'

interface ProgressTrackerProps {
  steps: ProgressStep[]
  currentStepIndex: number
}

// Lucide 아이콘 매핑
const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Search,
  Database,
  Bot,
  CheckCircle2,
}

/**
 * 분석 진행 상황을 표시하는 컴포넌트
 * 각 단계별 아이콘과 상태를 애니메이션과 함께 보여줍니다.
 */
export const ProgressTracker: React.FC<ProgressTrackerProps> = ({ steps, currentStepIndex }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className="w-full max-w-2xl mx-auto mb-6"
    >
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 md:p-6">
        <div className="flex flex-col space-y-3">
          {steps.map((step, index) => {
            const IconComponent = iconMap[step.icon]
            const isActive = index === currentStepIndex
            const isCompleted = step.status === 'completed'
            const isError = step.status === 'error'
            const isPending = step.status === 'pending'
            const isInProgress = step.status === 'in_progress'

            return (
              <motion.div
                key={step.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center space-x-4"
              >
                {/* 아이콘 */}
                <div
                  className={`
                    flex items-center justify-center w-10 h-10 rounded-full shrink-0 transition-all duration-300
                    ${isCompleted ? 'bg-green-100' : ''}
                    ${isInProgress ? 'bg-blue-100' : ''}
                    ${isError ? 'bg-red-100' : ''}
                    ${isPending ? 'bg-gray-100' : ''}
                  `}
                >
                  {isError && (
                    <XCircle className="w-5 h-5 text-red-600" />
                  )}
                  {isInProgress && (
                    <Loader2 className="w-5 h-5 text-blue-600 animate-spin" />
                  )}
                  {isCompleted && (
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                  )}
                  {isPending && IconComponent && (
                    <IconComponent className="w-5 h-5 text-gray-400" />
                  )}
                </div>

                {/* 단계 정보 */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <h4
                      className={`
                        text-sm font-semibold transition-colors
                        ${isCompleted ? 'text-green-700' : ''}
                        ${isInProgress ? 'text-blue-700' : ''}
                        ${isError ? 'text-red-700' : ''}
                        ${isPending ? 'text-gray-400' : ''}
                      `}
                    >
                      {step.label}
                    </h4>
                    {isInProgress && (
                      <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="flex space-x-1"
                      >
                        <motion.div
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ duration: 1.5, repeat: Infinity, delay: 0 }}
                          className="w-1.5 h-1.5 bg-blue-500 rounded-full"
                        />
                        <motion.div
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ duration: 1.5, repeat: Infinity, delay: 0.2 }}
                          className="w-1.5 h-1.5 bg-blue-500 rounded-full"
                        />
                        <motion.div
                          animate={{ opacity: [0.3, 1, 0.3] }}
                          transition={{ duration: 1.5, repeat: Infinity, delay: 0.4 }}
                          className="w-1.5 h-1.5 bg-blue-500 rounded-full"
                        />
                      </motion.div>
                    )}
                  </div>
                  {(isInProgress || isCompleted) && step.message && (
                    <motion.p
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      exit={{ opacity: 0, height: 0 }}
                      className={`
                        text-xs mt-1 transition-colors
                        ${isCompleted ? 'text-gray-600' : 'text-gray-500'}
                      `}
                    >
                      {step.message}
                    </motion.p>
                  )}
                </div>

                {/* 상태 배지 (완료된 단계만) */}
                {isCompleted && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="px-2 py-1 bg-green-50 text-green-700 text-xs font-medium rounded-md"
                  >
                    완료
                  </motion.div>
                )}
              </motion.div>
            )
          })}
        </div>

        {/* 전체 진행률 바 */}
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-medium text-gray-600">전체 진행률</span>
            <span className="text-xs font-semibold text-blue-600">
              {Math.round((currentStepIndex / steps.length) * 100)}%
            </span>
          </div>
          <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              animate={{ width: `${(currentStepIndex / steps.length) * 100}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              className="h-full bg-gradient-to-r from-blue-500 to-blue-600 rounded-full"
            />
          </div>
        </div>
      </div>
    </motion.div>
  )
}
