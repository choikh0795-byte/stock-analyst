import logging
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class StockCalculator:
    """계산 및 보정 로직 전담 (숫자 값만 반환)."""

    def calculate_current_price(self, info: Dict, stock) -> float:
        current_price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
            or info.get("open")
            or 0
        )

        if current_price == 0:
            try:
                hist = stock.history(period="5d")
                if not hist.empty:
                    current_price = float(hist["Close"].iloc[-1])
            except Exception:
                pass

        return current_price

    def calculate_pe_ratio(self, info: Dict, fdr_data: Dict, market_cap: Optional[float]) -> Optional[float]:
        pe_ratio = info.get("trailingPE")

        if not pe_ratio:
            try:
                net_income = info.get("netIncomeToCommon", 0)
                logger.info(f"[DEBUG] PER 계산 시도: 시가총액={market_cap}, 순이익={net_income}")
                if market_cap and market_cap > 0 and net_income and net_income > 0:
                    pe_ratio = round(market_cap / net_income, 2)
                    logger.info(f"[DEBUG] PER 계산 결과: {pe_ratio}")
                else:
                    logger.warning(
                        f"[DEBUG] PER 계산 불가: 시가총액={market_cap}, 순이익={net_income} (0 이하 값)"
                    )
            except Exception as e:
                logger.warning(f"[DEBUG] PER 계산 실패: {str(e)}")
                
        if not pe_ratio:
            pe_ratio = info.get("forwardPE")

        if not pe_ratio:
            pe_ratio = fdr_data.get("per", 0.0)
            logger.info(f"[DEBUG] PER FDR 캐시 사용: {pe_ratio}")

        return pe_ratio

    def _calculate_total_equity_from_info(self, info: Dict) -> Optional[float]:
        total_equity = info.get("totalStockholderEquity") or info.get("totalEquity")
        if not total_equity:
            total_assets = info.get("totalAssets", 0)
            total_liabilities = info.get("totalLiabilities", 0)
            if total_assets > 0 and total_liabilities >= 0:
                total_equity = total_assets - total_liabilities
                logger.info(
                    f"[DEBUG] PBR 3차 계산: 자본총계 계산 (자산={total_assets}, 부채={total_liabilities}, 자본={total_equity})"
                )
        return total_equity

    def _calculate_total_equity_from_balance_sheet(self, stock) -> Optional[float]:
        try:
            balance_sheet = stock.balance_sheet
            if balance_sheet is not None and not balance_sheet.empty:
                latest_date = balance_sheet.columns[0]
                logger.info(f"[DEBUG] PBR 4차 계산: 최신 재무상태표 날짜 = {latest_date}")

                equity_keywords = [
                    "Stockholders Equity",
                    "Total Stockholder Equity",
                    "Total Equity Gross Minority Interest",
                    "Total Stockholders' Equity",
                    "Stockholders' Equity",
                ]

                for keyword in equity_keywords:
                    matching_rows = balance_sheet.index[
                        balance_sheet.index.str.contains(keyword, case=False, na=False)
                    ]
                    if len(matching_rows) > 0:
                        total_equity = balance_sheet.loc[matching_rows[0], latest_date]
                        logger.info(f"[DEBUG] PBR 4차 계산: '{keyword}' 키워드로 자본총계 발견 = {total_equity}")
                        return total_equity

                logger.warning(
                    f"[DEBUG] PBR 4차 계산: balance_sheet에서 자본총계 항목을 찾을 수 없음. 인덱스 목록: {list(balance_sheet.index)}"
                )
        except Exception as e:
            logger.warning(f"[DEBUG] PBR 4차 계산 실패: {str(e)}")

        return None

    def calculate_pb_ratio(
        self,
        info: Dict,
        current_price: float,
        fdr_data: Dict,
        market_cap: Optional[float],
        stock,
    ) -> Optional[float]:
        pb_ratio = info.get("priceToBook")

        if not pb_ratio:
            try:
                book_value = info.get("bookValue")
                logger.info(f"[DEBUG] PBR 계산 시도: 현재가={current_price}, BPS={book_value}")
                if current_price > 0 and book_value and book_value > 0:
                    pb_ratio = round(current_price / book_value, 2)
                    logger.info(f"[DEBUG] PBR 계산 결과: {pb_ratio}")
                else:
                    logger.warning(
                        f"[DEBUG] PBR 계산 불가: 현재가={current_price}, BPS={book_value} (0 이하 값 또는 None)"
                    )
            except Exception as e:
                logger.warning(f"[DEBUG] PBR 계산 실패: {str(e)}")

        if not pb_ratio:
            try:
                total_equity = self._calculate_total_equity_from_info(info)
                logger.info(f"[DEBUG] PBR 3차 계산 시도: 시가총액={market_cap}, 자본총계={total_equity}")
                if market_cap and market_cap > 0 and total_equity and total_equity > 0:
                    pb_ratio = round(market_cap / total_equity, 2)
                    logger.info(f"[Calculation] PBR 2차 계산 성공(시총/자본): {pb_ratio}")
                else:
                    logger.warning(
                        f"[DEBUG] PBR 3차 계산 불가: 시가총액={market_cap}, 자본총계={total_equity} (0 이하 값 또는 None)"
                    )
            except Exception as e:
                logger.warning(f"[DEBUG] PBR 3차 계산 실패: {str(e)}")

        if not pb_ratio:
            try:
                if market_cap and market_cap > 0:
                    logger.info(f"[DEBUG] PBR 4차 계산 시도: balance_sheet 조회 시작")
                    total_equity = self._calculate_total_equity_from_balance_sheet(stock)

                    if total_equity is None:
                        logger.warning(
                            "[DEBUG] PBR 4차 계산: balance_sheet에서 자본총계 항목을 찾을 수 없음."
                        )
                    elif pd.notna(total_equity) and float(total_equity) > 0:
                        pb_ratio = round(market_cap / float(total_equity), 2)
                        logger.info(f"[Calculation] PBR 4차 계산 성공(BalanceSheet): {pb_ratio}")
                    else:
                        logger.warning(f"[DEBUG] PBR 4차 계산 불가: 자본총계 값이 유효하지 않음 ({total_equity})")
            except Exception as e:
                logger.warning(f"[DEBUG] PBR 4차 계산 실패: {str(e)}")

        if not pb_ratio:
            pb_ratio = fdr_data.get("pbr", 0.0)
            logger.info(f"[DEBUG] PBR FDR 캐시 사용: {pb_ratio}")

        return pb_ratio

    def calculate_pb_ratio_without_stock(
        self,
        info: Dict,
        current_price: float,
        fdr_data: Dict,
        market_cap: Optional[float],
    ) -> Optional[float]:
        """
        stock 객체 없이 PBR을 계산합니다.
        balance_sheet 조회 단계는 건너뜁니다.
        """
        pb_ratio = info.get("priceToBook")

        if not pb_ratio:
            try:
                book_value = info.get("bookValue")
                logger.info(f"[DEBUG] PBR 계산 시도: 현재가={current_price}, BPS={book_value}")
                if current_price > 0 and book_value and book_value > 0:
                    pb_ratio = round(current_price / book_value, 2)
                    logger.info(f"[DEBUG] PBR 계산 결과: {pb_ratio}")
                else:
                    logger.warning(
                        f"[DEBUG] PBR 계산 불가: 현재가={current_price}, BPS={book_value} (0 이하 값 또는 None)"
                    )
            except Exception as e:
                logger.warning(f"[DEBUG] PBR 계산 실패: {str(e)}")

        if not pb_ratio:
            try:
                total_equity = self._calculate_total_equity_from_info(info)
                logger.info(f"[DEBUG] PBR 3차 계산 시도: 시가총액={market_cap}, 자본총계={total_equity}")
                if market_cap and market_cap > 0 and total_equity and total_equity > 0:
                    pb_ratio = round(market_cap / total_equity, 2)
                    logger.info(f"[Calculation] PBR 2차 계산 성공(시총/자본): {pb_ratio}")
                else:
                    logger.warning(
                        f"[DEBUG] PBR 3차 계산 불가: 시가총액={market_cap}, 자본총계={total_equity} (0 이하 값 또는 None)"
                    )
            except Exception as e:
                logger.warning(f"[DEBUG] PBR 3차 계산 실패: {str(e)}")

        # stock 객체가 없으므로 balance_sheet 조회 단계는 건너뜀

        if not pb_ratio:
            pb_ratio = fdr_data.get("pbr", 0.0)
            logger.info(f"[DEBUG] PBR FDR 캐시 사용: {pb_ratio}")

        return pb_ratio

    def calculate_dividend_yield(self, info: Dict, fdr_data: Dict, is_korean: bool) -> float:
        # is_korean is kept for interface compatibility
        _ = is_korean

        dividend_rate = info.get("dividendRate")
        current_price = info.get("currentPrice")
        raw_dividend_yield = info.get("dividendYield")
        fdr_dividend_yield = fdr_data.get("dividend_yield")

        # 1) 직접 계산: dividendRate / currentPrice
        try:
            if dividend_rate is not None and current_price is not None:
                rate_value = float(dividend_rate)
                price_value = float(current_price)

                if rate_value > 0 and price_value > 0:
                    manual_dividend_yield = (rate_value / price_value) * 100
                    logger.info(
                        f"[Calculation] 배당률 1차(직접 계산) 성공: dividendRate={rate_value}, "
                        f"currentPrice={price_value}, yield={manual_dividend_yield}"
                    )
                    return float(manual_dividend_yield)
        except Exception as e:
            logger.warning(f"[DEBUG] 배당률 직접 계산 실패: {e}")

        # 2) yfinance dividendYield 필드 활용 (단위 보정 포함)
        try:
            if raw_dividend_yield is not None:
                dividend_yield = float(raw_dividend_yield)
                if dividend_yield < 1.0:
                    dividend_yield = dividend_yield * 100

                logger.info(
                    f"[Calculation] 배당률 2차(yfinance dividendYield) 사용: raw={raw_dividend_yield}, "
                    f"normalized={dividend_yield}"
                )
                return float(dividend_yield)
        except Exception as e:
            logger.warning(f"[DEBUG] 배당률 yfinance 보정 실패: {e}")

        # 3) FDR 캐시 fallback
        try:
            if fdr_dividend_yield is not None:
                dividend_yield = float(fdr_dividend_yield)
                logger.info(f"[Calculation] 배당률 3차(FDR) 사용: {dividend_yield}")
                return dividend_yield
        except Exception as e:
            logger.warning(f"[DEBUG] 배당률 FDR 변환 실패: {e}")

        return 0.0

    def calculate_roe(self, info: Dict, stock) -> Optional[float]:
        return_on_equity = info.get("returnOnEquity")
        roe = None
        if return_on_equity is not None:
            roe = round(return_on_equity * 100, 2)
            logger.info(f"[Calculation] ROE 1차 성공 (info.returnOnEquity): {roe}")

        if not roe:
            try:
                net_income = info.get("netIncomeToCommon", 0)
                total_equity = info.get("totalStockholderEquity") or info.get("totalEquity", 0)

                if not total_equity or total_equity == 0:
                    total_assets = info.get("totalAssets", 0)
                    total_liabilities = info.get("totalLiabilities", 0)
                    if total_assets > 0 and total_liabilities >= 0:
                        total_equity = total_assets - total_liabilities
                        logger.info(
                            f"[Calculation] ROE 2차 계산: 자본총계 계산 (자산={total_assets}, 부채={total_liabilities}, 자본={total_equity})"
                        )

                logger.info(f"[Calculation] ROE 2차 계산 시도: 순이익={net_income}, 자본총계={total_equity}")
                if net_income and net_income > 0 and total_equity and total_equity > 0:
                    roe = round((net_income / total_equity) * 100, 2)
                    logger.info(f"[Calculation] ROE 2차 계산 성공(순이익/자본): {roe}%")
                else:
                    logger.warning(
                        f"[Calculation] ROE 2차 계산 불가: 순이익={net_income}, 자본총계={total_equity} (0 이하 값 또는 None)"
                    )
            except Exception as e:
                logger.warning(f"[Calculation] ROE 2차 계산 실패: {str(e)}")

        if not roe:
            try:
                logger.info(f"[Calculation] ROE 3차 계산 시도: balance_sheet 및 income_stmt 조회 시작")

                balance_sheet = stock.balance_sheet
                total_equity = None

                if balance_sheet is not None and not balance_sheet.empty:
                    latest_date = balance_sheet.columns[0]
                    logger.info(f"[Calculation] ROE 3차 계산: 최신 재무상태표 날짜 = {latest_date}")

                    equity_keywords = [
                        "Stockholders Equity",
                        "Total Stockholder Equity",
                        "Total Equity Gross Minority Interest",
                        "Total Stockholders' Equity",
                        "Stockholders' Equity",
                    ]

                    for keyword in equity_keywords:
                        matching_rows = balance_sheet.index[
                            balance_sheet.index.str.contains(keyword, case=False, na=False)
                        ]
                        if len(matching_rows) > 0:
                            total_equity = balance_sheet.loc[matching_rows[0], latest_date]
                            logger.info(
                                f"[Calculation] ROE 3차 계산: '{keyword}' 키워드로 자본총계 발견 = {total_equity}"
                            )
                            break

                income_stmt = stock.income_stmt
                net_income = None

                if income_stmt is not None and not income_stmt.empty:
                    latest_date_income = income_stmt.columns[0]
                    logger.info(f"[Calculation] ROE 3차 계산: 최신 손익계산서 날짜 = {latest_date_income}")

                    income_keywords = [
                        "Net Income",
                        "Net Income Common Stockholders",
                        "Net Income Available To Common Stockholders",
                        "Net Income After Taxes",
                    ]

                    for keyword in income_keywords:
                        matching_rows = income_stmt.index[
                            income_stmt.index.str.contains(keyword, case=False, na=False)
                        ]
                        if len(matching_rows) > 0:
                            net_income = income_stmt.loc[matching_rows[0], latest_date_income]
                            logger.info(f"[Calculation] ROE 3차 계산: '{keyword}' 키워드로 순이익 발견 = {net_income}")
                            break

                if total_equity is not None and pd.notna(total_equity) and float(total_equity) > 0:
                    if net_income is not None and pd.notna(net_income):
                        roe = round((float(net_income) / float(total_equity)) * 100, 2)
                        logger.info(f"[Calculation] ROE 3차 계산 성공(BalanceSheet+IncomeStmt): {roe}%")
                    else:
                        logger.warning(f"[Calculation] ROE 3차 계산 불가: 순이익을 찾을 수 없음")
                else:
                    logger.warning(f"[Calculation] ROE 3차 계산 불가: 자본총계를 찾을 수 없거나 유효하지 않음")

            except Exception as e:
                logger.warning(f"[Calculation] ROE 3차 계산 실패: {str(e)}")

        return roe

    def calculate_roe_without_stock(self, info: Dict) -> Optional[float]:
        """
        stock 객체 없이 ROE를 계산합니다.
        balance_sheet와 income_stmt 조회 단계는 건너뜁니다.
        """
        return_on_equity = info.get("returnOnEquity")
        roe = None
        if return_on_equity is not None:
            roe = round(return_on_equity * 100, 2)
            logger.info(f"[Calculation] ROE 1차 성공 (info.returnOnEquity): {roe}")

        if not roe:
            try:
                net_income = info.get("netIncomeToCommon", 0)
                total_equity = info.get("totalStockholderEquity") or info.get("totalEquity", 0)

                if not total_equity or total_equity == 0:
                    total_assets = info.get("totalAssets", 0)
                    total_liabilities = info.get("totalLiabilities", 0)
                    if total_assets > 0 and total_liabilities >= 0:
                        total_equity = total_assets - total_liabilities
                        logger.info(
                            f"[Calculation] ROE 2차 계산: 자본총계 계산 (자산={total_assets}, 부채={total_liabilities}, 자본={total_equity})"
                        )

                logger.info(f"[Calculation] ROE 2차 계산 시도: 순이익={net_income}, 자본총계={total_equity}")
                if net_income and net_income > 0 and total_equity and total_equity > 0:
                    roe = round((net_income / total_equity) * 100, 2)
                    logger.info(f"[Calculation] ROE 2차 계산 성공(순이익/자본): {roe}%")
                else:
                    logger.warning(
                        f"[Calculation] ROE 2차 계산 불가: 순이익={net_income}, 자본총계={total_equity} (0 이하 값 또는 None)"
                    )
            except Exception as e:
                logger.warning(f"[Calculation] ROE 2차 계산 실패: {str(e)}")

        # stock 객체가 없으므로 balance_sheet와 income_stmt 조회 단계는 건너뜀

        return roe

    def calculate_volatility(self, info: Dict, stock) -> Tuple[Optional[float], Optional[str]]:
        volatility = None
        volatility_type = None

        beta = info.get("beta")
        if beta is not None:
            volatility = beta
            volatility_type = "beta"
            logger.info(f"[Calculation] 변동성 1차 성공 (info.beta): {beta}")

        if not volatility:
            try:
                logger.info(f"[Calculation] 변동성 2차 계산 시도: stock.history(period='1y') 조회 시작")
                hist = stock.history(period="1y")

                if hist is not None and not hist.empty and len(hist) > 1:
                    closes = hist["Close"]
                    daily_returns = closes.pct_change().dropna()

                    if len(daily_returns) > 0:
                        daily_std = daily_returns.std()
                        annual_volatility = daily_std * np.sqrt(252)
                        volatility = round(annual_volatility * 100, 2)
                        volatility_type = "historical"
                        logger.info(f"[Calculation] 변동성 2차 계산 성공(Historical Volatility): {volatility}% (1년)")
                    else:
                        logger.warning(f"[Calculation] 변동성 2차 계산 불가: 일일 수익률 계산 실패")
                else:
                    logger.warning(
                        f"[Calculation] 변동성 2차 계산 불가: history 데이터가 없거나 부족함 (길이: {len(hist) if hist is not None and not hist.empty else 0})"
                    )
            except Exception as e:
                logger.warning(f"[Calculation] 변동성 2차 계산 실패: {str(e)}")

        return volatility, volatility_type

    def calculate_profit_margin(self, info: Dict) -> Optional[float]:
        """
        순이익률(Profit Margin) 계산
        
        Args:
            info: yfinance info 딕셔너리
            
        Returns:
            Optional[float]: 순이익률 (0~1 사이의 값, None일 경우 계산 불가)
        """
        try:
            # profitMargins 필드 직접 사용
            profit_margin = info.get("profitMargins")
            if profit_margin is not None:
                return float(profit_margin)
            
            # netIncomeToCommon / totalRevenue로 계산
            net_income = info.get("netIncomeToCommon")
            total_revenue = info.get("totalRevenue")
            
            if net_income is not None and total_revenue is not None and total_revenue > 0:
                profit_margin = net_income / total_revenue
                return float(profit_margin)
        except Exception as e:
            logger.warning(f"[Calculation] Profit Margin 계산 실패: {str(e)}")
        
        return None

    def _score_profitability(self, roe: Optional[float], profit_margin: Optional[float]) -> float:
        """
        수익성 점수 계산 (가중치 40%)
        
        Args:
            roe: ROE 값 (% 단위, 예: 15.5)
            profit_margin: 순이익률 (0~1 사이, 예: 0.15)
            
        Returns:
            float: 0~100 사이의 점수
        """
        roe_score = 50.0  # 기본값 (Neutral)
        profit_margin_score = 50.0  # 기본값 (Neutral)
        
        # ROE 점수 계산
        if roe is not None:
            if roe > 20:
                roe_score = 100.0
            elif roe >= 10:
                # 10~20% 사이: 선형 보간 (50~100점)
                roe_score = 50.0 + ((roe - 10) / 10) * 50.0
            elif roe >= 0:
                # 0~10% 사이: 선형 보간 (0~50점)
                roe_score = (roe / 10) * 50.0
            else:
                # 음수: 감점 (0점)
                roe_score = 0.0
        
        # Profit Margin 점수 계산
        if profit_margin is not None:
            # profit_margin을 퍼센트로 변환 (0.15 -> 15%)
            profit_margin_pct = profit_margin * 100
            
            if profit_margin_pct > 20:
                profit_margin_score = 100.0
            elif profit_margin_pct >= 10:
                # 10~20% 사이: 선형 보간 (50~100점)
                profit_margin_score = 50.0 + ((profit_margin_pct - 10) / 10) * 50.0
            elif profit_margin_pct >= 0:
                # 0~10% 사이: 선형 보간 (0~50점)
                profit_margin_score = (profit_margin_pct / 10) * 50.0
            else:
                # 음수: 감점 (0점)
                profit_margin_score = 0.0
        
        # ROE와 Profit Margin의 평균 (각 50% 가중치)
        profitability_score = (roe_score * 0.5) + (profit_margin_score * 0.5)
        return round(profitability_score, 1)

    def _score_valuation(self, pe_ratio: Optional[float], pb_ratio: Optional[float]) -> float:
        """
        밸류에이션 점수 계산 (가중치 30%)
        
        Args:
            pe_ratio: PER 값
            pb_ratio: PBR 값
            
        Returns:
            float: 0~100 사이의 점수
        """
        pe_score = 50.0  # 기본값 (Neutral)
        pb_score = 50.0  # 기본값 (Neutral)
        
        # PER 점수 계산
        if pe_ratio is not None and pe_ratio > 0:
            if pe_ratio <= 10:
                # 0~10: 고득점 (저평가)
                pe_score = 100.0 - ((pe_ratio / 10) * 20.0)  # 10일 때 80점, 0일 때 100점
            elif pe_ratio <= 20:
                # 10~20: 중간 점수
                pe_score = 80.0 - ((pe_ratio - 10) / 10) * 30.0  # 20일 때 50점
            elif pe_ratio <= 30:
                # 20~30: 낮은 점수
                pe_score = 50.0 - ((pe_ratio - 20) / 10) * 30.0  # 30일 때 20점
            else:
                # 30 이상: 매우 낮은 점수 (고평가)
                pe_score = max(0.0, 20.0 - ((pe_ratio - 30) / 10) * 10.0)  # 40일 때 10점, 그 이상은 0점에 수렴
        
        # PBR 점수 계산
        if pb_ratio is not None and pb_ratio > 0:
            if pb_ratio <= 1:
                # 0~1: 고득점 (저평가)
                pb_score = 100.0 - (pb_ratio * 20.0)  # 1일 때 80점, 0일 때 100점
            elif pb_ratio <= 2:
                # 1~2: 중간 점수
                pb_score = 80.0 - ((pb_ratio - 1) * 30.0)  # 2일 때 50점
            elif pb_ratio <= 3:
                # 2~3: 낮은 점수
                pb_score = 50.0 - ((pb_ratio - 2) * 30.0)  # 3일 때 20점
            else:
                # 3 이상: 매우 낮은 점수
                pb_score = max(0.0, 20.0 - ((pb_ratio - 3) * 5.0))  # 4일 때 15점, 그 이상은 0점에 수렴
        
        # PER과 PBR의 평균 (각 50% 가중치)
        valuation_score = (pe_score * 0.5) + (pb_score * 0.5)
        return round(valuation_score, 1)

    def _score_momentum(
        self,
        current_price: float,
        fifty_two_week_low: Optional[float],
        fifty_two_week_high: Optional[float],
    ) -> float:
        """
        모멘텀/추세 점수 계산 (가중치 20%)
        
        Args:
            current_price: 현재가
            fifty_two_week_low: 52주 최저가
            fifty_two_week_high: 52주 최고가
            
        Returns:
            float: 0~100 사이의 점수
        """
        if (
            fifty_two_week_low is None
            or fifty_two_week_high is None
            or fifty_two_week_low >= fifty_two_week_high
        ):
            return 50.0  # 기본값 (Neutral)
        
        # 현재가가 52주 범위 내에서 어느 위치에 있는지 계산 (0~1)
        price_range = fifty_two_week_high - fifty_two_week_low
        if price_range <= 0:
            return 50.0
        
        position_ratio = (current_price - fifty_two_week_low) / price_range
        
        # 52주 최고가에 근접할수록 높은 점수
        # position_ratio가 1.0에 가까울수록 (최고가 근처) 높은 점수
        # position_ratio가 0.0에 가까울수록 (최저가 근처) 낮은 점수
        momentum_score = 20.0 + (position_ratio * 80.0)  # 0.0일 때 20점, 1.0일 때 100점
        
        return round(momentum_score, 1)

    def _score_stability(self, market_cap: Optional[float], beta: Optional[float]) -> float:
        """
        수급/안정성 점수 계산 (가중치 10%)
        
        Args:
            market_cap: 시가총액 (숫자 또는 문자열)
            beta: Beta 값
            
        Returns:
            float: 0~100 사이의 점수
        """
        market_cap_score = 50.0  # 기본값 (Neutral)
        beta_score = 50.0  # 기본값 (Neutral)
        
        # Market Cap 점수 계산
        if market_cap is not None:
            try:
                # 문자열인 경우 숫자로 변환
                if isinstance(market_cap, str):
                    market_cap_numeric = float(market_cap)
                else:
                    market_cap_numeric = float(market_cap)
                
                # 시가총액이 클수록 안정성 점수 가산
                # 1조 이상: 100점, 1000억 이상: 80점, 100억 이상: 60점, 그 이하: 40점
                if market_cap_numeric >= 1_000_000_000_000:  # 1조 이상
                    market_cap_score = 100.0
                elif market_cap_numeric >= 100_000_000_000:  # 1000억 이상
                    market_cap_score = 80.0
                elif market_cap_numeric >= 10_000_000_000:  # 100억 이상
                    market_cap_score = 60.0
                else:
                    market_cap_score = 40.0
            except (ValueError, TypeError):
                pass
        
        # Beta 점수 계산
        if beta is not None:
            # Beta가 1 내외면 안정적, 너무 높으면 리스크 감점
            if 0.8 <= beta <= 1.2:
                # 0.8~1.2: 안정적 (고득점)
                beta_score = 100.0
            elif 0.5 <= beta < 0.8 or 1.2 < beta <= 1.5:
                # 0.5~0.8 또는 1.2~1.5: 보통
                if beta < 1.0:
                    beta_score = 80.0 + ((beta - 0.5) / 0.3) * 20.0  # 0.5일 때 80점, 0.8일 때 100점
                else:
                    beta_score = 100.0 - ((beta - 1.2) / 0.3) * 20.0  # 1.2일 때 100점, 1.5일 때 80점
            elif beta < 0.5:
                # 0.5 미만: 너무 낮음 (방어적이지만 성장성 낮음)
                beta_score = 60.0 + ((beta / 0.5) * 20.0)  # 0일 때 60점, 0.5일 때 80점
            else:
                # 1.5 초과: 변동성 높음 (리스크)
                beta_score = max(0.0, 80.0 - ((beta - 1.5) * 10.0))  # 1.5일 때 80점, 2.5일 때 0점
        
        # Market Cap과 Beta의 평균 (각 50% 가중치)
        stability_score = (market_cap_score * 0.5) + (beta_score * 0.5)
        return round(stability_score, 1)

    def calculate_score(
        self,
        stock_data: Dict,
        roe: Optional[float] = None,
        pe_ratio: Optional[float] = None,
        pb_ratio: Optional[float] = None,
        market_cap: Optional[float] = None,
        beta: Optional[float] = None,
        info: Optional[Dict] = None,
    ) -> float:
        """
        종합 투자 점수 계산 (가중치 기반 알고리즘)
        
        점수 산정 공식:
        Total = (수익성 * 0.4) + (밸류에이션 * 0.3) + (모멘텀 * 0.2) + (안정성 * 0.1)
        
        Args:
            stock_data: 주식 정보 딕셔너리 (current_price, fifty_two_week_low, fifty_two_week_high 등 포함)
            roe: ROE 값 (% 단위)
            pe_ratio: PER 값
            pb_ratio: PBR 값
            market_cap: 시가총액 (숫자 또는 문자열)
            beta: Beta 값
            info: yfinance info 딕셔너리 (Profit Margin 계산용)
            
        Returns:
            float: 0~100 사이의 점수 (소수점 첫째 자리까지)
        """
        # Profit Margin 계산
        info_dict = info or stock_data.get("_info", {})
        profit_margin = self.calculate_profit_margin(info_dict)
        
        # 각 영역별 점수 계산
        profitability_score = self._score_profitability(roe, profit_margin)
        valuation_score = self._score_valuation(pe_ratio, pb_ratio)
        
        current_price = stock_data.get("current_price", 0)
        fifty_two_week_low = stock_data.get("fifty_two_week_low")
        fifty_two_week_high = stock_data.get("fifty_two_week_high")
        momentum_score = self._score_momentum(current_price, fifty_two_week_low, fifty_two_week_high)
        
        stability_score = self._score_stability(market_cap, beta)
        
        # 가중치 합산
        total_score = (
            (profitability_score * 0.4)
            + (valuation_score * 0.3)
            + (momentum_score * 0.2)
            + (stability_score * 0.1)
        )
        
        # 0~100 범위로 제한
        total_score = max(0.0, min(100.0, total_score))
        
        logger.info(
            f"[Calculation] 점수 계산 완료: "
            f"수익성={profitability_score}, 밸류={valuation_score}, "
            f"모멘텀={momentum_score}, 안정성={stability_score}, "
            f"종합={total_score:.1f}"
        )
        
        return round(total_score, 1)

