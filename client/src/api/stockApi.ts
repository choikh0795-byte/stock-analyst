import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  StockAnalysisRequest,
  StockAnalysisResponse,
  StockInfo,
  UpdateLog,
} from '../types/stock'

/**
 * StockApiClient - Singleton Pattern으로 구현된 주식 API 클라이언트
 * 모든 API 호출은 이 클래스를 통해서만 이루어집니다.
 */
class StockApiClient {
  private static instance: StockApiClient | null = null
  private axiosInstance: AxiosInstance
  private readonly baseURL: string

  private constructor(baseURL?: string) {
    // 환경변수에서 API URL 가져오기, 없으면 로컬 주소 사용
    this.baseURL = baseURL || import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    this.axiosInstance = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // 요청 인터셉터
    this.axiosInstance.interceptors.request.use(
      (config) => {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => {
        console.error('[API Request Error]', error)
        return Promise.reject(error)
      }
    )

    // 응답 인터셉터
    this.axiosInstance.interceptors.response.use(
      (response) => {
        console.log(`[API Response] ${response.status} ${response.config.url}`)
        return response
      },
      (error: AxiosError) => {
        console.error('[API Response Error]', error)
        return Promise.reject(error)
      }
    )
  }

  /**
   * Singleton 인스턴스 반환
   */
  public static getInstance(baseURL?: string): StockApiClient {
    if (!StockApiClient.instance) {
      StockApiClient.instance = new StockApiClient(baseURL)
    }
    return StockApiClient.instance
  }

  /**
   * 주식 정보 조회
   * @param ticker 주식 티커 심볼
   * @returns 주식 정보와 뉴스
   */
  async getStockInfo(ticker: string): Promise<{ stock_data: StockInfo; news: string[] }> {
    try {
      const response = await this.axiosInstance.get<{
        stock_data: StockInfo
        news: string[]
      }>(`/api/v1/stock/${ticker.toUpperCase()}`)
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || '주식 정보를 가져오는 중 오류가 발생했습니다.'
        )
      }
      throw error
    }
  }

  /**
   * 주식 분석 (정보 + AI 분석)
   * @param request 분석 요청 데이터
   * @returns 주식 정보, 뉴스, AI 분석 결과
   */
  async getStockAnalysis(
    request: StockAnalysisRequest
  ): Promise<StockAnalysisResponse> {
    try {
      const response = await this.axiosInstance.post<StockAnalysisResponse>(
        '/api/v1/stock/analyze',
        {
          ticker: request.ticker.toUpperCase(),
        }
      )
      // 디버그 로그: 백엔드 응답 원본 확인
      console.info('[StockApi][Response] /analyze stock_data', {
        roe: response.data?.stock_data?.roe,
        roe_str: response.data?.stock_data?.roe_str,
        return_on_equity: response.data?.stock_data?.return_on_equity,
        eps: response.data?.stock_data?.eps,
        eps_str: response.data?.stock_data?.eps_str,
        beta: response.data?.stock_data?.beta,
      })
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || '주식 분석 중 오류가 발생했습니다.'
        )
      }
      throw error
    }
  }

  /**
   * AI 분석만 수행
   * @param request 분석 요청 데이터
   * @returns AI 분석 결과
   */
  async getAIAnalysis(request: StockAnalysisRequest) {
    try {
      const response = await this.axiosInstance.post(
        '/api/v1/stock/analyze-ai',
        {
          ticker: request.ticker.toUpperCase(),
        }
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || 'AI 분석 중 오류가 발생했습니다.'
        )
      }
      throw error
    }
  }

  /**
   * 종목명이나 기업명을 티커로 변환
   * @param query 검색어 (한글 종목명, 기업명, 티커 모두 가능)
   * @returns 변환된 티커
   */
  async searchTicker(query: string): Promise<{ ticker: string; name?: string }> {
    try {
      const response = await this.axiosInstance.post<{ ticker: string; name?: string }>(
        '/api/v1/stock/search',
        { query: query.trim() }
      )
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail || '티커 검색 중 오류가 발생했습니다.'
        )
      }
      throw error
    }
  }

  /**
   * 업데이트 로그 조회
   * @returns 업데이트 로그 목록
   */
  async fetchUpdateLogs(): Promise<UpdateLog[]> {
    try {
      const response = await this.axiosInstance.get<UpdateLog[]>('/api/updates')
      return response.data
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(
          error.response?.data?.detail ||
            '업데이트 로그를 가져오는 중 오류가 발생했습니다.'
        )
      }
      throw error
    }
  }
}

// Singleton 인스턴스 export
export const stockApi = StockApiClient.getInstance()

