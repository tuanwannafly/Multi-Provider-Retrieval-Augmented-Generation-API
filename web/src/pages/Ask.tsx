import { useState } from 'react'
import { api } from '@/services/api'
import { toast } from 'sonner'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Send, Bot, User } from 'lucide-react'
import ReactMarkdown from 'react-markdown'

const PROVIDERS = ['groq', 'gemini', 'anthropic'] as const

export default function Ask() {
  const [question, setQuestion] = useState('')
  const [collection, setCollection] = useState('')
  const [provider, setProvider] = useState<'groq' | 'gemini' | 'anthropic'>('groq')
  const [topK, setTopK] = useState(5)
  const [stream, setStream] = useState(true)
  const [streamingAnswer, setStreamingAnswer] = useState('')
  const [messages, setMessages] = useState<{ role: string; content: string; provider?: string; latency_ms?: number }[]>([])

  const handleAsk = async () => {
    if (!question.trim() || !collection.trim()) {
      toast.error('Please enter question and collection')
      return
    }

    const userMessage = { role: 'user', content: question }
    setMessages(prev => [...prev, userMessage])
    setStreamingAnswer('')
    const questionToSend = question
    setQuestion('')

    if (stream) {
      try {
        let answer = ''
        await api.askStream(
          { question: questionToSend, collection, provider, top_k: topK, stream: true },
          (token) => {
            answer += token
            setStreamingAnswer(answer)
          }
        )
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: answer,
          provider,
        }])
      } catch (error) {
        toast.error('Streaming failed', { description: String(error) })
      }
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Ask (RAG Chat)</h1>

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
            <label className="text-sm font-medium">Provider</label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value as any)}
              className="w-full px-3 py-2 border rounded-md mt-1"
            >
              {PROVIDERS.map(p => (
                <option key={p} value={p}>{p}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-sm font-medium">Top K: {topK}</label>
            <input
              type="range"
              min="1"
              max="10"
              value={topK}
              onChange={(e) => setTopK(Number(e.target.value))}
              className="w-full mt-1"
            />
          </div>
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="stream"
              checked={stream}
              onChange={(e) => setStream(e.target.checked)}
            />
            <label htmlFor="stream" className="text-sm">Enable streaming (SSE)</label>
          </div>
        </CardContent>
      </Card>

      <Card className="h-[500px] flex flex-col">
        <CardHeader>
          <CardTitle>Chat</CardTitle>
        </CardHeader>
        <CardContent className="flex-1 overflow-auto space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`flex items-start gap-2 max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {msg.role === 'user' ? (
                  <User className="h-5 w-5 mt-1" />
                ) : (
                  <Bot className="h-5 w-5 mt-1" />
                )}
                <div className={`p-3 rounded-lg ${msg.role === 'user' ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                  {msg.role === 'user' ? (
                    msg.content
                  ) : (
                    <>
                      <ReactMarkdown>{msg.content}</ReactMarkdown>
                      {msg.provider && (
                        <p className="text-xs text-muted-foreground mt-2">
                          {msg.provider}
                        </p>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
          {streamingAnswer && (
            <div className="flex justify-start">
              <div className="flex items-start gap-2 max-w-[80%]">
                <Bot className="h-5 w-5 mt-1" />
                <div className="p-3 rounded-lg bg-muted">
                  <ReactMarkdown>{streamingAnswer}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleAsk()}
          placeholder="Ask a question about your documents..."
          className="flex-1 px-4 py-2 border rounded-md"
        />
        <Button onClick={handleAsk} disabled={!question.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}