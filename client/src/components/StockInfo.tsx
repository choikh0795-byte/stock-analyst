import React from 'react'
import type { StockInfo } from '../types/stock'
import './StockInfo.css'

interface StockInfoProps {
  data: StockInfo
}

/**
 * 주식 기본 정보 표시 컴포넌트
 */
export const StockInfo: React.FC<StockInfoProps> = ({ data }) => {
  const isPositive = data.change_status === 'RISING'

  return (
    <div className="stock-info">
      <h2>
        {data.name} ({data.symbol})
      </h2>

      <div className="metrics">
        <div className="metric-card">
          <div className="metric-label">현재가</div>
          <div className="metric-value">
            {data.current_price_str || '-'}
            {data.change_value !== null && data.change_value !== undefined && data.change_value !== 0 && (
              <span className={`delta ${isPositive ? 'positive' : 'negative'}`}>
                {data.change_value_str || '-'} ({data.change_percentage_str || '-'})
              </span>
            )}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">PER</div>
          <div className="metric-value">{data.pe_ratio_str || 'N/A'}</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">섹터</div>
          <div className="metric-value">{data.sector}</div>
        </div>
      </div>
    </div>
  )
}

