import { cn } from "@/lib/utils"

function Sidebar({ className }: { className?: string }) {
  return (
    <div className={cn("flex h-full w-64 flex-col border-r bg-background p-4", className)}>
      <div className="mb-6">
        <h1 className="text-xl font-bold">Multi-LLM RAG</h1>
        <p className="text-xs text-muted-foreground">API Dashboard</p>
      </div>
      <nav className="flex flex-col gap-2">
        <a href="/" className="px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground">
          Dashboard
        </a>
        <a href="/documents" className="px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground">
          Documents
        </a>
        <a href="/collections" className="px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground">
          Collections
        </a>
        <a href="/ask" className="px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground">
          Ask
        </a>
        <a href="/compare" className="px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground">
          Compare
        </a>
        <a href="/evaluate" className="px-3 py-2 rounded-md hover:bg-accent hover:text-accent-foreground">
          Evaluate
        </a>
      </nav>
    </div>
  )
}

export { Sidebar }