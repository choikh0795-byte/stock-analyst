import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional

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

    def get_stock_info(self, ticker: str, db: Session) -> Dict:
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
            return cached_log.analysis_json.get("stock_data", {})

        # Provider에서 표준화된 딕셔너리 직접 받기
        info = self.provider.get_stock_info(ticker)

        # Provider가 이미 계산한 current_price 사용
        current_price = info.get("current_price") or 0.0
        fdr_data = {}  # 캐시 제거로 인해 빈 딕셔너리 사용

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

        roe = info.get("roe")
        if not roe:
            calc_info = self._convert_to_calculator_format(info)
            # PBR/PER 백업 데이터 준비 (Yahoo 실패 시 KIS/FDR 데이터 활용)
            backup_data = {
                "pbr": pb_ratio,
                "pb_ratio": pb_ratio,
                "per": pe_ratio,
                "pe_ratio": pe_ratio,
            }
            roe = self.calculator.calculate_roe_without_stock(calc_info, backup_data)
        
        # EPS 계산: Calculator 사용
        eps = info.get("eps")
        if eps is None:
            calc_info = self._convert_to_calculator_format(info)
            eps = self.calculator.calculate_eps(calc_info, current_price)

        # 부채비율: Calculator 사용
        debt_ratio = info.get("debt_ratio")
        if debt_ratio is None:
            calc_info = self._convert_to_calculator_format(info)
            debt_ratio = self.calculator.calculate_debt_ratio(calc_info)

        previous_close = info.get("previous_close")
        fifty_two_week_low = info.get("fifty_two_week_low")
        fifty_two_week_high = info.get("fifty_two_week_high")
        target_mean_price = info.get("target_mean_price")
        beta = info.get("beta")

        # 가격 변동 계산 (previous_close가 유효할 때만 계산)
        change_value = None
        change_percentage = None
        change_status = "NEUTRAL"

        if previous_close is not None and previous_close > 0:
            change_value = current_price - previous_close
            change_percentage = (change_value / previous_close) * 100
            change_status = self.formatter.get_change_status(current_price, previous_close)
            logger.info(
                f"[StockService] 등락률 계산: 현재가={current_price}, 전일종가={previous_close}, "
                f"등락액={change_value}, 등락률={change_percentage:.2f}%"
            )
        else:
            logger.warning(
                f"[StockService] 등락률 계산 불가: 현재가={current_price}, 전일종가={previous_close} "
                f"(전일종가가 None 또는 0 이하)"
            )

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
        debt_ratio_str = self.formatter.format_debt_ratio(debt_ratio)
        pe_ratio_str = self.formatter.format_pe_ratio(pe_ratio, is_korean)
        pb_ratio_str = self.formatter.format_pb_ratio(pb_ratio, is_korean)
        beta_str = self.formatter.format_beta(beta)
        change_value_str = self.formatter.format_change_value(change_value, is_korean)
        change_percentage_str = self.formatter.format_change_percentage(change_percentage)
        target_upside_str = self.formatter.format_target_upside(target_upside)

        is_korean_stock = is_korean
        currency_symbol = "₩" if is_korean else "$"

        stock_name = info.get("name") or ticker

        # market_cap을 문자열로 변환 (스키마 호환성)
        if market_cap is not None:
            try:
                # float로 먼저 변환 후 int로 변환 (소수점 제거)
                market_cap_str_value = str(int(float(market_cap)))
            except (ValueError, TypeError) as e:
                logger.warning(f"market_cap 변환 실패: {e}")
                market_cap_str_value = None
        else:
            market_cap_str_value = None
        
        # ETF 전용 필드 추출 및 포맷팅
        total_assets = info.get("total_assets")
        dividend_yield = info.get("dividend_yield")
        premium_discount = info.get("premium_discount")
        inception_date = info.get("inception_date")
        average_volume = info.get("average_volume")
        change_52week = info.get("change_52week")
        top_holdings = info.get("top_holdings", [])

        # 포맷터가 None 처리를 하므로 항상 호출 (N/A 반환)
        total_assets_str = self.formatter.format_total_assets(total_assets, is_korean)
        dividend_yield_str = self.formatter.format_percentage(dividend_yield, 2)
        premium_discount_str = self.formatter.format_premium_discount(premium_discount)
        inception_date_str = self.formatter.format_inception_date(inception_date)
        average_volume_str = self.formatter.format_average_volume(average_volume)
        change_52week_str = self.formatter.format_52week_change(change_52week)

        data = {
            "name": stock_name,
            "symbol": ticker,
            "current_price": current_price,
            "previous_close": previous_close,
            "pe_ratio": pe_ratio,
            "pb_ratio": pb_ratio,
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
            "debt_ratio_str": debt_ratio_str,
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
            "debt_ratio": debt_ratio,
            # ETF 전용 필드 (6개)
            "total_assets": total_assets,
            "total_assets_str": total_assets_str,
            "dividend_yield": dividend_yield,
            "dividend_yield_str": dividend_yield_str,
            "premium_discount": premium_discount,
            "premium_discount_str": premium_discount_str,
            "inception_date": inception_date,
            "inception_date_str": inception_date_str,
            "average_volume": average_volume,
            "average_volume_str": average_volume_str,
            "change_52week": change_52week,
            "change_52week_str": change_52week_str,
            "top_holdings": top_holdings,
        }

        # market_cap 타입 최종 확인 및 강제 변환
        if 'market_cap' in data and data['market_cap'] is not None:
            if not isinstance(data['market_cap'], str):
                try:
                    data['market_cap'] = str(int(float(data['market_cap'])))
                except (ValueError, TypeError) as e:
                    logger.error(f"market_cap 강제 변환 실패: {e}")
                    data['market_cap'] = None

        # 자산 타입 판별
        asset_type = info.get("asset_type", "STOCK")

        # 점수 계산 (자산 타입별 알고리즘)
        if asset_type == "ETF":
            # ETF 점수 계산
            expense_ratio = info.get("expense_ratio")
            premium_discount = info.get("premium_discount")
            total_assets = info.get("total_assets")

            score = self.calculator.calculate_etf_score(
                stock_data=data,
                expense_ratio=expense_ratio,
                premium_discount=premium_discount,
                total_assets=total_assets,
            )
            logger.info(f"[StockService] ETF 점수 계산 완료: {score}")
        else:
            # 주식 점수 계산 (기존 로직)
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
            logger.info(f"[StockService] 주식 점수 계산 완료: {score}")

        data["score"] = score
        data["asset_type"] = asset_type

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

        logger.info(
            f"[StockService] 반환: {data['name']} / PER:{pe_ratio_str} / PBR:{pb_ratio_str} / ROE:{roe_str} / EPS:{eps_str} / Score:{score}"
        )
        
        self._save_to_db(db, ticker, data)

        return data

    def _convert_to_calculator_format(self, info: Dict) -> Dict:
        """
        Provider가 반환한 표준화된 딕셔너리를 calculator가 기대하는 형식으로 변환합니다.

        개선 사항 (v3):
        - _info 키가 있으면 원본 yfinance 데이터를 우선 사용
        - 표준화된 키를 yfinance 형식 키로 매핑
        """
        # _info가 있으면 원본 데이터 사용 (Yahoo Provider가 제공)
        if "_info" in info and info["_info"]:
            calc_info = info["_info"].copy()
            # 표준화된 값으로 덮어쓰기 (Provider가 이미 계산한 값 우선)
            if "current_price" in info:
                calc_info["currentPrice"] = info["current_price"]
            if "market_cap" in info:
                calc_info["marketCap"] = info["market_cap"]
            if "previous_close" in info:
                calc_info["previousClose"] = info["previous_close"]
            if "fifty_two_week_low" in info:
                calc_info["fiftyTwoWeekLow"] = info["fifty_two_week_low"]
            if "fifty_two_week_high" in info:
                calc_info["fiftyTwoWeekHigh"] = info["fifty_two_week_high"]
            if "target_mean_price" in info:
                calc_info["targetMeanPrice"] = info["target_mean_price"]
            return calc_info

        # _info가 없으면 기존 로직 (표준화된 키를 yfinance 형식 키로 매핑)
        calc_info = info.copy()
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

    def _save_to_db(self, db: Session, ticker: str, data: Dict) -> None:
        try:
            analysis_json = {"stock_data": data}
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

