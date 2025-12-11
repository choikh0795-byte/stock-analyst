import React from 'react'
import './ErrorMessage.css'

interface ErrorMessageProps {
  message: string
}

/**
 * 에러 메시지 표시 컴포넌트
 */
export const ErrorMessage: React.FC<ErrorMessageProps> = ({ message }) => {
  return (
    <div className="error-message">
      ❌ {message}
    </div>
  )
}

