import React from 'react'
import type { StockInfo } from '../types/stock'
import { calculatePriceChange } from '../utils/stockUtils'
import './StockInfo.css'

interface StockInfoProps {
  data: StockInfo
}

/**
 * 주식 기본 정보 표시 컴포넌트
 */
export const StockInfo: React.FC<StockInfoProps> = ({ data }) => {
  const priceChange = calculatePriceChange(data.current_price, data.previous_close)
  const isPositive = priceChange.value >= 0

  return (
    <div className="stock-info">
      <h2>
        {data.name} ({data.symbol})
      </h2>

      <div className="metrics">
        <div className="metric-card">
          <div className="metric-label">현재가</div>
          <div className="metric-value">
            ${data.current_price}
            {data.current_price !== data.previous_close && (
              <span className={`delta ${isPositive ? 'positive' : 'negative'}`}>
                {isPositive ? '+' : ''}
                {priceChange.value.toFixed(2)} ({priceChange.percentage.toFixed(2)}%)
              </span>
            )}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">PER</div>
          <div className="metric-value">{data.pe_ratio || 'N/A'}</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">섹터</div>
          <div className="metric-value">{data.sector}</div>
        </div>
      </div>
    </div>
  )
}

