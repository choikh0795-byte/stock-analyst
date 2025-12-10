import streamlit as st
import yfinance as yf
import openai
import os
import json
from dotenv import load_dotenv

# .env 파일에서 API 키 로드
load_dotenv()

# OpenAI 클라이언트 설정 (API KEY가 환경변수에 있어야 함)
# 만약 .env 안쓰고 테스트하려면 아래에 직접 키 입력: api_key="sk-..."
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="AI 주식 3초 분석",
    page_icon="📈",
    layout="centered"
)

@st.cache_data(ttl=3600)
def get_stock_info(ticker):
    try:
        print(f"--- [DEBUG] 검색 시작: {ticker} ---")
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info:
            st.error(f"❌ '{ticker}' 정보를 가져올 수 없습니다.")
            return None, None

        # [핵심 수정] 가격을 찾는 순서 (우선순위: currentPrice -> regularMarketPrice -> previousClose)
        # 값이 None일 경우를 대비해 0으로 강제 변환
        current_price = info.get("currentPrice") or info.get("regularMarketPrice") or info.get("previousClose") or 0
        
        # [핵심 수정] PER 같은 지표가 ETF엔 없을 수 있음 (None 체크 강화)
        pe_ratio = info.get("trailingPE")
        if pe_ratio is None:
            pe_ratio = "N/A (ETF)"
        
        # 데이터 매핑
        data = {
            "name": info.get("shortName", info.get("longName", ticker)), # 짧은 이름 없으면 긴 이름
            "symbol": info.get("symbol", ticker),
            "current_price": current_price,
            "previous_close": info.get("previousClose", current_price), # 전일가 없으면 현재가로 대체
            "market_cap": info.get("marketCap", "N/A"),
            "pe_ratio": pe_ratio,
            "sector": info.get("sector", "ETF/Index"), # 섹터 없으면 ETF로 간주
            "summary": info.get("longBusinessSummary", "정보 없음")[:500],
        }

        # 가격이 0원(데이터 오류)이면 경고
        if data['current_price'] == 0:
            st.warning(f"⚠️ {ticker}의 가격 데이터를 찾을 수 없습니다.")
            print(f"--- [DEBUG] 가격 찾기 실패: {ticker} ---")
            return None, None

        print(f"--- [DEBUG] 데이터 확보 성공: {data['name']} / ${data['current_price']} ---")

        # 뉴스 가져오기 (에러 방지 적용됨)
        news_titles = []
        try:
            raw_news = stock.news
            if raw_news:
                for n in raw_news[:3]:
                    if isinstance(n, dict) and 'title' in n:
                        news_titles.append(n['title'])
        except Exception:
            pass # 뉴스 에러는 쿨하게 무시
            
        return data, news_titles

    except Exception as e:
        st.error(f"🔥 시스템 에러: {e}")
        print(f"--- [DEBUG] 치명적 에러: {e} ---")
        return None, None

# 3. AI 분석 함수 (JSON 모드 사용)
def analyze_stock_with_ai(data, news):
    if not data:
        return None

    prompt = f"""
    너는 20년 경력의 냉철한 펀드매니저야. 아래 데이터를 보고 초보 투자자를 위해 분석해줘.
    
    [기업 정보]
    - 종목: {data['name']} ({data['symbol']})
    - 현재가: {data['current_price']}
    - 섹터: {data['sector']}
    - PER: {data['pe_ratio']}
    - 최근 뉴스 헤드라인: {', '.join(news)}
    
    [요청사항]
    반드시 아래 JSON 포맷으로만 응답해. (다른 말 덧붙이지 마)
    {{
        "score": (0~100 사이의 정수, 매수 매력도),
        "signal": ("매수", "중립", "주의" 중 하나),
        "one_line": (한 줄 핵심 코멘트, 반말 모드),
        "summary": (투자 포인트 3가지 요약, 리스트 형태),
        "risk": (주의해야 할 리스크 1가지)
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 가성비 모델
            messages=[
                {"role": "system", "content": "You are a helpful financial assistant. Output valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"} # JSON 강제 출력
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        st.error(f"AI 분석 중 오류 발생: {e}")
        return None

# --- UI 구성 ---

st.title("📈 AI 주식/ETF 3초 진단")
st.caption("개발자 블로그: [https://blog.naver.com/cjhol2107]")

# 검색창
ticker_input = st.text_input("티커를 입력하세요 (예: AAPL, TSLA, SCHD)", "").upper()

if ticker_input:
    with st.spinner(f"🔍 '{ticker_input}' 데이터를 분석하고 있습니다..."):
        # 데이터 가져오기
        stock_data, latest_news = get_stock_info(ticker_input)
        
        if stock_data and stock_data['current_price'] > 0:
            # 1. 기본 시세 정보 표시
            col1, col2, col3 = st.columns(3)
            price = stock_data['current_price']
            prev = stock_data['previous_close']
            delta = price - prev
            delta_per = (delta / prev) * 100
            
            col1.metric("현재가", f"${price}", f"{delta:.2f} ({delta_per:.2f}%)")
            col2.metric("PER", stock_data['pe_ratio'])
            col3.metric("섹터", stock_data['sector'])
            
            st.divider()

            # 2. AI 분석 실행
            ai_result = analyze_stock_with_ai(stock_data, latest_news)
            
            if ai_result:
                # 점수와 신호등
                score = ai_result['score']
                signal = ai_result['signal']
                color_map = {"매수": "green", "중립": "orange", "주의": "red"}
                color = color_map.get(signal, "blue")
                
                st.subheader(f"🤖 AI 투자 점수: :{color}[{score}점]")
                st.progress(score / 100)
                
                # 한줄평 (카드 스타일)
                st.info(f"💡 **한 줄 요약:** {ai_result['one_line']}")
                
                # 상세 분석
                c1, c2 = st.columns(2)
                with c1:
                    st.write("#### ✅ 투자 포인트")
                    for point in ai_result['summary']:
                        st.write(f"- {point}")
                
                with c2:
                    st.write("#### ⚠️ 리스크 요인")
                    st.write(f"- {ai_result['risk']}")
                
            else:
                st.error("AI 분석에 실패했습니다.")
                
        else:
            st.error("종목을 찾을 수 없습니다. 티커를 확인해주세요. (미국 주식 권장)")