/**
 * 주식/ETF 지표에 대한 초보자용 설명 상수
 */

export interface MetricDefinition {
  label: string
  icon: string
  definition: string
  summary?: string
  tip?: string
  key: 'pe_ratio' | 'pb_ratio' | 'roe' | 'return_on_equity' | 'debt_ratio' | 'beta' | 'eps' | 'target_mean_price' | 'total_assets' | 'premium_discount' | 'dividend_yield' | 'inception_date' | 'average_volume' | 'change_52week'
}

export const METRIC_DEFINITIONS: Record<string, MetricDefinition> = {
  pe_ratio: {
    label: 'PER',
    icon: '🏷️',
    definition: '기업이 벌어들이는 이익 대비 주가가 얼마나 비싼지를 나타내는 지표야. 낮을수록 저평가되었다고 봐. 보통 10~20배가 적정선이고, 10 이하는 저평가, 30 이상은 고평가로 봐.',
    summary: '기업이 벌어들이는 이익 대비 주가가 얼마나 비싼지 보는 지표야.',
    tip: '보통 10~20배가 적정, 10 이하는 저평가, 30 이상은 고평가로 봐. 같은 업종 평균과 함께 비교해봐.',
    key: 'pe_ratio',
  },
  pb_ratio: {
    label: 'PBR',
    icon: '🏢',
    definition: '주가를 주당 순자산으로 나눈 값이야. 기업의 자산 대비 주가가 얼마나 비싼지 보여줘. 1 이하는 저평가, 1~2배가 적정선, 3 이상은 고평가로 봐.',
    summary: '주가를 주당 순자산으로 나눈 값이야. 자산 대비 주가가 비싼지 가늠하는 지표야.',
    tip: '1 이하면 저평가, 1~2배는 적정, 3 이상은 고평가로 봐. 자산 비중이 큰 업종일수록 PBR이 낮은 편이니 업종 특성도 함께 보자.',
    key: 'pb_ratio',
  },
  roe: {
    label: 'ROE',
    icon: '👑',
    definition: '자기자본 대비 얼마나 수익을 내는지 보여주는 지표야. 높을수록 기업의 수익성이 좋다는 뜻이야. 보통 15% 이상이면 우수한 편이고, 10% 미만이면 개선이 필요해.',
    summary: '자기자본으로 얼마나 효율적으로 이익을 내는지 보여주는 지표야.',
    tip: '15% 이상이면 우수, 10% 이상이면 양호로 봐. 단일 수치보다 최근 3~5년 추세가 상승하는지 확인해봐.',
    key: 'roe',
  },
  // 구버전 키 호환
  return_on_equity: {
    label: 'ROE',
    icon: '👑',
    definition: '자기자본 대비 얼마나 수익을 내는지 보여주는 지표야. 높을수록 기업의 수익성이 좋다는 뜻이야. 보통 15% 이상이면 우수한 편이고, 10% 미만이면 개선이 필요해.',
    summary: '자기자본으로 얼마나 효율적으로 이익을 내는지 보여주는 지표야.',
    tip: '15% 이상이면 우수, 10% 이상이면 양호로 봐. 단일 수치보다 최근 3~5년 추세가 상승하는지 확인해봐.',
    key: 'return_on_equity',
  },
  debt_ratio: {
    label: '부채비율',
    icon: '⚖️',
    definition: '기업의 총부채를 자기자본으로 나눈 값이야. 기업이 얼마나 빚을 지고 있는지를 보여주는 지표야. 보통 100~200%가 적정선이고, 100% 이하면 안정적, 300% 이상이면 재무 리스크가 크다고 봐.',
    summary: '기업이 자기자본 대비 얼마나 부채를 지고 있는지 보여주는 지표야.',
    tip: '100% 이하면 매우 안정적, 100~200%는 적정, 300% 이상이면 재무 리스크가 높아. 업종별로 평균이 다르니 같은 업종과 비교해봐.',
    key: 'debt_ratio',
  },
  beta: {
    label: '변동성 (Beta)',
    icon: '📊',
    definition: '시장 대비 주가 변동성이 얼마나 큰지 보여주는 지표야. 1보다 크면 시장보다 변동성이 크고, 1보다 작으면 시장보다 안정적이야. 높을수록 리스크가 크지만 수익 기대치도 커.',
    summary: '시장 대비 주가가 얼마나 크게 흔들리는지 나타내는 변동성 지표야.',
    tip: '1보다 크면 시장보다 변동성이 크고, 1보다 작으면 더 안정적이야. 포트폴리오 리스크 조절할 때 참고해봐.',
    key: 'beta',
  },
  eps: {
    label: 'EPS (주당순이익)',
    icon: '💵',
    definition: '기업이 발행한 주식 1주당 얼마의 순이익을 내는지 보여주는 지표야. 높을수록 기업의 수익성이 좋다는 뜻이야. PER과 함께 보면 더 정확한 평가가 가능해. EPS가 높고 PER이 낮으면 저평가된 우량주로 볼 수 있어.',
    summary: '기업이 주식 1주당 얼마를 버는지 보여주는 지표야.',
    tip: '높을수록 수익성이 좋아. PER과 함께 보면 더 정확해!',
    key: 'eps',
  },
  target_mean_price: {
    label: '목표가',
    icon: '🎯',
    definition: '애널리스트들이 예상하는 목표 주가야. 현재가보다 높으면 상승 여력이 있다는 뜻이고, 낮으면 하락 가능성이 있어. 다만 목표가는 참고용으로만 봐야 해.',
    summary: '애널리스트들이 예상하는 목표 주가를 평균낸 값이야.',
    tip: '현재가와 목표가 차이(업사이드)를 보고, 의견 수가 충분한지 함께 확인해봐. 어디까지나 참고용이니 기업 펀더멘털과 같이 판단해.',
    key: 'target_mean_price',
  },
  // ===== ETF 전용 지표 (6개) =====
  total_assets: {
    label: '순자산 (AUM)',
    icon: '🏦',
    definition: 'ETF가 운용하는 총 자산 규모야. 클수록 유동성이 좋고 안정적이야. 보통 100억 달러 이상이면 대형 ETF로 봐. 작은 ETF는 상장폐지 위험이 있으니 주의해.',
    summary: 'ETF가 운용하는 총 자산 규모야. 클수록 유동성과 안정성이 좋아.',
    tip: '100억 달러 이상이면 대형 ETF로 안전해. 10억 달러 미만이면 유동성 리스크를 고려해봐.',
    key: 'total_assets',
  },
  premium_discount: {
    label: '괴리율',
    icon: '📏',
    definition: 'ETF 시장 가격과 순자산가치(NAV)의 차이를 나타내는 지표야. 0%에 가까울수록 추적이 정확하다는 뜻이야. ±0.50% 이내면 우수, ±1.00% 이상이면 추적 성능이 나쁘다고 봐.',
    summary: 'ETF 시장 가격이 순자산가치(NAV)와 얼마나 차이 나는지 보여주는 지표야.',
    tip: '±0.50% 이내면 우수한 추적 성능이야. 괴리율이 크면 매매 타이밍을 조절해봐.',
    key: 'premium_discount',
  },
  dividend_yield: {
    label: '배당수익률',
    icon: '💸',
    definition: 'ETF가 매년 지급하는 배당금을 주가로 나눈 값이야. 높을수록 배당 수익이 커. 보통 2~4%면 적정 수준이고, 5% 이상이면 고배당 ETF로 봐.',
    summary: 'ETF가 주는 연간 배당금을 주가로 나눈 비율이야.',
    tip: '2~4%면 적정, 5% 이상이면 고배당으로 봐. 배당 성장률도 함께 확인하면 좋아.',
    key: 'dividend_yield',
  },
  inception_date: {
    label: '설정일',
    icon: '📅',
    definition: 'ETF가 처음 만들어진 날짜야. 오래된 ETF일수록 운용 이력과 데이터가 많아서 신뢰도가 높아. 보통 3년 이상 운용된 ETF를 선호하는 편이야.',
    summary: 'ETF가 처음 설정된 날짜야. 오래될수록 운용 이력이 풍부해.',
    tip: '3년 이상 운용된 ETF가 신뢰도가 높아. 신생 ETF는 추적 성과를 충분히 확인해봐.',
    key: 'inception_date',
  },
  average_volume: {
    label: '평균 거래량',
    icon: '📊',
    definition: '하루 평균 몇 주가 거래되는지 보여주는 지표야. 거래량이 많을수록 유동성이 좋아서 원하는 가격에 사고팔기 쉬워. 보통 100만 주 이상이면 유동성이 좋다고 봐.',
    summary: '하루 평균 거래량이야. 많을수록 유동성이 좋아.',
    tip: '100만 주 이상이면 유동성 걱정 없어. 거래량이 적으면 매도할 때 손해 볼 수 있으니 주의해.',
    key: 'average_volume',
  },
  change_52week: {
    label: '52주 수익률',
    icon: '📈',
    definition: '지난 1년간 ETF 가격이 얼마나 올랐는지(또는 떨어졌는지) 보여주는 지표야. 양수면 수익, 음수면 손실이야. 시장 전체 흐름과 비교해보면 ETF 성과를 평가할 수 있어.',
    summary: '지난 1년간 가격 변동률이야. 성과를 한눈에 볼 수 있어.',
    tip: 'S&P 500 ETF(SPY) 수익률과 비교해보면 시장 대비 성과를 알 수 있어. 단기 변동보다는 장기 추세를 봐.',
    key: 'change_52week',
  },
}

export const METRIC_KEYS = Object.keys(METRIC_DEFINITIONS) as Array<keyof typeof METRIC_DEFINITIONS>

