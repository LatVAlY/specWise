"use client"

import { useState, useEffect } from "react"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { RefreshCw, FileText, CheckCircle, AlertCircle, Clock, X, Trash2 } from "lucide-react"
import { useTasksStore } from "@/store/tasks-store"
import { useDeleteTask } from "@/hooks/use-tasks"
import { TaskStatus } from "@/types/api"
import { toast } from "@/components/ui/use-toast"
import { formatDistanceToNow } from "date-fns"
import { Skeleton } from "@/components/ui/skeleton"

export function TasksTable() {
  const { activeTasks, removeTask } = useTasksStore()
  const deleteTaskMutation = useDeleteTask()
  const [isLoading, setIsLoading] = useState(true)

  // Simulate loading for a better UX
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLoading(false)
    }, 1000)
    return () => clearTimeout(timer)
  }, [])

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
        <Button variant="outline" size="sm" onClick={() => setIsLoading(true)} disabled={isLoading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Task</TableHead>
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
              activeTasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <FileText className="h-4 w-4 text-blue-500" />
                      <span className="font-medium">{task.file_name || task.description || "Unknown task"}</span>
                    </div>
                    <div className="mt-1 text-xs text-muted-foreground">ID: {task.id.substring(0, 8)}...</div>
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
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-red-500 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDeleteTask(task.id)}
                      disabled={deleteTaskMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
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
