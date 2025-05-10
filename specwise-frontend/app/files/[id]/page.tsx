"use client"

import { useState, useEffect } from "react"
import { useParams, useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { ArrowLeft, FileText, Download, Edit, Trash2 } from "lucide-react"
import { useFileById, useDeleteFile } from "@/hooks/use-files"

import { toast } from "@/components/ui/use-toast"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import type { FileModel } from "@/types/api"
import { ArticleSelection } from "@/components/article_selections"

export default function FileDetailsPage() {
  const params = useParams()
  const router = useRouter()
  const fileId = params.id as string
  const { data, isLoading, error, refetch } = useFileById(fileId)
  const deleteFileMutation = useDeleteFile()
  const [file, setFile] = useState<FileModel | null>(null)
  const [showArticleSelection, setShowArticleSelection] = useState(false)
  const [showDeleteDialog, setShowDeleteDialog] = useState(false)

  useEffect(() => {
    if (data?.file) {
      setFile(data.file)
    }
  }, [data])

  const handleBack = () => {
    router.push("/")
  }

  const handleGenerateXml = () => {
    setShowArticleSelection(true)
  }

  const handleDownloadXml = (file: FileModel) => {
    if (!file.xml_content) {
      toast({
        title: "No XML content",
        description: "XML content is not available for this file.",
        variant: "destructive",
      })
      return
    }

    const blob = new Blob([file.xml_content], { type: "application/xml" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `${file.filename.split(".")[0]}.xml`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  const handleArticleSelectionSuccess = () => {
    setShowArticleSelection(false)
    // Refetch the file to get updated XML content
    refetch()
  }

  const handleDeleteFile = async () => {
    if (!file) return

    try {
      await deleteFileMutation.mutateAsync(file.id)
      toast({
        title: "File deleted",
        description: `${file.filename} has been deleted successfully.`,
      })
      router.push("/")
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete the file. Please try again.",
        variant: "destructive",
      })
      setShowDeleteDialog(false)
    }
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-6 px-4 space-y-6">
        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="sm" disabled>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>
              <Skeleton className="h-8 w-64" />
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (error || !file) {
    return (
      <div className="container mx-auto py-6 px-4 space-y-6">
        <div className="flex items-center space-x-2">
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back
          </Button>
        </div>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-6 text-muted-foreground">
              <p className="text-red-500">
                Error loading file details. The file may have been deleted or does not exist.
              </p>
              <Button variant="outline" className="mt-4" onClick={handleBack}>
                Return to Files
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  if (showArticleSelection) {
    return (
      <div className="container mx-auto py-6 px-4">
        <ArticleSelection
          file={file}
          onBack={() => setShowArticleSelection(false)}
          onSuccess={handleArticleSelectionSuccess}
        />
      </div>
    )
  }

  return (
    <>
      <div className="container mx-auto py-6 px-4 space-y-6">
        <div className="flex items-center justify-between">
          <Button variant="ghost" size="sm" onClick={handleBack}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Files
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-red-500 hover:text-red-700 hover:bg-red-50"
            onClick={() => setShowDeleteDialog(true)}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Delete File
          </Button>
        </div>

        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <CardTitle className="text-xl">File Details</CardTitle>
              <FileText className="h-6 w-6 text-blue-500" />
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground">Filename</h3>
                <p className="mt-1">{file.filename}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground">Customer Number</h3>
                <p className="mt-1">{file.customer_number}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground">Created</h3>
                <p className="mt-1">{file.created_at ? new Date(file.created_at).toLocaleString() : "Unknown"}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground">File ID</h3>
                <p className="mt-1">{file.id}</p>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-4">
              {!file.is_xml_generated ? (
                <Button onClick={handleGenerateXml}>Generate XML</Button>
              ) : (
                <>
                  <Button onClick={() => handleDownloadXml(file)}>
                    <Download className="h-4 w-4 mr-2" />
                    Download XML
                  </Button>
                  <Button variant="outline" onClick={handleGenerateXml}>
                    <Edit className="h-4 w-4 mr-2" />
                    Edit Selection
                  </Button>
                </>
              )}
            </div>

            <div className="pt-4">
              <h3 className="text-sm font-medium mb-3">Articles ({file.items.length})</h3>
              {file.items.length === 0 ? (
                <p className="text-muted-foreground">No articles found in this file.</p>
              ) : (
                <div className="border rounded-md overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-muted">
                      <tr>
                        <th className="px-4 py-2 text-left font-medium">SKU</th>
                        <th className="px-4 py-2 text-left font-medium">Name</th>
                        <th className="px-4 py-2 text-left font-medium">Quantity</th>
                        <th className="px-4 py-2 text-left font-medium">Price</th>
                        <th className="px-4 py-2 text-left font-medium">Confidence</th>
                        <th className="px-4 py-2 text-left font-medium">commission</th>
                      </tr>
                    </thead>
                    <tbody>
                      {file.items.map((item, index) => (
                        <tr key={index} className={index % 2 === 0 ? "bg-white" : "bg-muted/30"}>
                          <td className="px-4 py-2">{item.sku}</td>
                          <td className="px-4 py-2">{item.name}</td>
                          <td className="px-4 py-2">
                            {item.quantity} {item.quantityunit}
                          </td>
                          <td className="px-4 py-2">
                            {item.price} {item.priceunit}
                          </td>
                          <td className="px-4 py-2">
                            <span className={item.confidence >= 0.9 ? "text-green-600" : "text-amber-600"}>
                              {(item.confidence * 100).toFixed(1)}%
                            </span>
                          </td>
                          <td className="px-4 py-2">{item.commission}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure you want to delete this file?</AlertDialogTitle>
            <AlertDialogDescription>
              You are about to delete <strong>{file.filename}</strong>. This action cannot be undone and all associated
              data will be permanently removed.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteFile}
              className="bg-red-500 hover:bg-red-600 text-white"
              disabled={deleteFileMutation.isPending}
            >
              {deleteFileMutation.isPending ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  )
}
