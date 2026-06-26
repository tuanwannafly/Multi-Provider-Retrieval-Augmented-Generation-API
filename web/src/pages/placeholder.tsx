import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function PlaceholderPage({ title, phase }: { title: string; phase: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-muted-foreground">{phase} will implement this page.</p>
      </CardContent>
    </Card>
  )
}
