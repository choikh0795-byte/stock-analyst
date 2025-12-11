import json
import logging
import re
from typing import Dict, Optional

import FinanceDataReader as fdr
import pandas as pd
import yfinance as yf

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
        try:
            from yfinance import Search

            search = Search(query, max_results=1, enable_fuzzy_query=True)
            if not search.quotes:
                raise ValueError("검색 불가")
            return search.quotes[0]["symbol"]
        except Exception as e:
            raise ValueError(f"검색 실패: {e}")

    def get_stock(self, ticker: str):
        return yf.Ticker(ticker)

    def get_info(self, stock) -> Dict:
        info = {}
        try:
            info = stock.info
        except Exception:
            pass
        return info

    def get_news_titles(self, stock) -> list:
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

