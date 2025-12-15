from typing import Dict, List, Optional, Tuple
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
    
    def analyze_stock(
        self, 
        stock_data: Dict, 
        news: List[str]
    ) -> Optional[Dict]:
        """
        주식 데이터를 분석하여 AI 분석 결과를 반환합니다.
        
        Args:
            stock_data: 주식 정보 딕셔너리
            news: 뉴스 헤드라인 리스트
            
        Returns:
            Optional[Dict]: AI 분석 결과 딕셔너리 (실패 시 None)
        """
        if not stock_data:
            logger.warning("[AIService] stock_data가 비어있습니다.")
            return None

        system_prompt, user_prompt = self._build_analysis_prompts(stock_data, news)

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
    
    def _build_analysis_prompts(self, stock_data: Dict, news: List[str]) -> Tuple[str, str]:
        """
        AI 분석을 위한 시스템 프롬프트와 사용자 프롬프트를 생성합니다.
        
        Args:
            stock_data: 주식 정보 딕셔너리
            news: 뉴스 헤드라인 리스트
            
        Returns:
            Tuple[str, str]: (시스템 프롬프트, 사용자 프롬프트)
        """
        # 시스템 프롬프트: 20년 경력 펀드매니저 페르소나
        system_prompt = """You are a Senior Portfolio Manager with 20 years of experience in equity analysis and fund management. 
Your role is to provide insightful, sharp, and professional investment analysis.

[Your Persona]
- You have deep expertise in fundamental analysis, sector comparisons, and risk assessment
- You are friendly but sharp - you don't sugarcoat risks, but you explain them clearly
- You see beyond the numbers and identify what's really happening behind the scenes
- You always consider sector/industry context when evaluating metrics
- You warn about potential traps (value traps, dividend traps, leverage effects, etc.)

[Your Analysis Style]
- Always compare metrics against sector/industry averages when possible
- Identify the "why" behind the numbers, not just the "what"
- Point out risks and potential pitfalls that casual investors might miss
- Use a friendly but professional tone - approachable but authoritative
- Never use textbook definitions - provide real-world insights
- Never end sentences with periods (.) - use casual Korean endings like "~해", "~야", "~임"

[Critical Analysis Guidelines]

**PER (Price-to-Earnings Ratio)**
- Low PER: Could be undervalued, BUT also check if it's a value trap (stagnant growth, declining earnings)
- High PER: Could be overvalued, BUT also check if premium is justified by strong growth prospects
- Always compare to sector average (e.g., tech stocks typically have higher PER than utilities)

**ROE (Return on Equity)**
- High ROE: Good, BUT check if it's driven by excessive leverage (debt) rather than operational efficiency
- Low ROE: Poor, but consider if it's a temporary downturn or structural issue
- Compare to industry peers and historical trends

**Dividend Yield**
- High yield: Attractive, BUT beware of dividend traps (high yield due to falling stock price, unsustainable payout)
- Low yield: Not necessarily bad if company reinvests for growth
- Check payout ratio and sustainability

**EPS (Earnings Per Share)**
- Not just the number, but the trend: Is it consistently growing?
- Compare to sector growth rates
- Watch for one-time gains that inflate EPS

**PBR (Price-to-Book Ratio)**
- Below 1: Potentially undervalued, but check asset quality
- Above 3: Potentially overvalued, but growth companies often trade above book value
- Sector context matters (financials vs. tech)

**Beta**
- Low (<0.8): Less volatile, defensive
- High (>1.2): More volatile, cyclical
- Consider if volatility matches investor risk tolerance

Output valid JSON only. Never add explanations outside the JSON structure."""

        # 사용자 프롬프트: 구체적인 데이터와 컨텍스트
        news_text = ', '.join(news) if news else '없음'
        
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
        
        user_prompt = f"""분석 대상 종목의 상세 정보를 제공합니다. 위에서 제시한 분석 가이드라인을 엄격히 준수하여 전문가적 인사이트를 제공해주세요.

[기업 기본 정보]
- 종목명: {stock_data.get('name', 'N/A')} ({stock_data.get('symbol', 'N/A')})
- 현재가: {stock_data.get('current_price', 'N/A')} {stock_data.get('currency', '')}
- 섹터(Sector): {sector}
- 산업(Industry): {industry}
- 시가총액: {market_cap_display} ({market_cap_context})

[핵심 재무 지표]
- PER (주가수익비율): {stock_data.get('pe_ratio', 'N/A')}
- PBR (주가순자산비율): {stock_data.get('pb_ratio', 'N/A')}
- ROE (자기자본이익률): {stock_data.get('roe', 'N/A')}% (백엔드 계산값) 또는 {stock_data.get('return_on_equity', 'N/A')} (원본)
- EPS (주당순이익): {stock_data.get('eps', 'N/A')} {stock_data.get('currency', '')}
- 배당률 (Dividend Yield, 이미 퍼센트 값): {dividend_yield_display}
- Beta (시장 대비 변동성): {stock_data.get('beta', 'N/A')}
- 목표가 (Target Price): {stock_data.get('target_mean_price', 'N/A')} {stock_data.get('currency', '')}

[백엔드 계산 점수]
- 종합 투자 점수: {backend_score}점 (가중치 기반 알고리즘으로 계산됨)

[최근 뉴스 헤드라인]
{news_text}

[분석 요청사항]
위 정보를 바탕으로 다음 JSON 포맷으로 응답해주세요. 각 지표별 인사이트는 반드시 섹터/산업 맥락을 고려하고, 잠재적 리스크를 언급해야 합니다.

**중요**: score는 백엔드에서 이미 계산되어 제공되므로, 이 값을 그대로 사용하세요. signal은 score를 기반으로 판단하세요.

{{
    "signal": ("매수", "중립", "주의" 중 하나. score 70 이상이면 "매수", 50~70이면 "중립", 50 미만이면 "주의"),
    "one_line": (한 줄 핵심 코멘트, 친근하지만 전문가적인 톤, 마침표 없음),
    "summary": (투자 포인트 3가지 요약, 리스트 형태, 각 항목 마침표 없음),
    "risk": (주의해야 할 리스크 1가지, 마침표 없음),
    "metric_insights": {{
        "pe_ratio": (PER 지표에 대한 전문가적 평가. 섹터 평균 대비 평가, Value Trap 가능성 등 고려. 친근하지만 날카로운 톤, 마침표 없음. 값이 null이면 "데이터 없음"으로),
        "pb_ratio": (PBR 지표에 대한 전문가적 평가. 섹터 맥락 고려, 마침표 없음. 값이 null이면 "데이터 없음"으로),
        "return_on_equity": (ROE 지표에 대한 전문가적 평가. 레버리지 효과 의심, 산업 대비 평가 포함, 마침표 없음. 값이 null이면 "데이터 없음"으로),
        "roe": (ROE 지표에 대한 전문가적 평가. return_on_equity와 동일한 내용, 마침표 없음. 값이 null이면 "데이터 없음"으로),
        "eps": (EPS 지표에 대한 전문가적 평가. 성장 추세, 섹터 대비 평가 포함, 마침표 없음. 값이 null이면 "데이터 없음"으로),
        "dividend_yield": (배당률 지표에 대한 전문가적 평가. 이 값은 이미 퍼센트 단위(예: 0.11%)이므로 100을 다시 곱하지 말 것. 배당 함정 가능성 경고 포함, 마침표 없음. 값이 null이면 "데이터 없음"으로),
        "beta": (Beta 지표에 대한 전문가적 평가. 변동성 의미 해석, 마침표 없음. 값이 null이면 "데이터 없음"으로),
        "target_mean_price": (목표가 지표에 대한 전문가적 평가. 상승 여력 분석, 마침표 없음. 값이 null이면 "데이터 없음"으로)
    }}
}}

**중요**: 
- 모든 metric_insights는 단순한 정의가 아닌, 섹터/산업 맥락을 고려한 전문가적 인사이트여야 함
- 잠재적 리스크나 함정을 언급할 때는 친근하지만 날카로운 톤으로
- 전송된 영문 파라미터 명을 언급하지 말 것 (ex. return_on_equity와 동일한 내용으로, 과도한 레버리지 사용이 없어서 운용 효율성이 의심스러워)
- 예시: "PER가 6.1배로 낮아서 저평가 상태입니다" (X) → "반도체 섹터임에도 PER 6배는 이례적인 저평가야. 다만 업황 둔화 우려가 과도하게 반영된 것인지, 실제 실적 악화 신호인지 확인이 필요해" (O)"""
        
        return system_prompt, user_prompt

