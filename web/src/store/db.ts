import Dexie, { Table } from 'dexie'

export interface Conversation {
  id?: number
  title: string
  created_at: Date
  updated_at: Date
}

export interface Message {
  id?: number
  conversation_id: number
  role: 'user' | 'assistant'
  content: string
  provider?: string
  model?: string
  latency_ms?: number
  created_at: Date
}

export interface QueryHistory {
  id?: number
  timestamp: Date
  question: string
  collection: string
  provider: string
  latency_ms: number
  tokens?: number
}

class AppDatabase extends Dexie {
  conversations!: Table<Conversation, number>
  messages!: Table<Message, number>
  queryHistory!: Table<QueryHistory, number>

  constructor() {
    super('rag-api-db')
    this.version(1).stores({
      conversations: '++id, title, created_at, updated_at',
      messages: '++id, conversation_id, role, created_at',
      queryHistory: '++id, timestamp, question, collection, provider',
    })
  }
}

export const db = new AppDatabase()