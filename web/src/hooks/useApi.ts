import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'

export function useReadiness() {
  return useQuery({
    queryKey: ['readiness'],
    queryFn: () => api.readiness(),
    refetchInterval: 5000,
    retry: false,
  })
}

export function useCollections() {
  return useQuery({
    queryKey: ['collections'],
    queryFn: () => api.getCollections(),
    refetchInterval: 10000,
  })
}