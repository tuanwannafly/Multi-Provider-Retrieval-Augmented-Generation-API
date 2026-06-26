import { useQuery } from '@tanstack/react-query'
import { api } from '@/services/api'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Activity, Database, Clock, CheckCircle } from 'lucide-react'

export default function Dashboard() {
  const { data: health, isLoading: healthLoading } = useQuery({
    queryKey: ['health'],
    queryFn: () => api.health(),
  })

  const { data: readiness } = useQuery({
    queryKey: ['readiness'],
    queryFn: () => api.readiness(),
    refetchInterval: 5000,
  })

  const { data: collections } = useQuery({
    queryKey: ['collections'],
    queryFn: () => api.getCollections(),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Dashboard</h1>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">API Status</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {healthLoading ? 'Loading...' : health?.status === 'ok' ? 'Healthy' : 'Unknown'}
            </div>
            <p className="text-xs text-muted-foreground">
              v{health?.version}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Readiness</CardTitle>
            <CheckCircle className={`h-4 w-4 ${readiness?.status === 'ready' ? 'text-green-500' : 'text-yellow-500'}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold capitalize">{readiness?.status || 'loading'}</div>
            <p className="text-xs text-muted-foreground">
              {readiness?.qdrant === 'connected' ? 'Qdrant connected' : 'Connecting...'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Collections</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{collections?.total_collections || 0}</div>
            <p className="text-xs text-muted-foreground">
              {collections?.total_chunks || 0} chunks total
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Embedding Model</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {readiness?.embedding_model === 'loaded' ? 'Loaded' : 'Loading'}
            </div>
            <p className="text-xs text-muted-foreground">
              all-MiniLM-L6-v2
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>System Info</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex justify-between">
            <span className="text-muted-foreground">Qdrant URL:</span>
            <span className="font-medium">{readiness?.qdrant_url}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-muted-foreground">API Version:</span>
            <span className="font-medium">{health?.version}</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}