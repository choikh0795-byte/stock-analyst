/**
 * 주식 지표에 대한 초보자용 설명 상수
 */

export interface MetricDefinition {
  label: string
  icon: string
  definition: string
  key: 'pe_ratio' | 'pb_ratio' | 'return_on_equity' | 'dividend_yield' | 'beta' | 'target_mean_price'
}

export const METRIC_DEFINITIONS: Record<string, MetricDefinition> = {
  pe_ratio: {
    label: 'PER',
    icon: '🏷️',
    definition: '기업이 벌어들이는 이익 대비 주가가 얼마나 비싼지를 나타내는 지표야. 낮을수록 저평가되었다고 봐. 보통 10~20배가 적정선이고, 10 이하는 저평가, 30 이상은 고평가로 봐.',
    key: 'pe_ratio',
  },
  pb_ratio: {
    label: 'PBR',
    icon: '🏢',
    definition: '주가를 주당 순자산으로 나눈 값이야. 기업의 자산 대비 주가가 얼마나 비싼지 보여줘. 1 이하는 저평가, 1~2배가 적정선, 3 이상은 고평가로 봐.',
    key: 'pb_ratio',
  },
  return_on_equity: {
    label: 'ROE',
    icon: '👑',
    definition: '자기자본 대비 얼마나 수익을 내는지 보여주는 지표야. 높을수록 기업의 수익성이 좋다는 뜻이야. 보통 15% 이상이면 우수한 편이고, 10% 미만이면 개선이 필요해.',
    key: 'return_on_equity',
  },
  dividend_yield: {
    label: '배당률',
    icon: '💰',
    definition: '주가 대비 배당금이 얼마나 되는지 보여주는 지표야. 높을수록 배당을 많이 주는 종목이야. 보통 2~4%가 적정선이고, 5% 이상이면 배당주로 분류해.',
    key: 'dividend_yield',
  },
  beta: {
    label: '변동성 (Beta)',
    icon: '📊',
    definition: '시장 대비 주가 변동성이 얼마나 큰지 보여주는 지표야. 1보다 크면 시장보다 변동성이 크고, 1보다 작으면 시장보다 안정적이야. 높을수록 리스크가 크지만 수익 기대치도 커.',
    key: 'beta',
  },
  target_mean_price: {
    label: '목표가',
    icon: '🎯',
    definition: '애널리스트들이 예상하는 목표 주가야. 현재가보다 높으면 상승 여력이 있다는 뜻이고, 낮으면 하락 가능성이 있어. 다만 목표가는 참고용으로만 봐야 해.',
    key: 'target_mean_price',
  },
}

export const METRIC_KEYS = Object.keys(METRIC_DEFINITIONS) as Array<keyof typeof METRIC_DEFINITIONS>

