/**
 * 주식 지표에 대한 초보자용 설명 상수
 */

export interface MetricDefinition {
  label: string
  icon: string
  definition: string
  summary?: string
  tip?: string
  key: 'pe_ratio' | 'pb_ratio' | 'roe' | 'return_on_equity' | 'dividend_yield' | 'beta' | 'eps' | 'target_mean_price'
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
  dividend_yield: {
    label: '배당률',
    icon: '💰',
    definition: '주가 대비 배당금이 얼마나 되는지 보여주는 지표야. 높을수록 배당을 많이 주는 종목이야. 보통 2~4%가 적정선이고, 5% 이상이면 배당주로 분류해.',
    summary: '주가 대비 배당금을 얼마나 주는지 비율로 보여주는 지표야.',
    tip: '2~4%면 적정, 5% 이상이면 고배당으로 봐. 배당락일·배당성향과 함께 보고, 배당이 꾸준했는지도 확인해봐.',
    key: 'dividend_yield',
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
}

export const METRIC_KEYS = Object.keys(METRIC_DEFINITIONS) as Array<keyof typeof METRIC_DEFINITIONS>

