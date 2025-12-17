import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.stock import StockAnalysisLog
from .calculator import StockCalculator
from .formatter import StockFormatter
from .provider import StockProvider
from .kis_master_service import KisMasterService

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

        # KIS 마스터 서비스 (한국 종목명 매핑용)
        self._kis_master: Optional[KisMasterService] = None
        try:
            self._kis_master = KisMasterService()
            loaded = self._kis_master.load_master_data()
            if loaded:
                logger.info("[StockService] KIS 마스터 데이터 로드 성공")
            else:
                logger.warning("[StockService] KIS 마스터 데이터 로드 실패 - korean_stock_name 비활성화")
        except Exception as e:
            logger.error(f"[StockService] KIS 마스터 서비스 초기화 실패: {e}")
            self._kis_master = None


    def search_ticker(self, query: str) -> str:
        return self.provider.search_ticker(query)

    def get_stock_info(self, ticker: str, db: Session) -> Tuple[Dict, List[str]]:
        from .provider import StockProvider
        if not StockProvider._is_ticker_format(ticker):
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

        # Provider에서 표준화된 딕셔너리 직접 받기
        info = self.provider.get_stock_info(ticker)

        logger.info(f"[DEBUG] === stock.info 전체 데이터 (ticker: {ticker}) ===")
        try:
            logger.info(json.dumps(info, indent=2, ensure_ascii=False, default=str))
        except Exception as e:
            logger.warning(f"[DEBUG] stock.info 로그 출력 실패: {e}")
            logger.info(f"[DEBUG] stock.info 타입: {type(info)}, 키 개수: {len(info) if isinstance(info, dict) else 'N/A'}")

        # Provider가 이미 계산한 current_price 사용
        current_price = info.get("current_price") or 0.0
        fdr_data = {}  # 캐시 제거로 인해 빈 딕셔너리 사용

        logger.info(f"[DEBUG] === PER/PBR 계산 시작 전 변수 확인 ===")
        logger.info(f"[DEBUG] pe_ratio (Provider): {info.get('pe_ratio')} (type: {type(info.get('pe_ratio'))})")
        logger.info(f"[DEBUG] pb_ratio (Provider): {info.get('pb_ratio')} (type: {type(info.get('pb_ratio'))})")
        logger.info(f"[DEBUG] market_cap (Provider): {info.get('market_cap')} (type: {type(info.get('market_cap'))})")
        logger.info(f"[DEBUG] current_price (Provider): {current_price} (type: {type(current_price)})")

        # Provider가 이미 계산한 값들을 사용하거나, 없을 경우 calculator로 계산
        market_cap = info.get("market_cap")
        pe_ratio = info.get("pe_ratio")
        if not pe_ratio:
            # calculator는 yfinance 형식을 기대하므로, 표준화된 딕셔너리를 변환
            calc_info = self._convert_to_calculator_format(info)
            pe_ratio = self.calculator.calculate_pe_ratio(calc_info, fdr_data, market_cap)
        
        pb_ratio = info.get("pb_ratio")
        if not pb_ratio:
            calc_info = self._convert_to_calculator_format(info)
            pb_ratio = self.calculator.calculate_pb_ratio_without_stock(calc_info, current_price, fdr_data, market_cap)
        
        dividend_yield = info.get("dividend_yield")
        if not dividend_yield:
            calc_info = self._convert_to_calculator_format(info)
            dividend_yield = self.calculator.calculate_dividend_yield(calc_info, fdr_data, is_korean)
        
        roe = info.get("roe")
        if not roe:
            calc_info = self._convert_to_calculator_format(info)
            roe = self.calculator.calculate_roe_without_stock(calc_info)
        
        # EPS 계산: Provider가 이미 계산한 값 사용
        eps = info.get("eps")
        if eps is None:
            eps = self._calculate_eps_from_info(info, current_price)

        previous_close = info.get("previous_close") or current_price
        fifty_two_week_low = info.get("fifty_two_week_low")
        fifty_two_week_high = info.get("fifty_two_week_high")
        target_mean_price = info.get("target_mean_price")
        beta = info.get("beta")

        # 가격 변동 계산
        change_value = current_price - previous_close if previous_close else 0.0
        change_percentage = (change_value / previous_close * 100) if previous_close and previous_close > 0 else 0.0
        change_status = self.formatter.get_change_status(current_price, previous_close)

        # 목표가 괴리율 계산
        target_upside = None
        if target_mean_price and current_price and current_price > 0:
            target_upside = ((target_mean_price - current_price) / current_price) * 100

        # 모든 값 포맷팅
        current_price_str = self.formatter.format_currency(current_price, is_korean)
        previous_close_str = self.formatter.format_currency(previous_close, is_korean)
        fifty_two_week_low_str = (
            self.formatter.format_currency(fifty_two_week_low, is_korean) if fifty_two_week_low else None
        )
        fifty_two_week_high_str = (
            self.formatter.format_currency(fifty_two_week_high, is_korean) if fifty_two_week_high else None
        )
        target_mean_price_str = (
            self.formatter.format_currency(target_mean_price, is_korean) if target_mean_price else "정보없음"
        )

        market_cap_str = self.formatter.format_market_cap(market_cap)
        roe_str = self.formatter.format_roe(roe)
        eps_str = self.formatter.format_eps(eps, is_korean)
        dividend_yield_str = self.formatter.format_dividend(dividend_yield, is_korean)
        pe_ratio_str = self.formatter.format_pe_ratio(pe_ratio, is_korean)
        pb_ratio_str = self.formatter.format_pb_ratio(pb_ratio, is_korean)
        beta_str = self.formatter.format_beta(beta)
        change_value_str = self.formatter.format_change_value(change_value, is_korean)
        change_percentage_str = self.formatter.format_change_percentage(change_percentage)
        target_upside_str = self.formatter.format_target_upside(target_upside)

        logger.info(f"[Formatting Check] {ticker} -> Price: {current_price} -> Formatted: {current_price_str}")
        logger.info(f"[Formatting Check] {ticker} -> ROE: {roe} -> Formatted: {roe_str}")
        logger.info(f"[Formatting Check] {ticker} -> EPS: {eps} -> Formatted: {eps_str}")
        logger.info(f"[Formatting Check] {ticker} -> Dividend Yield: {dividend_yield} -> Formatted: {dividend_yield_str}")

        is_korean_stock = is_korean
        currency_symbol = "₩" if is_korean else "$"

        stock_name = info.get("name") or ticker

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
            "beta": beta,
            # 포맷팅된 문자열 필드
            "current_price_str": current_price_str,
            "previous_close_str": previous_close_str,
            "fifty_two_week_low_str": fifty_two_week_low_str,
            "fifty_two_week_high_str": fifty_two_week_high_str,
            "target_mean_price_str": target_mean_price_str,
            "market_cap_str": market_cap_str,
            "market_cap": market_cap_str_value,  # 스키마 호환성을 위해 문자열로 변환
            "roe_str": roe_str,
            "eps_str": eps_str,
            "dividend_yield_str": dividend_yield_str,
            "pe_ratio_str": pe_ratio_str,
            "pb_ratio_str": pb_ratio_str,
            "beta_str": beta_str,
            # 가격 변동 관련
            "change_value": change_value,
            "change_value_str": change_value_str,
            "change_percentage": change_percentage,
            "change_percentage_str": change_percentage_str,
            "change_status": change_status,
            # 목표가 괴리율
            "target_upside": target_upside,
            "target_upside_str": target_upside_str,
            # 기타 필드
            "currency": info.get("currency", "KRW" if is_korean_stock else "USD"),
            "sector": info.get("sector") or "정보없음",
            "industry": info.get("industry") or "정보 없음",  # AI 분석을 위한 산업 정보 추가
            "summary": (info.get("summary") or "정보 없음")[:500],
            "fifty_two_week_low": fifty_two_week_low,
            "fifty_two_week_high": fifty_two_week_high,
            "target_mean_price": target_mean_price,
            "roe": roe,
            "eps": eps,
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
        # beta는 표준화된 딕셔너리에서 가져오거나, calculator 형식으로 변환된 딕셔너리에서 가져옴
        calc_info = self._convert_to_calculator_format(info)
        calc_beta = calc_info.get("beta") or beta
        score = self.calculator.calculate_score(
            stock_data=data,
            roe=roe,
            pe_ratio=pe_ratio,
            pb_ratio=pb_ratio,
            market_cap=market_cap,
            beta=calc_beta,
            info=calc_info,
        )
        data["score"] = score

        # 한국 종목명 (KIS 마스터 기준) 매핑 시도
        korean_stock_name: Optional[str] = None
        if is_korean and self._kis_master is not None:
            try:
                if not self._kis_master._loaded:
                    # 필요 시 지연 로드
                    self._kis_master.load_master_data()
                korean_stock_name = self._kis_master.get_name_by_ticker(ticker)
            except Exception as e:
                logger.warning(f"[StockService] KIS 마스터에서 한국 종목명 조회 실패: {e}")

        data["name"] = korean_stock_name or stock_name
        
        logger.info(f"[DEBUG] === 최종 반환 값 확인 ===")
        logger.info(f"[DEBUG] market_cap 최종값: {data.get('market_cap')} (type: {type(data.get('market_cap'))})")
        logger.info(f"[DEBUG] 최종 pe_ratio: {pe_ratio} (type: {type(pe_ratio)}) -> pe_ratio_str: {pe_ratio_str}")
        logger.info(f"[DEBUG] 최종 pb_ratio: {pb_ratio} (type: {type(pb_ratio)}) -> pb_ratio_str: {pb_ratio_str}")
        logger.info(f"[DEBUG] 최종 roe: {roe} (type: {type(roe)}) -> roe_str: {roe_str}")
        logger.info(f"[DEBUG] 최종 dividend_yield: {dividend_yield} (type: {type(dividend_yield)}) -> dividend_yield_str: {dividend_yield_str}")
        logger.info(f"[DEBUG] 최종 eps: {eps} (type: {type(eps)}) -> eps_str: {eps_str}")
        logger.info(f"[DEBUG] 최종 beta: {beta} (type: {type(beta)}) -> beta_str: {beta_str}")
        logger.info(f"[DEBUG] 최종 change_value: {change_value} -> change_value_str: {change_value_str}")
        logger.info(f"[DEBUG] 최종 change_percentage: {change_percentage} -> change_percentage_str: {change_percentage_str}")
        logger.info(f"[DEBUG] 최종 change_status: {change_status}")
        logger.info(f"[DEBUG] 최종 target_upside: {target_upside} -> target_upside_str: {target_upside_str}")
        logger.info(f"[DEBUG] 최종 score: {score} (type: {type(score)})")
        logger.info(
            f"[StockService] 반환: {data['name']} / PER:{pe_ratio_str} / PBR:{pb_ratio_str} / ROE:{roe_str} / EPS:{eps_str} / Score:{score}"
        )

        # Provider의 get_news 메서드 사용
        news_titles = self.provider.get_news(ticker)
        
        # 최종 JSON payload를 서버 콘솔에 출력
        final_payload = {
            "stock_data": data,
            "news": news_titles
        }
        print("\n" + "="*80)
        print(f"[StockService] 최종 JSON Payload (ticker: {ticker})")
        print("="*80)
        try:
            print(json.dumps(final_payload, indent=2, ensure_ascii=False, default=str))
        except Exception as e:
            logger.warning(f"[StockService] JSON 직렬화 실패: {e}")
            print(f"JSON 직렬화 실패: {e}")
        print("="*80 + "\n")
        
        self._save_to_db(db, ticker, data, news_titles)

        return data, news_titles

    def _convert_to_calculator_format(self, info: Dict) -> Dict:
        """
        Provider가 반환한 표준화된 딕셔너리를 calculator가 기대하는 형식으로 변환합니다.
        """
        calc_info = info.copy()
        # 표준화된 키를 yfinance 형식 키로 매핑
        if "current_price" in calc_info and "currentPrice" not in calc_info:
            calc_info["currentPrice"] = calc_info["current_price"]
        if "market_cap" in calc_info and "marketCap" not in calc_info:
            calc_info["marketCap"] = calc_info["market_cap"]
        if "previous_close" in calc_info and "previousClose" not in calc_info:
            calc_info["previousClose"] = calc_info["previous_close"]
        if "fifty_two_week_low" in calc_info and "fiftyTwoWeekLow" not in calc_info:
            calc_info["fiftyTwoWeekLow"] = calc_info["fifty_two_week_low"]
        if "fifty_two_week_high" in calc_info and "fiftyTwoWeekHigh" not in calc_info:
            calc_info["fiftyTwoWeekHigh"] = calc_info["fifty_two_week_high"]
        if "target_mean_price" in calc_info and "targetMeanPrice" not in calc_info:
            calc_info["targetMeanPrice"] = calc_info["target_mean_price"]
        return calc_info

    def _calculate_eps_from_info(self, info: Dict, current_price: float) -> Optional[float]:
        """
        EPS(주당순이익)를 다단계 방어 로직으로 계산
        
        우선순위:
        1. Provider가 이미 계산한 eps 값
        2. trailingEps 또는 forwardEps (직접 접근)
        3. netIncomeToCommon / sharesOutstanding (기본 계산)
        4. epsCurrentYear (기존 필드)
        5. currentPrice / trailingPE (밸류에이션 역산)
        
        Args:
            info: Provider가 반환한 표준화된 딕셔너리
            current_price: 현재 주가
            
        Returns:
            계산된 EPS 값 (float) 또는 None
        """
        # 표준화된 딕셔너리와 yfinance 형식 모두 지원
        calc_info = self._convert_to_calculator_format(info)
        
        # 1순위: trailingEps 또는 forwardEps 직접 접근
        eps = calc_info.get("trailingEps") or calc_info.get("forwardEps")
        if eps is not None:
            try:
                eps_float = float(eps)
                if eps_float > 0:
                    logger.info(f"[EPS Calculation] 1순위 성공: trailingEps/forwardEps = {eps_float}")
                    return eps_float
            except (ValueError, TypeError):
                pass
        
        # 2순위: netIncomeToCommon / sharesOutstanding
        net_income = calc_info.get("netIncomeToCommon")
        shares_outstanding = calc_info.get("sharesOutstanding")
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
        eps_current_year = calc_info.get("epsCurrentYear")
        if eps_current_year is not None:
            try:
                eps_float = float(eps_current_year)
                if eps_float > 0:
                    logger.info(f"[EPS Calculation] 3순위 성공: epsCurrentYear = {eps_float}")
                    return eps_float
            except (ValueError, TypeError):
                pass
        
        # 4순위: currentPrice / trailingPE (밸류에이션 역산)
        trailing_pe = calc_info.get("trailingPE")
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

