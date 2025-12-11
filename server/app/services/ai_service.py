from typing import Dict, List, Optional
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

        prompt = self._build_analysis_prompt(stock_data, news)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful financial assistant. Output valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"[AIService] 분석 완료: {stock_data.get('symbol', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"[AIService] AI 분석 중 오류 발생: {e}")
            return None
    
    def _build_analysis_prompt(self, stock_data: Dict, news: List[str]) -> str:
        """
        AI 분석을 위한 프롬프트를 생성합니다.
        
        Args:
            stock_data: 주식 정보 딕셔너리
            news: 뉴스 헤드라인 리스트
            
        Returns:
            str: 생성된 프롬프트
        """
        news_text = ', '.join(news) if news else '없음'
        
        prompt = f"""
        너는 주식 잘하는 학교 선배야. 친근하고 쉬운 말투로 초보 투자자에게 조언해줘.
        
        [말투 지침]
        - 친근하고 쉬운 구어체를 사용해 (~~해요, ~~요 체)
        - 어려운 금융 용어는 쉽게 풀어서 설명해
        - 마치 주식 잘하는 학교 선배가 조언해주듯이 다정하게
        - **중요: 문장의 끝에 마침표(.)를 절대 찍지 마** (예: "매수하는 게 좋아" (O), "매수하는 게 좋습니다." (X))
        - 명사형 종결(~~함, ~~임) 금지
        
        [기업 정보]
        - 종목: {stock_data['name']} ({stock_data['symbol']})
        - 현재가: {stock_data['current_price']}
        - 섹터: {stock_data['sector']}
        - PER: {stock_data.get('pe_ratio')}
        - PBR: {stock_data.get('pb_ratio')}
        - ROE: {stock_data.get('return_on_equity')}
        - 배당률: {stock_data.get('dividend_yield')}
        - Beta: {stock_data.get('beta')}
        - 목표가: {stock_data.get('target_mean_price')}
        - 최근 뉴스 헤드라인: {news_text}
        
        [요청사항]
        반드시 아래 JSON 포맷으로만 응답해 (다른 말 덧붙이지 마)
        {{
            "score": (0~100 사이의 정수, 매수 매력도),
            "signal": ("매수", "중립", "주의" 중 하나),
            "one_line": (한 줄 핵심 코멘트, 친근한 구어체, 마침표 없음),
            "summary": (투자 포인트 3가지 요약, 리스트 형태, 각 항목 마침표 없음),
            "risk": (주의해야 할 리스크 1가지, 마침표 없음),
            "metric_insights": {{
                "pe_ratio": (PER 지표에 대한 한 문장 평가, 친근한 구어체, 마침표 없음, 값이 null이면 "데이터 없음"으로),
                "pb_ratio": (PBR 지표에 대한 한 문장 평가, 친근한 구어체, 마침표 없음, 값이 null이면 "데이터 없음"으로),
                "return_on_equity": (ROE 지표에 대한 한 문장 평가, 친근한 구어체, 마침표 없음, 값이 null이면 "데이터 없음"으로),
                "dividend_yield": (배당률 지표에 대한 한 문장 평가, 친근한 구어체, 마침표 없음, 값이 null이면 "데이터 없음"으로),
                "beta": (Beta 지표에 대한 한 문장 평가, 친근한 구어체, 마침표 없음, 값이 null이면 "데이터 없음"으로),
                "target_mean_price": (목표가 지표에 대한 한 문장 평가, 친근한 구어체, 마침표 없음, 값이 null이면 "데이터 없음"으로)
            }}
        }}
        """
        
        return prompt

