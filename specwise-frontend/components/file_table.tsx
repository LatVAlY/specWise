"use client"

import { useState, useEffect } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Download, RefreshCw, FileText, CheckCircle } from "lucide-react"
import { useAllFiles } from "@/hooks/use-files"
import { useGenerateXml } from "@/hooks/use-files"
import { toast } from "@/components/ui/use-toast"
import { formatDistanceToNow } from "date-fns"
import { Skeleton } from "@/components/ui/skeleton"
import type { FileModel } from "@/types/api"

export function FilesTable() {
  const { data: filesData, refetch, isLoading: isLoadingFiles } = useAllFiles()
  const generateXmlMutation = useGenerateXml()
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!isLoadingFiles && filesData) {
      setIsLoading(false)
    }
  }, [isLoadingFiles, filesData])

  const handleRefresh = () => {
    setIsLoading(true)
    refetch().then(() => {
      setIsLoading(false)
    })
  }

  const handleGenerateXml = async (fileId: string) => {
    try {
      await generateXmlMutation.mutateAsync(fileId)
      toast({
        title: "XML Generated",
        description: "XML has been generated successfully.",
      })
      refetch()
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to generate XML. Please try again.",
        variant: "destructive",
      })
    }
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

  const files: any[] = filesData?.files || []
  console.log("Files data:", files)
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Files</h2>
        <Button variant="outline" size="sm" onClick={handleRefresh} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>File</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Created</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              // Loading state
              Array.from({ length: 3 }).map((_, index) => (
                <TableRow key={`loading-${index}`}>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Skeleton className="h-4 w-4 rounded-full" />
                      <Skeleton className="h-4 w-40" />
                    </div>
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-20" />
                  </TableCell>
                  <TableCell>
                    <Skeleton className="h-4 w-24" />
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end">
                      <Skeleton className="h-8 w-20" />
                    </div>
                  </TableCell>
                </TableRow>
              ))
            ) : files.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-6 text-muted-foreground">
                  No files found. Upload files to start processing.
                </TableCell>
              </TableRow>
            ) : (
              files.map((file: any) => (
                <TableRow key={file.id}>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <FileText className="h-4 w-4 text-blue-500" />
                      <span className="font-medium">{file.filename}</span>
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">ID: {file.id.substring(0, 8)}...</div>
                  </TableCell>
                  <TableCell>
                    <span className="text-sm">{file.customer_number}</span>
                  </TableCell>
                  <TableCell>
                    {file.created_at ? (
                      <span className="text-sm text-muted-foreground">
                        {formatDistanceToNow(new Date(file.created_at), { addSuffix: true })}
                      </span>
                    ) : (
                      "Unknown"
                    )}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex justify-end space-x-2">
                      {!file.is_xml_generated ? (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleGenerateXml(file.id)}
                          disabled={generateXmlMutation.isPending}
                        >
                          Generate XML
                        </Button>
                      ) : (
                        <Button variant="outline" size="sm" onClick={() => handleDownloadXml(file)}>
                          <Download className="h-4 w-4 mr-2" />
                          Download XML
                        </Button>
                      )}
                      {file.is_xml_generated && (
                        <Badge variant="outline" className="bg-green-50 ml-2 flex items-center">
                          <CheckCircle className="h-3 w-3 mr-1 text-green-500" />
                          XML Ready
                        </Badge>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
