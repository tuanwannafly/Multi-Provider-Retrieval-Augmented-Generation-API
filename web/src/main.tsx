import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { Sidebar } from './components/sidebar'
import Dashboard from './pages/Dashboard'
import Documents from './pages/Documents'
import Collections from './pages/Collections'
import Ask from './pages/Ask'
import Compare from './pages/Compare'
import Evaluate from './pages/Evaluate'
import './index.css'

const queryClient = new QueryClient()

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="flex h-screen">
          <Sidebar />
          <main className="flex-1 overflow-auto p-8">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/documents" element={<Documents />} />
              <Route path="/collections" element={<Collections />} />
              <Route path="/ask" element={<Ask />} />
              <Route path="/compare" element={<Compare />} />
              <Route path="/evaluate" element={<Evaluate />} />
            </Routes>
          </main>
        </div>
        <Toaster />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)