import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.stock import StockAnalysisLog
from .calculator import StockCalculator
from .formatter import StockFormatter
from .provider import StockProvider

logger = logging.getLogger(__name__)


class StockService:
    """
    StockService Facade
    - Provider: 외부 데이터 수집/캐싱
    - Calculator: 결측치 방어 계산
    - Formatter: 화면용 문자열 포맷팅
    """

    def __init__(
        self,
        provider: Optional[StockProvider] = None,
        calculator: Optional[StockCalculator] = None,
        formatter: Optional[StockFormatter] = None,
    ) -> None:
        self.provider = provider or StockProvider()
        self.calculator = calculator or StockCalculator()
        self.formatter = formatter or StockFormatter()

    @classmethod
    def _load_ticker_cache(cls) -> None:
        StockProvider._load_ticker_cache()

    def search_ticker(self, query: str) -> str:
        return self.provider.search_ticker(query)

    def get_stock_info(self, ticker: str, db: Session) -> Tuple[Dict, List[str]]:
        if not self.provider._is_ticker_format(ticker):
            ticker = self.search_ticker(ticker)

        is_korean = ticker.upper().endswith((".KS", ".KQ"))
        logger.info(f"[StockService] 조회 시작: {ticker}")

        cache_valid_until = datetime.utcnow() - timedelta(hours=1)
        cached_log = (
            db.query(StockAnalysisLog)
            .filter(StockAnalysisLog.ticker == ticker.upper(), StockAnalysisLog.updated_at >= cache_valid_until)
            .first()
        )
        if cached_log:
            return cached_log.analysis_json.get("stock_data", {}), cached_log.analysis_json.get("news", [])

        stock = self.provider.get_stock(ticker)
        info = self.provider.get_info(stock)

        logger.info(f"[DEBUG] === stock.info 전체 데이터 (ticker: {ticker}) ===")
        try:
            logger.info(json.dumps(info, indent=2, ensure_ascii=False, default=str))
        except Exception as e:
            logger.warning(f"[DEBUG] stock.info 로그 출력 실패: {e}")
            logger.info(f"[DEBUG] stock.info 타입: {type(info)}, 키 개수: {len(info) if isinstance(info, dict) else 'N/A'}")

        current_price = self.calculator.calculate_current_price(info, stock)
        fdr_data = self.provider.get_fundamental_cache(ticker)

        logger.info(f"[DEBUG] === PER/PBR 계산 시작 전 변수 확인 ===")
        logger.info(f"[DEBUG] trailingPE: {info.get('trailingPE')} (type: {type(info.get('trailingPE'))})")
        logger.info(f"[DEBUG] forwardPE: {info.get('forwardPE')} (type: {type(info.get('forwardPE'))})")
        logger.info(f"[DEBUG] priceToBook: {info.get('priceToBook')} (type: {type(info.get('priceToBook'))})")
        logger.info(f"[DEBUG] bookValue: {info.get('bookValue')} (type: {type(info.get('bookValue'))})")
        logger.info(f"[DEBUG] marketCap: {info.get('marketCap')} (type: {type(info.get('marketCap'))})")
        logger.info(f"[DEBUG] netIncomeToCommon: {info.get('netIncomeToCommon')} (type: {type(info.get('netIncomeToCommon'))})")
        logger.info(f"[DEBUG] currentPrice: {current_price} (type: {type(current_price)})")

        market_cap = info.get("marketCap")
        pe_ratio = self.calculator.calculate_pe_ratio(info, fdr_data, market_cap)
        pb_ratio = self.calculator.calculate_pb_ratio(info, current_price, fdr_data, market_cap, stock)
        dividend_yield = self.calculator.calculate_dividend_yield(info, fdr_data, is_korean)
        roe = self.calculator.calculate_roe(info, stock)
        volatility, volatility_type = self.calculator.calculate_volatility(info, stock)

        previous_close = info.get("previousClose", current_price)
        fifty_two_week_low = info.get("fiftyTwoWeekLow")
        fifty_two_week_high = info.get("fiftyTwoWeekHigh")
        target_mean_price = info.get("targetMeanPrice")

        current_price_str = self.formatter.format_currency(current_price, is_korean)
        previous_close_str = self.formatter.format_currency(previous_close, is_korean)
        fifty_two_week_low_str = (
            self.formatter.format_currency(fifty_two_week_low, is_korean) if fifty_two_week_low else None
        )
        fifty_two_week_high_str = (
            self.formatter.format_currency(fifty_two_week_high, is_korean) if fifty_two_week_high else None
        )
        target_mean_price_str = (
            self.formatter.format_currency(target_mean_price, is_korean) if target_mean_price else None
        )

        market_cap_str = self.formatter.format_market_cap(market_cap)
        roe_str = self.formatter.format_roe(roe)
        volatility_str = self.formatter.format_volatility(volatility, volatility_type)
        dividend_yield_str = self.formatter.format_dividend(dividend_yield, is_korean)

        logger.info(f"[Formatting Check] {ticker} -> Price: {current_price} -> Formatted: {current_price_str}")
        logger.info(f"[Formatting Check] {ticker} -> ROE: {roe} -> Formatted: {roe_str}")
        logger.info(
            f"[Formatting Check] {ticker} -> Volatility: {volatility} ({volatility_type}) -> Formatted: {volatility_str}"
        )

        is_korean_stock = is_korean
        currency_symbol = "₩" if is_korean else "$"

        stock_name = info.get("shortName", info.get("longName", ticker))
        if is_korean_stock:
            korean_name = self.provider.get_korean_name(ticker)
            if korean_name:
                stock_name = korean_name
                logger.info(f"[StockService] 한국 종목 한글명 사용: {ticker} -> {korean_name}")

        data = {
            "name": stock_name,
            "symbol": ticker,
            "current_price": current_price,
            "previous_close": previous_close,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
            "dividend_yield": dividend_yield,
            "current_price_str": current_price_str,
            "previous_close_str": previous_close_str,
            "fifty_two_week_low_str": fifty_two_week_low_str,
            "fifty_two_week_high_str": fifty_two_week_high_str,
            "target_mean_price_str": target_mean_price_str,
            "market_cap_str": market_cap_str,
            "currency": "KRW" if is_korean_stock else "USD",
            "sector": info.get("sector", "ETF/Index"),
            "summary": (info.get("longBusinessSummary", "정보 없음")[:500]),
            "fifty_two_week_low": fifty_two_week_low,
            "fifty_two_week_high": fifty_two_week_high,
            "target_mean_price": target_mean_price,
            "roe": roe,
            "roe_str": roe_str,
            "volatility": volatility,
            "volatility_str": volatility_str,
            "dividend_yield_str": dividend_yield_str,
        }

        logger.info(f"[DEBUG] === 최종 반환 값 확인 ===")
        logger.info(f"[DEBUG] 최종 pe_ratio: {pe_ratio} (type: {type(pe_ratio)})")
        logger.info(f"[DEBUG] 최종 pb_ratio: {pb_ratio} (type: {type(pb_ratio)})")
        logger.info(f"[DEBUG] 최종 roe: {roe} (type: {type(roe)}) -> roe_str: {roe_str}")
        logger.info(f"[DEBUG] 최종 dividend_yield: {dividend_yield} (type: {type(dividend_yield)}) -> dividend_yield_str: {dividend_yield_str}")
        logger.info(
            f"[DEBUG] 최종 volatility: {volatility} (type: {type(volatility)}, source: {volatility_type}) -> volatility_str: {volatility_str}"
        )
        logger.info(
            f"[StockService] 반환: {data['name']} / PER:{data['pe_ratio']} / PBR:{data['pb_ratio']} / ROE:{roe_str} / Volatility:{volatility_str}"
        )

        news_titles = self.provider.get_news_titles(stock)
        self._save_to_db(db, ticker, data, news_titles)

        return data, news_titles

    def _save_to_db(self, db: Session, ticker: str, data: Dict, news: List[str]) -> None:
        try:
            analysis_json = {"stock_data": data, "news": news}
            log = db.query(StockAnalysisLog).filter(StockAnalysisLog.ticker == ticker.upper()).first()
            if log:
                log.price = data["current_price"]
                log.analysis_json = analysis_json
                log.updated_at = datetime.utcnow()
            else:
                new_log = StockAnalysisLog(ticker=ticker.upper(), price=data["current_price"], analysis_json=analysis_json)
                db.add(new_log)
            db.commit()
        except Exception:
            db.rollback()

