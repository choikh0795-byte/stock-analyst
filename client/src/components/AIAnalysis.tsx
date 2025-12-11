import React from 'react'
import type { AIAnalysis } from '../types/stock'
import { getSignalColor } from '../utils/stockUtils'
import './AIAnalysis.css'

interface AIAnalysisProps {
  analysis: AIAnalysis
}

/**
 * AI 분석 결과 표시 컴포넌트
 */
export const AIAnalysis: React.FC<AIAnalysisProps> = ({ analysis }) => {
  const signalColor = getSignalColor(analysis.signal)

  return (
    <div className="ai-analysis">
      <h3>
        🤖 AI 투자 점수: <span style={{ color: signalColor }}>{analysis.score}점</span>
      </h3>

      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{
            width: `${analysis.score}%`,
            backgroundColor: signalColor,
          }}
        />
      </div>

      <div className="one-line-summary">
        💡 <strong>한 줄 요약:</strong> {analysis.one_line}
      </div>

      <div className="analysis-details">
        <div className="analysis-column">
          <h4>✅ 투자 포인트</h4>
          <ul>
            {analysis.summary.map((point, index) => (
              <li key={index}>{point}</li>
            ))}
          </ul>
        </div>

        <div className="analysis-column">
          <h4>⚠️ 리스크 요인</h4>
          <ul>
            <li>{analysis.risk}</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

