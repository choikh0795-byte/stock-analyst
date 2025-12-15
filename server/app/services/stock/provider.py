import json
import logging
import re
from typing import Dict, Optional

import FinanceDataReader as fdr
import pandas as pd
import yfinance as yf
import requests  # [필수 추가] requests 모듈 임포트

logger = logging.getLogger(__name__)


class StockProvider:
    """외부 데이터 수집 및 캐싱 담당."""

    _ticker_cache: Dict[str, str] = {}
    _ticker_to_name_cache: Dict[str, str] = {}
    _fundamental_cache: Dict[str, Dict] = {}
    _is_cache_loaded: bool = False

    def __init__(self) -> None:
        if not StockProvider._is_cache_loaded:
            self._load_ticker_cache()

    @classmethod
    def _load_ticker_cache(cls) -> None:
        # ... (기존 코드와 동일) ...
        if cls._is_cache_loaded:
            return
        try:
            logger.info("[StockService] 종목 리스트 및 재무정보 메모리 캐싱 시작...")
            df_krx = fdr.StockListing("KRX")

            has_per = "PER" in df_krx.columns
            has_pbr = "PBR" in df_krx.columns
            has_div = "DividendYield" in df_krx.columns

            for _, row in df_krx.iterrows():
                name = str(row["Name"]).strip()
                name_upper = name.upper()
                code = str(row["Code"])
                market = row["Market"]

                if market == "KOSPI":
                    ticker = f"{code}.KS"
                elif market == "KOSDAQ":
                    ticker = f"{code}.KQ"
                else:
                    continue

                cls._ticker_cache[name_upper] = ticker
                cls._ticker_to_name_cache[ticker] = name

                try:
                    per_val = float(row["PER"]) if has_per and pd.notna(row["PER"]) else 0.0
                except Exception:
                    per_val = 0.0

                try:
                    pbr_val = float(row["PBR"]) if has_pbr and pd.notna(row["PBR"]) else 0.0
                except Exception:
                    pbr_val = 0.0

                try:
                    div_val = float(row["DividendYield"]) if has_div and pd.notna(row["DividendYield"]) else 0.0
                except Exception:
                    div_val = 0.0

                cls._fundamental_cache[ticker] = {"per": per_val, "pbr": pbr_val, "dividend_yield": div_val}

            cls._is_cache_loaded = True
            logger.info(f"[StockService] 캐싱 완료.")
            cls._save_debug_file()

        except Exception as e:
            logger.error(f"[StockService] 캐싱 실패: {e}")

    @classmethod
    def _save_debug_file(cls) -> None:
        # ... (기존 코드와 동일) ...
        try:
            debug_data = {
                "ticker_map_sample": dict(list(cls._ticker_cache.items())[:5]),
                "fundamental_map_sample": dict(list(cls._fundamental_cache.items())[:5]),
                "total_count": len(cls._ticker_cache),
            }
            with open("debug_stock_data.json", "w", encoding="utf-8") as f:
                json.dump(debug_data, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    @staticmethod
    def _is_ticker_format(query: str) -> bool:
        ticker_pattern = re.compile(r"^[A-Z0-9]{1,10}(\.KS|\.KQ)?$")
        return bool(ticker_pattern.match(query.upper().strip()))

    def search_ticker(self, query: str) -> str:
        # ... (기존 코드와 동일) ...
        query = query.strip().upper()
        if not query:
            raise ValueError("검색어를 입력해주세요.")
        if self._is_ticker_format(query):
            return query

        if query in self._ticker_cache:
            return self._ticker_cache[query]
        for name, ticker in self._ticker_cache.items():
            if query in name:
                return ticker

        return self._search_with_yfinance(query)

    def _search_with_yfinance(self, query: str) -> str:
        # ... (기존 코드와 동일) ...
        try:
            from yfinance import Search

            search = Search(query, max_results=1, enable_fuzzy_query=True)
            if not search.quotes:
                raise ValueError("검색 불가")
            return search.quotes[0]["symbol"]
        except Exception as e:
            raise ValueError(f"검색 실패: {e}")

    # ================= [핵심 수정 부분] =================
    def get_stock(self, ticker: str):
        """
        yfinance Ticker 객체를 생성합니다.
        Render 등 서버 환경에서의 차단을 막기 위해 User-Agent가 포함된 Session을 주입합니다.
        """
        try:
            session = requests.Session()
            # 브라우저인 척 위장하는 헤더 설정
            session.headers.update({
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            })
            return yf.Ticker(ticker, session=session)
        except Exception as e:
            logger.error(f"[StockProvider] Ticker 생성 중 오류: {e}")
            # fallback: 세션 없이 시도
            return yf.Ticker(ticker)

    def get_info(self, stock) -> Dict:
        """
        stock.info 데이터를 가져오되, 실패하거나 비어있을 경우 fast_info로 보완합니다.
        """
        info = {}
        
        # 1. 기본 info 가져오기 시도 (느리거나 차단될 수 있음)
        try:
            info = stock.info
        except Exception as e:
            logger.warning(f"[StockProvider] info fetch warning (1차 시도): {e}")
        
        # info가 None이거나 비어있을 경우 딕셔너리 초기화
        if info is None:
            info = {}

        # 2. fast_info를 사용하여 핵심 데이터 강제 주입 (방어 로직)
        # fast_info는 Yahoo Finance API를 직접 찌르므로 차단 확률이 낮고 속도가 빠름
        try:
            fast_info = stock.fast_info
            
            # (1) 시가총액 (Market Cap)
            if 'marketCap' not in info or not info['marketCap']:
                val = fast_info.market_cap
                if val:
                    info['marketCap'] = val
                    logger.info(f"[StockProvider] fast_info로 marketCap 복구: {val}")

            # (2) 현재가 (Current Price)
            # last_price가 가장 최신 가격임
            if 'currentPrice' not in info or not info['currentPrice']:
                val = fast_info.last_price
                if val:
                    info['currentPrice'] = val
                    info['regularMarketPrice'] = val # 호환성을 위해 추가
                    logger.info(f"[StockProvider] fast_info로 currentPrice 복구: {val}")

            # (3) 전일 종가 (Previous Close)
            if 'previousClose' not in info or not info['previousClose']:
                val = fast_info.previous_close
                if val:
                    info['previousClose'] = val

            # (4) 52주 최고/최저
            if 'fiftyTwoWeekHigh' not in info or not info['fiftyTwoWeekHigh']:
                val = fast_info.year_high
                if val:
                    info['fiftyTwoWeekHigh'] = val
            
            if 'fiftyTwoWeekLow' not in info or not info['fiftyTwoWeekLow']:
                val = fast_info.year_low
                if val:
                    info['fiftyTwoWeekLow'] = val

        except Exception as e:
            logger.warning(f"[StockProvider] fast_info fetch failed (2차 방어 실패): {e}")

        return info
    # ====================================================

    def get_news_titles(self, stock) -> list:
        # ... (기존 코드와 동일) ...
        titles = []
        try:
            news = stock.news
            if news:
                for n in news[:3]:
                    if isinstance(n, dict) and "title" in n:
                        titles.append(n["title"])
        except Exception:
            pass
        return titles

    def get_fundamental_cache(self, ticker: str) -> Dict:
        return self._fundamental_cache.get(ticker, {})

    def get_korean_name(self, ticker: str) -> Optional[str]:
        return self._ticker_to_name_cache.get(ticker)