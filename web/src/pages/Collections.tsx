import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import { toast } from 'sonner'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Database, Trash2, FileText } from 'lucide-react'

export default function Collections() {
  const queryClient = useQueryClient()
  const { data, isLoading } = useQuery({ queryKey: ['collections'], queryFn: () => api.getCollections() })
  const deleteMutation = useMutation({ mutationFn: (name: string) => api.deleteCollection(name), onSuccess: () => { toast.success('Collection deleted'); queryClient.invalidateQueries({ queryKey: ['collections'] }) }, onError: (error) => { toast.error('Delete failed', { description: error.message }) } })
  if (isLoading) return <div>Loading...</div>
  return (<div className="space-y-6"><h1 className="text-3xl font-bold">Collections</h1><div className="grid gap-4">{data?.collections.map((c) => (<Card key={c.name}><CardHeader className="flex flex-row items-center justify-between space-y-0"><div className="flex items-center gap-3"><Database className="h-6 w-6 text-muted-foreground" /><div><CardTitle className="text-xl">{c.name}</CardTitle><p className="text-sm text-muted-foreground">Created: {new Date(c.created_at).toLocaleDateString()}</p></div></div><Button variant="outline" size="sm" onClick={() => deleteMutation.mutate(c.name)} disabled={deleteMutation.isPending}><Trash2 className="h-4 w-4 mr-2" /> Delete</Button></CardHeader><CardContent><div className="grid grid-cols-3 gap-4 mt-4"><div className="flex items-center gap-2"><FileText className="h-4 w-4 text-muted-foreground" /><span className="text-sm"><strong>{c.document_count}</strong> documents</span></div><div className="flex items-center gap-2"><Database className="h-4 w-4 text-muted-foreground" /><span className="text-sm"><strong>{c.chunk_count}</strong> chunks</span></div><div className="text-sm"><strong>{c.disk_size_mb.toFixed(1)}</strong> MB</div></div></CardContent></Card>))}{data?.collections.length === 0 && (<Card><CardContent className="py-8 text-center text-muted-foreground">No collections yet.</CardContent></Card>)}</div></div>)
}
