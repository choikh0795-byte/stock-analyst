import { useState, useEffect, useRef, useCallback } from 'react'
import { stockApi } from '../api/stockApi'
import type { Asset } from '../types/asset'

interface UseAssetSearchResult {
  results: Asset[]
  isLoading: boolean
  error: string | null
  search: (query: string) => void
  clearResults: () => void
}

export function useAssetSearch(): UseAssetSearchResult {
  const [results, setResults] = useState<Asset[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const cacheRef = useRef<Map<string, Asset[]>>(new Map())
  const abortControllerRef = useRef<AbortController | null>(null)
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  const fetchAssets = useCallback(async (query: string) => {
    if (query.length === 0) {
      setResults([])
      setIsLoading(false)
      return
    }

    if (cacheRef.current.has(query)) {
      setResults(cacheRef.current.get(query)!)
      setIsLoading(false)
      return
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    abortControllerRef.current = new AbortController()

    try {
      setIsLoading(true)
      setError(null)

      const response = await stockApi.searchAssets(
        query,
        10,
        abortControllerRef.current.signal
      )

      cacheRef.current.set(query, response.results)
      setResults(response.results)
    } catch (err) {
      if (err instanceof Error && err.message !== 'Request cancelled') {
        setError(err.message)
        setResults([])
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  const search = useCallback(
    (query: string) => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }

      if (query.length === 0) {
        setResults([])
        setIsLoading(false)
        return
      }

      setIsLoading(true)

      debounceTimerRef.current = setTimeout(() => {
        fetchAssets(query)
      }, 200)
    },
    [fetchAssets]
  )

  const clearResults = useCallback(() => {
    setResults([])
    setError(null)
    setIsLoading(false)

    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
  }, [])

  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [])

  return {
    results,
    isLoading,
    error,
    search,
    clearResults,
  }
}
