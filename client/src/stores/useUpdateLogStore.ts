import { create } from 'zustand'
import { stockApi } from '../api/stockApi'
import type { UpdateLog } from '../types/stock'

interface UpdateLogStore {
  // State
  logs: UpdateLog[]
  isOpen: boolean
  isLoading: boolean

  // Actions
  fetchLogs: () => Promise<void>
  openModal: () => Promise<void>
  closeModal: () => void
}

export const useUpdateLogStore = create<UpdateLogStore>((set, get) => ({
  // Initial State
  logs: [],
  isOpen: false,
  isLoading: false,

  // Actions
  fetchLogs: async () => {
    if (get().isLoading) return
    set({ isLoading: true })
    try {
      const data = await stockApi.fetchUpdateLogs()
      set({ logs: data, isLoading: false })
    } catch (error) {
      console.error('[UpdateLogStore] fetchLogs error', error)
      set({ isLoading: false })
    }
  },

  openModal: async () => {
    set({ isOpen: true })
    if (get().logs.length === 0) {
      await get().fetchLogs()
    }
  },

  closeModal: () => set({ isOpen: false }),
}))

