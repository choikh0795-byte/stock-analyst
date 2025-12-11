import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  StockAnalysisRequest,
  StockAnalysisResponse,
  StockInfo
} from '../types/stock'

/**
 * StockApiClient - Singleton Pattern으로 구현된 주식 API 클라이언트
 * 모든 API 호출은 이 클래스를 통해서만 이루어집니다.
 */
class StockApiClient {
  private static instance: StockApiClient | null = null
  private axiosInstance: AxiosInstance
  private readonly baseURL: string

  private constructor(baseURL: string = 'http://localhost:8000') {
    this.baseURL = baseURL
    this.axiosInstance = axios.create({
      baseURL,
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
}

// Singleton 인스턴스 export
export const stockApi = StockApiClient.getInstance()

