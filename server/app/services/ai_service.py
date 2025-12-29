from typing import Dict, Optional, Tuple
import openai
import json
import logging
from pydantic import BaseModel
from app.schemas.stock import AIAnalysisResponse, MetricInsights

logger = logging.getLogger(__name__)


class AIService:
    """
    OpenAI를 사용하여 주식 분석을 수행하는 서비스 클래스 (성능 최적화)

    최적화 포인트:
    - Structured Outputs 사용 (빠른 JSON 파싱)
    - temperature 0.2 (일관성 증가, 생성 속도 향상)
    - max_tokens 제한 (800) (불필요한 토큰 생성 방지)
    - 간소화된 프롬프트 (토큰 수 감소)
    - 단순화된 JSON 스키마 (metric_insights: 8개→4개 필드)
    """

    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        """
        AIService 초기화

        Args:
            api_key: OpenAI API 키
            model: 사용할 OpenAI 모델명
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model

        # 성능 최적화 설정
        self.temperature = 0.2  # 일관성↑, 속도↑
        self.max_tokens = 800  # 응답 길이 제한

    def _filter_payload(self, data: Dict) -> Dict:
        """
        OpenAI Payload에서 불필요한 값 제거하여 토큰 수 감소

        제거 대상:
        - None, null 값
        - 0 (숫자)
        - "정보 없음", "정보없음", "N/A", "" (문자열)

        Args:
            data: 원본 딕셔너리

        Returns:
            Dict: 필터링된 딕셔너리
        """
        filtered = {}

        for key, value in data.items():
            # None 값 제거
            if value is None:
                continue

            # 문자열 값 필터링
            if isinstance(value, str):
                # 공백 제거 후 비교
                value_stripped = value.strip()
                # "정보 없음", "정보없음", "N/A", 빈 문자열 제거
                if value_stripped in ["", "정보 없음", "정보없음", "N/A", "None", "null"]:
                    continue

            # 숫자 0 제거 (score는 유지)
            if isinstance(value, (int, float)) and value == 0 and key != "score":
                continue

            # 유효한 값만 추가
            filtered[key] = value

        logger.debug(f"[AIService] Payload 필터링: {len(data)} -> {len(filtered)} 필드 (감소: {len(data) - len(filtered)})")
        return filtered
    
    def analyze_stock(
        self,
        stock_data: Dict
    ) -> Optional[Dict]:
        """
        주식 데이터를 분석하여 AI 분석 결과를 반환합니다. (최적화)

        최적화:
        - Structured Outputs로 JSON 스키마 강제 (파싱 속도↑)
        - temperature 0.2 적용 (생성 속도↑)
        - max_tokens 800 제한 (불필요한 생성 방지)

        Args:
            stock_data: 주식 정보 딕셔너리

        Returns:
            Optional[Dict]: AI 분석 결과 딕셔너리 (실패 시 None)
        """
        if not stock_data:
            logger.warning("[AIService] stock_data가 비어있습니다.")
            return None

        # Payload 필터링 (토큰 수 감소)
        filtered_stock_data = self._filter_payload(stock_data)

        system_prompt, user_prompt = self._build_analysis_prompts(filtered_stock_data)

        try:
            # Structured Outputs 사용 (response_format에 스키마 명시)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "stock_analysis",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "properties": {
                                "signal": {
                                    "type": "string",
                                    "enum": ["매수", "중립", "주의"]
                                },
                                "one_line": {"type": "string"},
                                "summary": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "minItems": 3,
                                    "maxItems": 3
                                },
                                "risk": {"type": "string"},
                                "metric_insights": {
                                    "type": "object",
                                    "properties": {
                                        "valuation": {"type": "string"},
                                        "profitability": {"type": "string"},
                                        "dividend": {"type": "string"},
                                        "volatility": {"type": "string"}
                                    },
                                    "required": ["valuation", "profitability", "dividend", "volatility"],
                                    "additionalProperties": False
                                }
                            },
                            "required": ["signal", "one_line", "summary", "risk", "metric_insights"],
                            "additionalProperties": False
                        }
                    }
                },
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            result = json.loads(response.choices[0].message.content)

            # 백엔드에서 계산한 점수를 AI 응답에 추가
            backend_score = stock_data.get("score")
            if backend_score is not None:
                result["score"] = float(backend_score)
            else:
                # 점수가 없으면 기본값 50점
                result["score"] = 50.0
                logger.warning(f"[AIService] stock_data에 score가 없어 기본값 50.0 사용")

            logger.info(f"[AIService] 분석 완료: {stock_data.get('symbol', 'Unknown')}, score={result.get('score')}, 응답시간 최적화 적용")
            return result

        except Exception as e:
            logger.error(f"[AIService] AI 분석 중 오류 발생: {e}")
            return None
    
    def _build_analysis_prompts(self, stock_data: Dict) -> Tuple[str, str]:
        """
        AI 분석을 위한 시스템 프롬프트와 사용자 프롬프트를 생성합니다. (최적화)

        최적화:
        - system prompt 최소화 (핵심만 유지)
        - user prompt JSON 스키마 간소화 (8개→4개 필드)
        - 불필요한 설명 제거

        Args:
            stock_data: 주식 정보 딕셔너리

        Returns:
            Tuple[str, str]: (시스템 프롬프트, 사용자 프롬프트)
        """
        # 시스템 프롬프트: 극도로 간결화 (토큰↓)
        system_prompt = """시니어 펀드매니저로서 투자 분석 제공.
섹터 기준 평가, 핵심 리스크 1개, 캐주얼 한국어(~해, ~야, ~임), 마침표 없음."""

        # 사용자 프롬프트: 데이터 중심, 간결화 (토큰↓)
        sector = stock_data.get('sector', '정보 없음')
        industry = stock_data.get('industry', '정보 없음')
        backend_score = stock_data.get("score", 50.0)

        # 배당률 포맷팅
        dividend_yield_value = stock_data.get("dividend_yield")
        if isinstance(dividend_yield_value, (int, float)):
            dividend_yield_display = f"{float(dividend_yield_value):.2f}%"
        else:
            dividend_yield_display = "N/A"

        user_prompt = f"""{stock_data.get('name', 'N/A')} ({stock_data.get('symbol', 'N/A')})
현재가: {stock_data.get('current_price', 'N/A')}{stock_data.get('currency', '')} | 섹터: {sector} | 산업: {industry}
PER: {stock_data.get('pe_ratio', 'N/A')} | PBR: {stock_data.get('pb_ratio', 'N/A')} | ROE: {stock_data.get('roe', 'N/A')}%
EPS: {stock_data.get('eps', 'N/A')} | 배당: {dividend_yield_display} | Beta: {stock_data.get('beta', 'N/A')}
목표가: {stock_data.get('target_mean_price', 'N/A')} | 점수: {backend_score}

JSON:
- signal: 매수(≥70), 중립(50-69), 주의(<50)
- one_line: 핵심 한줄
- summary: [3개 포인트]
- risk: 주요 리스크 1개
- metric_insights:
  * valuation: PER/PBR 종합평가
  * profitability: ROE/EPS 수익성
  * dividend: 배당 평가
  * volatility: Beta/목표가 해석"""

        return system_prompt, user_prompt

