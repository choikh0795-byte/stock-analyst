export interface Asset {
  id: number
  ticker: string
  name_en: string
  name_kr: string | null
  exchange: string
  asset_type: string
  country: string
  currency: string
  search_keywords: string | null
  fts_vector?: string
}

export interface AssetSearchResponse {
  results: Asset[]
  total: number
}
