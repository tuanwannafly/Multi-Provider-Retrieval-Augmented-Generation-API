import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { api } from '@/services/api'
import { toast } from 'sonner'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Zap, Clock, DollarSign, AlertCircle, CheckCircle } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

export default function Compare() {
  const [question, setQuestion] = useState('')
  const [collection, setCollection] = useState('')
  const [result, setResult] = useState<any>(null)

  const compareMutation = useMutation({
    mutationFn: (data: { question: string; collection: string }) =>
      api.compare(data),
    onSuccess: (data) => {
      setResult(data)
      toast.success('Comparison complete', {
        description: `Fastest: ${data.fastest_provider} (${data.total_elapsed_ms}ms)`,
      })
    },
    onError: (error) => {
      toast.error('Compare failed', { description: error.message })
    },
  })

  const handleCompare = () => {
    if (!question.trim() || !collection.trim()) {
      toast.error('Please enter question and collection')
      return
    }
    compareMutation.mutate({ question, collection })
  }

  const copyToClipboard = () => {
    if (!result) return
    const text = `# Compare Results\n\n**Question:** ${result.question}\n\n` +
      Object.entries(result.results).map(([provider, data]: [string, any]) =>
        `## ${provider}\n\n${data.status === 'success' ? data.answer : `❌ ${data.error}`}\n\n` +
        `Latency: ${data.latency_ms}ms\nTokens: ${data.tokens}\nCost: $${data.estimated_cost_usd || 0}\n`
      ).join('\n')
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Compare Providers</h1>

      <Card>
        <CardHeader>
          <CardTitle>Settings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label className="text-sm font-medium">Collection</label>
            <input
              type="text"
              value={collection}
              onChange={(e) => setCollection(e.target.value)}
              placeholder="math-101"
              className="w-full px-3 py-2 border rounded-md mt-1"
            />
          </div>
          <div>
            <label className="text-sm font-medium">Question</label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="What is gradient descent?"
              rows={3}
              className="w-full px-3 py-2 border rounded-md mt-1"
            />
          </div>
          <Button onClick={handleCompare} disabled={compareMutation.isPending}>
            {compareMutation.isPending ? 'Comparing...' : 'Compare All Providers'}
          </Button>
        </CardContent>
      </Card>

      {result && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">
              Total time: <strong>{result.total_elapsed_ms}ms</strong>
            </p>
            <Button variant="outline" size="sm" onClick={copyToClipboard}>
              Export Markdown
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {(['groq', 'gemini', 'anthropic'] as const).map((provider) => {
              const data = result.results[provider]
              const isFastest = result.fastest_provider === provider
              const isSuccess = data.status === 'success'

              return (
                <Card key={provider} className={isFastest ? 'border-green-500 border-2' : ''}>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="capitalize">{provider}</CardTitle>
                      {isFastest && <Zap className="h-4 w-4 text-yellow-500" />}
                      {isSuccess ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {isSuccess ? (
                      <>
                        <div className="text-sm text-muted-foreground">
                          <div className="flex items-center gap-2">
                            <Clock className="h-3 w-3" />
                            {data.latency_ms}ms
                          </div>
                          <div className="flex items-center gap-2">
                            <DollarSign className="h-3 w-3" />
                            ${data.estimated_cost_usd?.toFixed(4) || '0.0000'}
                          </div>
                          <div className="flex items-center gap-2">
                            <span>Tokens: {data.tokens}</span>
                          </div>
                        </div>
                        <div className="text-sm max-h-64 overflow-auto">
                          <ReactMarkdown>{data.answer || ''}</ReactMarkdown>
                        </div>
                      </>
                    ) : (
                      <div className="text-destructive text-sm">
                        <p className="font-bold">{data.error}</p>
                        <p>{data.message}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )
            })}
          </div>
        </div>
      )}
    </div>
  )
}