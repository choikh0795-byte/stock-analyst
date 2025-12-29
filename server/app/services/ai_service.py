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
        self.temperature = 0.6  # 자연스러운 톤 + 일관성 유지
        self.max_tokens = 600  # 응답 길이 제한 (충분한 길이)

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
                                        "per": {"type": "string"},
                                        "pbr": {"type": "string"},
                                        "roe": {"type": "string"},
                                        "eps": {"type": "string"},
                                        "debt_ratio": {"type": "string"},
                                        "target_gap": {"type": "string"}
                                    },
                                    "required": ["per", "pbr", "roe", "eps", "debt_ratio", "target_gap"],
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
        AI 분석을 위한 시스템 프롬프트와 사용자 프롬프트를 생성합니다.

        최적화:
        - 토큰 50% 절감 (간소화된 프롬프트)
        - 자연스러운 톤 (친근한 페르소나)
        - 지표별 독립 분석 유지

        Args:
            stock_data: 주식 정보 딕셔너리

        Returns:
            Tuple[str, str]: (시스템 프롬프트, 사용자 프롬프트)
        """
        # 시스템 프롬프트: 간결하고 친근한 톤
        system_prompt = """너는 10년차 펀드매니저야. 친근하고 솔직한 톤으로 투자 분석을 제공해.
각 지표는 서로 다른 관점이니 개별적으로 분석해줘.
섹터 평균 고려하고, 주요 리스크 1개만 명시해.
한국어 반말(~해, ~야, ~임) 사용하고 마침표 없이 작성해."""

        # 데이터 추출
        sector = stock_data.get('sector', '정보없음')
        industry = stock_data.get('industry', '정보없음')
        backend_score = stock_data.get("score", 50.0)

        per = stock_data.get('pe_ratio', 'N/A')
        pbr = stock_data.get('pb_ratio', 'N/A')
        roe = stock_data.get('roe', 'N/A')
        eps = stock_data.get('eps', 'N/A')
        debt_ratio = stock_data.get('debt_ratio', 'N/A')
        target_mean = stock_data.get('target_mean_price', 'N/A')
        current_price = stock_data.get('current_price', 'N/A')
        currency = stock_data.get('currency', '')

        # 목표가 괴리율
        target_gap = stock_data.get('target_upside', 'N/A')
        if target_gap != 'N/A' and target_gap is not None:
            target_gap = f"{target_gap:.1f}%"

        # 사용자 프롬프트: 간소화 (불필요한 구분선/설명 제거)
        user_prompt = f"""{stock_data.get('name', 'N/A')} ({stock_data.get('symbol', 'N/A')})
가격 {current_price}{currency} | 섹터 {sector} | 산업 {industry} | 점수 {backend_score}

지표:
PER {per}, PBR {pbr}, ROE {roe}%, EPS {eps}
부채비율 {debt_ratio}%, 목표가 {target_mean} (괴리율 {target_gap})

분석 요구사항:
1. signal: 매수(≥70), 중립(50-69), 주의(<50)
2. one_line: 핵심 한줄 요약
3. summary: 3개 포인트
4. risk: 주요 리스크 1개
5. metric_insights: 각 지표별 독립 분석 (PER, PBR, ROE, EPS, 부채비율, 목표가 괴리율)"""

        return system_prompt, user_prompt

