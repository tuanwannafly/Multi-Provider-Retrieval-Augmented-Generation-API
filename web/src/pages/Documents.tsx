import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '@/services/api'
import { toast } from 'sonner'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Upload, File, CheckCircle, XCircle } from 'lucide-react'

export default function Documents() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [collection, setCollection] = useState('')
  const queryClient = useQueryClient()

  const uploadMutation = useMutation({
    mutationFn: async () => {
      if (!selectedFile) throw new Error('No file selected')
      return api.upload(selectedFile, collection)
    },
    onSuccess: (data) => {
      toast.success(\Uploaded \\, {
        description: \\ chunks created in \\,
      })
      queryClient.invalidateQueries({ queryKey: ['collections'] })
      setSelectedFile(null)
      setCollection('')
    },
    onError: (error) => {
      toast.error('Upload failed', { description: error.message })
    },
  })

  const handleUpload = () => {
    if (!selectedFile || !collection) {
      toast.error('Please select a file and enter collection name')
      return
    }
    uploadMutation.mutate()
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    const file = e.dataTransfer.files[0]
    if (file && ['.pdf', '.docx', '.txt'].some(ext => file.name.toLowerCase().endsWith(ext))) {
      setSelectedFile(file)
    } else {
      toast.error('Invalid file type', { description: 'Only PDF, DOCX, and TXT are supported' })
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold">Documents Upload</h1>

      <Card>
        <CardHeader>
          <CardTitle>Upload Document</CardTitle>
        </CardHeader>
        <CardContent>
          <div
            className="border-2 border-dashed rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => document.getElementById('file-input')?.click()}
          >
            <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg font-medium mb-2">Drop your file here or click to browse</p>
            <p className="text-sm text-muted-foreground">Supported formats: PDF, DOCX, TXT</p>
            <input id="file-input" type="file" accept=".pdf,.docx,.txt" className="hidden" onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
          </div>

          {selectedFile && (
            <div className="mt-4 p-4 bg-muted rounded-lg flex items-center gap-3">
              <File className="h-5 w-5" />
              <span className="font-medium">{selectedFile.name}</span>
              <span className="text-sm text-muted-foreground">({(selectedFile.size / 1024).toFixed(1)} KB)</span>
            </div>
          )}

          <div className="mt-4 flex gap-4">
            <input type="text" placeholder="Collection name (e.g., math-101)" value={collection} onChange={(e) => setCollection(e.target.value)} className="flex-1 px-4 py-2 border rounded-md" />
            <Button onClick={handleUpload} disabled={!selectedFile || !collection || uploadMutation.isPending}>Upload</Button>
          </div>

          {uploadMutation.isError && (
            <div className="mt-4 flex items-center gap-2 text-destructive">
              <XCircle className="h-5 w-5" />
              <span>Upload failed: {uploadMutation.error.message}</span>
            </div>
          )}

          {uploadMutation.isSuccess && (
            <div className="mt-4 flex items-center gap-2 text-green-600">
              <CheckCircle className="h-5 w-5" />
              <span>Upload successful!</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
