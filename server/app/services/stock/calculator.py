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

    def calculate_dividend_yield(self, info: Dict, fdr_data: Dict, is_korean: bool) -> float:
        raw_dividend_yield = info.get("dividendYield")
        fdr_dividend_yield = fdr_data.get("dividend_yield")

        if is_korean:
            dividend_yield = fdr_dividend_yield if fdr_dividend_yield not in (None, 0) else raw_dividend_yield
        else:
            dividend_yield = raw_dividend_yield if raw_dividend_yield not in (None, 0) else fdr_dividend_yield

        try:
            if dividend_yield is None:
                dividend_yield = 0.0
            else:
                dividend_yield = float(dividend_yield)
                if dividend_yield > 1:
                    dividend_yield = round(dividend_yield / 100, 6)
        except Exception as e:
            logger.warning(f"[DEBUG] 배당률 정규화 실패: {e}")
            dividend_yield = 0.0

        return dividend_yield

    def calculate_roe(self, info: Dict, stock) -> Optional[float]:
        roe = round(info.get("returnOnEquity") * 100, 2)
        if roe:
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

