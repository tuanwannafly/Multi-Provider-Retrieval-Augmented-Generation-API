import { cn } from "@/lib/utils"

interface CardProps {
  className?: string
  children?: React.ReactNode
}

function Card({ className, children }: CardProps) {
  return (
    <div className={cn("rounded-lg border bg-card text-card-foreground shadow-sm", className)}>
      {children}
    </div>
  )
}

function CardHeader({ className, children }: CardProps) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)}>{children}</div>
}

function CardTitle({ className, children }: CardProps) {
  return <h3 className={cn("text-2xl font-semibold leading-none tracking-tight", className)}>{children}</h3>
}

function CardContent({ className, children }: CardProps) {
  return <div className={cn("p-6 pt-0", className)}>{children}</div>
}

export { Card, CardHeader, CardTitle, CardContent }