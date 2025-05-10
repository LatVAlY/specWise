"use client"

import { useState, useEffect } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Download, RefreshCw, FileText, CheckCircle, AlertCircle, Clock, X, Trash2 } from "lucide-react"
import { useTasksStore } from "@/store/tasks-store"
import { useGenerateXml } from "@/hooks/use-files"
import { useDeleteTask } from "@/hooks/use-tasks"
import { TaskStatus, type FileModel } from "@/types/api"
import { toast } from "@/components/ui/use-toast"
import { formatDistanceToNow } from "date-fns"
import { Skeleton } from "@/components/ui/skeleton"
import { API_BASE_URL } from "@/lib/api-client"

export function TasksTable() {
  const { activeTasks, removeTask } = useTasksStore()
  const generateXmlMutation = useGenerateXml()
  const deleteTaskMutation = useDeleteTask()

  // Function to fetch files for each task
  const fetchFilesForTasks = async () => {
    const taskFilesMap = new Map<string, FileModel[]>()

    for (const task of activeTasks) {
      try {
        const response = await fetch(`${API_BASE_URL}/files/task/${task.id}`)
        const data = await response.json()
        if (data.files && Array.isArray(data.files)) {
          taskFilesMap.set(task.id, data.files)
        }
      } catch (error) {
        console.error(`Error fetching files for task ${task.id}:`, error)
      }
    }

    return taskFilesMap
  }

  const [taskFiles, setTaskFiles] = useState<Map<string, FileModel[]>>(new Map())
  const [isLoading, setIsLoading] = useState(true)

  const refetchFiles = async () => {
    setIsLoading(true)
    try {
      const filesMap = await fetchFilesForTasks()
      setTaskFiles(filesMap)
    } catch (error) {
      console.error("Error fetching files:", error)
    } finally {
      setIsLoading(false)
    }
  }

  useEffect(() => {
    refetchFiles()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTasks.length])

  const handleGenerateXml = async (fileId: string) => {
    try {
      await generateXmlMutation.mutateAsync(fileId)
      toast({
        title: "XML Generated",
        description: "XML has been generated successfully.",
      })
      refetchFiles()
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

  const handleDeleteTask = async (taskId: string) => {
    try {
      await deleteTaskMutation.mutateAsync(taskId)
      removeTask(taskId)
      toast({
        title: "Task deleted",
        description: "The task has been deleted successfully.",
      })
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to delete the task. Please try again.",
        variant: "destructive",
      })
    }
  }

  const getStatusIcon = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.COMPLETED:
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case TaskStatus.FAILED:
        return <AlertCircle className="h-4 w-4 text-red-500" />
      case TaskStatus.CANCELED:
        return <X className="h-4 w-4 text-gray-500" />
      default:
        return <Clock className="h-4 w-4 text-blue-500" />
    }
  }

  const getStatusBadge = (status: TaskStatus) => {
    switch (status) {
      case TaskStatus.PENDING:
        return (
          <Badge variant="outline" className="bg-yellow-50">
            Pending
          </Badge>
        )
      case TaskStatus.IN_PROGRESS:
        return (
          <Badge variant="outline" className="bg-blue-50">
            In Progress
          </Badge>
        )
      case TaskStatus.COMPLETED:
        return (
          <Badge variant="outline" className="bg-green-50">
            Completed
          </Badge>
        )
      case TaskStatus.FAILED:
        return (
          <Badge variant="outline" className="bg-red-50">
            Failed
          </Badge>
        )
      case TaskStatus.CANCELED:
        return (
          <Badge variant="outline" className="bg-gray-50">
            Canceled
          </Badge>
        )
      case TaskStatus.UPDATING:
        return (
          <Badge variant="outline" className="bg-purple-50">
            Updating
          </Badge>
        )
      default:
        return <Badge variant="outline">Unknown</Badge>
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold">Processing Tasks</h2>
        <Button variant="outline" size="sm" onClick={refetchFiles} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>File</TableHead>
              <TableHead>Status</TableHead>
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
                    <Skeleton className="h-6 w-20" />
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
            ) : activeTasks.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-6 text-muted-foreground">
                  No tasks found. Upload files to start processing.
                </TableCell>
              </TableRow>
            ) : (
              activeTasks.map((task) => {
                const files = taskFiles.get(task.id) || []

                return (
                  <TableRow key={task.id}>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        <FileText className="h-4 w-4 text-blue-500" />
                        <span className="font-medium">{task.file_name || "Unknown file"}</span>
                      </div>
                      {files.length > 0 && (
                        <div className="mt-1 text-xs text-muted-foreground">{files.length} file(s) associated</div>
                      )}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(task.status)}
                        <span>{getStatusBadge(task.status)}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      {task.created_at ? (
                        <span className="text-sm text-muted-foreground">
                          {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                        </span>
                      ) : (
                        "Unknown"
                      )}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end space-x-2">
                        {task.status === TaskStatus.COMPLETED && files.length > 0 && (
                          <>
                            {files.map((file) => (
                              <div key={file.id} className="flex space-x-2">
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
                              </div>
                            ))}
                          </>
                        )}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-red-500 hover:text-red-700 hover:bg-red-50"
                          onClick={() => handleDeleteTask(task.id)}
                          disabled={deleteTaskMutation.isPending}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
