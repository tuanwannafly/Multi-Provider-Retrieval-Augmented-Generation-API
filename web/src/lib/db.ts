import Dexie, { type Table } from 'dexie'

export interface Conversation {
  id?: number
  title: string
  collection: string
  provider: string
  createdAt: number
}

export interface ChatMessage {
  id?: number
  conversationId: number
  role: 'user' | 'assistant'
  content: string
  latencyMs?: number
  createdAt: number
}

export interface QueryRecord {
  id?: number
  type: 'ask' | 'compare'
  question: string
  collection: string
  provider?: string
  latencyMs: number
  tokens?: number
  estimatedCostUsd?: number
  status: 'success' | 'error'
  faithfulness?: number
  answerRelevancy?: number
  createdAt: number
}

class RagDB extends Dexie {
  conversations!: Table<Conversation, number>
  messages!: Table<ChatMessage, number>
  queries!: Table<QueryRecord, number>

  constructor() {
    super('rag-api-web')
    this.version(1).stores({
      conversations: '++id, collection, provider, createdAt',
      messages: '++id, conversationId, createdAt',
      queries: '++id, type, provider, collection, createdAt',
    })
  }
}

export const db = new RagDB()
