from typing import Dict, Optional, Tuple
import openai
import json
import logging

logger = logging.getLogger(__name__)


class AIService:
    """
    OpenAI를 사용하여 주식 분석을 수행하는 서비스 클래스
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
        주식 데이터를 분석하여 AI 분석 결과를 반환합니다.

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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": system_prompt
                    },
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
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
            
            logger.info(f"[AIService] 분석 완료: {stock_data.get('symbol', 'Unknown')}, score={result.get('score')}")
            return result
            
        except Exception as e:
            logger.error(f"[AIService] AI 분석 중 오류 발생: {e}")
            return None
    
    def _build_analysis_prompts(self, stock_data: Dict) -> Tuple[str, str]:
        """
        AI 분석을 위한 시스템 프롬프트와 사용자 프롬프트를 생성합니다.
        
        Args:
            stock_data: 주식 정보 딕셔너리
            
        Returns:
            Tuple[str, str]: (시스템 프롬프트, 사용자 프롬프트)
        """
        # 시스템 프롬프트: 간결하고 핵심적인 지시사항
        system_prompt = """You are a senior fund manager providing sharp investment analysis.

Guidelines:
- Analyze metrics in sector/industry context
- Identify risks (value traps, dividend traps, leverage effects)
- Use casual Korean tone (~해, ~야, ~임), no periods
- Provide real-world insights, not textbook definitions

Output valid JSON only."""

        # 사용자 프롬프트: 구체적인 데이터와 컨텍스트
        # 시가총액 포맷팅 (market_cap은 문자열로 전달되므로 숫자로 변환)
        market_cap_str_value = stock_data.get('market_cap')
        market_cap_display = stock_data.get('market_cap_str', '정보 없음')
        
        # 문자열을 숫자로 변환하여 컨텍스트 생성
        try:
            market_cap_numeric = float(market_cap_str_value) if market_cap_str_value else None
        except (ValueError, TypeError):
            market_cap_numeric = None
        
        if market_cap_numeric:
            if market_cap_numeric >= 1_000_000_000_000:  # 1조 이상
                market_cap_context = f"{market_cap_numeric / 1_000_000_000_000:.2f}조원 규모"
            elif market_cap_numeric >= 1_000_000_000:  # 10억 이상
                market_cap_context = f"{market_cap_numeric / 1_000_000_000:.2f}억원 규모"
            else:
                market_cap_context = f"{market_cap_numeric:,.0f}원 규모"
        else:
            market_cap_context = "정보 없음"
        
        sector = stock_data.get('sector', '정보 없음')
        industry = stock_data.get('industry', '정보 없음')
        
        # 백엔드에서 계산한 점수
        backend_score = stock_data.get("score", 50.0)

        # 배당률은 백엔드에서 이미 퍼센트 값(예: 0.11%)으로 전달되므로,
        # 프롬프트에도 퍼센트 문자열로 고정해 LLM이 100을 추가로 곱하지 않도록 한다.
        dividend_yield_value = stock_data.get("dividend_yield")
        if isinstance(dividend_yield_value, (int, float)):
            dividend_yield_display = f"{float(dividend_yield_value):.2f}%"
        elif dividend_yield_value is None:
            dividend_yield_display = "N/A"
        else:
            dividend_yield_display = f"{dividend_yield_value} (퍼센트)"
        
        user_prompt = f"""분석 종목: {stock_data.get('name', 'N/A')} ({stock_data.get('symbol', 'N/A')})
현재가: {stock_data.get('current_price', 'N/A')} {stock_data.get('currency', '')}
섹터: {sector} | 산업: {industry} | 시총: {market_cap_display}

재무지표:
PER: {stock_data.get('pe_ratio', 'N/A')} | PBR: {stock_data.get('pb_ratio', 'N/A')} | ROE: {stock_data.get('roe', 'N/A')}%
EPS: {stock_data.get('eps', 'N/A')} | 배당: {dividend_yield_display} | Beta: {stock_data.get('beta', 'N/A')}
목표가: {stock_data.get('target_mean_price', 'N/A')} | 종합점수: {backend_score}점

JSON 형식으로 응답:
{{
    "signal": ("매수"[score≥70], "중립"[50≤score<70], "주의"[score<50]),
    "one_line": "핵심 코멘트 (마침표 없음)",
    "summary": ["포인트1", "포인트2", "포인트3"],
    "risk": "주요 리스크 1가지",
    "metric_insights": {{
        "pe_ratio": "섹터 맥락 고려한 평가 (null이면 '데이터 없음')",
        "pb_ratio": "섹터 맥락 고려한 평가",
        "return_on_equity": "레버리지 효과 고려한 평가",
        "roe": "return_on_equity와 동일",
        "eps": "성장 추세 평가",
        "dividend_yield": "배당 함정 여부 평가 (이미 % 단위)",
        "beta": "변동성 해석",
        "target_mean_price": "상승 여력 평가"
    }}
}}"""
        
        return system_prompt, user_prompt

