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
        
        # EPS 계산: 다단계 방어 로직 적용
        eps = self._calculate_eps(info, current_price)

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
        eps_str = self.formatter.format_eps(eps, is_korean)
        dividend_yield_str = self.formatter.format_dividend(dividend_yield, is_korean)

        logger.info(f"[Formatting Check] {ticker} -> Price: {current_price} -> Formatted: {current_price_str}")
        logger.info(f"[Formatting Check] {ticker} -> ROE: {roe} -> Formatted: {roe_str}")
        logger.info(f"[Formatting Check] {ticker} -> EPS: {eps} -> Formatted: {eps_str}")
        logger.info(f"[Formatting Check] {ticker} -> Dividend Yield: {dividend_yield} -> Formatted: {dividend_yield_str}")

        is_korean_stock = is_korean
        currency_symbol = "₩" if is_korean else "$"

        stock_name = info.get("shortName", info.get("longName", ticker))
        if is_korean_stock:
            korean_name = self.provider.get_korean_name(ticker)
            if korean_name:
                stock_name = korean_name
                logger.info(f"[StockService] 한국 종목 한글명 사용: {ticker} -> {korean_name}")

        # market_cap을 문자열로 변환 (스키마 호환성)
        if market_cap is not None:
            try:
                # float로 먼저 변환 후 int로 변환 (소수점 제거)
                market_cap_str_value = str(int(float(market_cap)))
                logger.info(f"[DEBUG] market_cap 변환: {market_cap} (type: {type(market_cap)}) -> {market_cap_str_value} (type: {type(market_cap_str_value)})")
            except (ValueError, TypeError) as e:
                logger.warning(f"[DEBUG] market_cap 변환 실패: {e}")
                market_cap_str_value = None
        else:
            market_cap_str_value = None
        
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
            "market_cap": market_cap_str_value,  # 스키마 호환성을 위해 문자열로 변환
            "currency": "KRW" if is_korean_stock else "USD",
            "sector": info.get("sector", "ETF/Index"),
            "industry": info.get("industry", "정보 없음"),  # AI 분석을 위한 산업 정보 추가
            "summary": (info.get("longBusinessSummary", "정보 없음")[:500]),
            "fifty_two_week_low": fifty_two_week_low,
            "fifty_two_week_high": fifty_two_week_high,
            "target_mean_price": target_mean_price,
            "roe": roe,
            "roe_str": roe_str,
            "eps": eps,
            "eps_str": eps_str,
            "dividend_yield_str": dividend_yield_str,
        }

        # market_cap 타입 최종 확인 및 강제 변환
        if 'market_cap' in data and data['market_cap'] is not None:
            if not isinstance(data['market_cap'], str):
                logger.warning(f"[DEBUG] market_cap이 문자열이 아님: {data['market_cap']} (type: {type(data['market_cap'])})")
                try:
                    data['market_cap'] = str(int(float(data['market_cap'])))
                    logger.info(f"[DEBUG] market_cap 강제 변환 완료: {data['market_cap']}")
                except (ValueError, TypeError) as e:
                    logger.error(f"[DEBUG] market_cap 강제 변환 실패: {e}")
                    data['market_cap'] = None

        # 점수 계산 (가중치 기반 알고리즘)
        beta = info.get("beta")
        score = self.calculator.calculate_score(
            stock_data=data,
            roe=roe,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            market_cap=market_cap,
            beta=beta,
            info=info,
        )
        data["score"] = score
        
        logger.info(f"[DEBUG] === 최종 반환 값 확인 ===")
        logger.info(f"[DEBUG] market_cap 최종값: {data.get('market_cap')} (type: {type(data.get('market_cap'))})")
        logger.info(f"[DEBUG] 최종 pe_ratio: {pe_ratio} (type: {type(pe_ratio)})")
        logger.info(f"[DEBUG] 최종 pb_ratio: {pb_ratio} (type: {type(pb_ratio)})")
        logger.info(f"[DEBUG] 최종 roe: {roe} (type: {type(roe)}) -> roe_str: {roe_str}")
        logger.info(f"[DEBUG] 최종 dividend_yield: {dividend_yield} (type: {type(dividend_yield)}) -> dividend_yield_str: {dividend_yield_str}")
        logger.info(f"[DEBUG] 최종 eps: {eps} (type: {type(eps)}) -> eps_str: {eps_str}")
        logger.info(f"[DEBUG] 최종 score: {score} (type: {type(score)})")
        logger.info(
            f"[StockService] 반환: {data['name']} / PER:{data['pe_ratio']} / PBR:{data['pb_ratio']} / ROE:{roe_str} / EPS:{eps_str} / Score:{score}"
        )

        news_titles = self.provider.get_news_titles(stock)
        self._save_to_db(db, ticker, data, news_titles)

        return data, news_titles

    def _calculate_eps(self, info: Dict, current_price: float) -> Optional[float]:
        """
        EPS(주당순이익)를 다단계 방어 로직으로 계산
        
        우선순위:
        1. trailingEps 또는 forwardEps (직접 접근)
        2. netIncomeToCommon / sharesOutstanding (기본 계산)
        3. epsCurrentYear (기존 필드)
        4. currentPrice / trailingPE (밸류에이션 역산)
        
        Args:
            info: yfinance API 응답 데이터 딕셔너리
            current_price: 현재 주가
            
        Returns:
            계산된 EPS 값 (float) 또는 None
        """
        # 1순위: trailingEps 또는 forwardEps 직접 접근
        eps = info.get("trailingEps") or info.get("forwardEps")
        if eps is not None:
            try:
                eps_float = float(eps)
                if eps_float > 0:
                    logger.info(f"[EPS Calculation] 1순위 성공: trailingEps/forwardEps = {eps_float}")
                    return eps_float
            except (ValueError, TypeError):
                pass
        
        # 2순위: netIncomeToCommon / sharesOutstanding
        net_income = info.get("netIncomeToCommon")
        shares_outstanding = info.get("sharesOutstanding")
        if net_income is not None and shares_outstanding is not None:
            try:
                net_income_float = float(net_income)
                shares_float = float(shares_outstanding)
                if shares_float > 0 and net_income_float > 0:
                    eps = net_income_float / shares_float
                    logger.info(
                        f"[EPS Calculation] 2순위 성공: netIncomeToCommon({net_income_float}) / "
                        f"sharesOutstanding({shares_float}) = {eps}"
                    )
                    return eps
            except (ValueError, TypeError) as e:
                logger.debug(f"[EPS Calculation] 2순위 계산 실패: {e}")
        
        # 3순위: epsCurrentYear
        eps_current_year = info.get("epsCurrentYear")
        if eps_current_year is not None:
            try:
                eps_float = float(eps_current_year)
                if eps_float > 0:
                    logger.info(f"[EPS Calculation] 3순위 성공: epsCurrentYear = {eps_float}")
                    return eps_float
            except (ValueError, TypeError):
                pass
        
        # 4순위: currentPrice / trailingPE (밸류에이션 역산)
        trailing_pe = info.get("trailingPE")
        if current_price and current_price > 0 and trailing_pe is not None:
            try:
                trailing_pe_float = float(trailing_pe)
                if trailing_pe_float > 0:
                    eps = current_price / trailing_pe_float
                    logger.info(
                        f"[EPS Calculation] 4순위 성공: currentPrice({current_price}) / "
                        f"trailingPE({trailing_pe_float}) = {eps}"
                    )
                    return eps
            except (ValueError, TypeError) as e:
                logger.debug(f"[EPS Calculation] 4순위 계산 실패: {e}")
        
        # 모든 단계 실패
        logger.warning("[EPS Calculation] 모든 단계 실패: EPS를 계산할 수 없습니다.")
        return None

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

