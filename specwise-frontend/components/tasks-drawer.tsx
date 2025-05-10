"use client"

import { useEffect, useState } from "react"
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Inbox, X, CheckCircle, AlertCircle, Clock, Trash2, Loader2 } from "lucide-react"
import { useTasksStore } from "@/store/tasks-store"
import { useDeleteTask } from "@/hooks/use-tasks"
import { TaskStatus } from "@/types/api"
import { Progress } from "@/components/ui/progress"
import { toast } from "@/components/ui/use-toast"
import { Skeleton } from "@/components/ui/skeleton"
import { API_BASE_URL } from "@/lib/api-client"

export function TasksDrawer() {
  const [open, setOpen] = useState(false)
  const { activeTasks, updateTask, removeTask } = useTasksStore()
  const deleteTaskMutation = useDeleteTask()
  const [isInitializing, setIsInitializing] = useState(true)

  // Set initializing to false after a short delay
  useEffect(() => {
    const timer = setTimeout(() => {
      setIsInitializing(false)
    }, 1000)
    return () => clearTimeout(timer)
  }, [])

  // Poll for task status updates
  useEffect(() => {
    const interval = setInterval(() => {
      activeTasks.forEach((task) => {
        if (
          task.status !== TaskStatus.COMPLETED &&
          task.status !== TaskStatus.FAILED &&
          task.status !== TaskStatus.CANCELED
         
        ) {
          fetch(`${API_BASE_URL}/tasks/task/${task.id}/status`)
            .then((res) => res.json())
            .then((data) => {
              if (data.task && data.task.status !== task.status || (task.data && data.task.description !== task.description)) {
                updateTask(task.id, { status: data.task.status, description: data.task.description })

                if (data.task.status === TaskStatus.COMPLETED) {
                  toast({
                    title: "Task completed",
                    description: `Task for ${task.file_name || "file"} has been completed.`,
                  })
                } else if (data.task.status === TaskStatus.FAILED) {
                  toast({
                    title: "Task failed",
                    description: `Task for ${task.file_name || "file"} has failed.`,
                    variant: "destructive",
                  })
                }
              }
            })
            .catch((error) => console.error("Error polling task status:", error))
        }
      })
    }, 5000)

    return () => clearInterval(interval)
  }, [activeTasks, updateTask])

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

  const pendingTasksCount = activeTasks.filter(
    (task) =>
      task.status !== TaskStatus.COMPLETED && task.status !== TaskStatus.FAILED && task.status !== TaskStatus.CANCELED,
  ).length

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
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          variant="outline"
          className="fixed bottom-4 left-4 z-50 flex items-center gap-2"
          onClick={() => setOpen(true)}
        >
          {isInitializing ? (
            <Loader2 className="h-5 w-5 animate-spin" />
          ) : (
            <>
              <Inbox className="h-5 w-5" />
              Tasks
              {pendingTasksCount > 0 && <Badge className="ml-1 bg-blue-500">{pendingTasksCount}</Badge>}
            </>
          )}
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-[400px] sm:w-[540px]">
        <SheetHeader>
          <SheetTitle className="flex items-center justify-between">
            Active Tasks
            {pendingTasksCount > 0 && <Badge className="ml-2 bg-blue-500">{pendingTasksCount} running</Badge>}
          </SheetTitle>
        </SheetHeader>
        <div className="mt-6 space-y-4">
          {isInitializing ? (
            // Loading state
            Array.from({ length: 3 }).map((_, index) => (
              <div key={`loading-${index}`} className="rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Skeleton className="h-4 w-4 rounded-full" />
                    <Skeleton className="h-4 w-40" />
                  </div>
                  <Skeleton className="h-6 w-20" />
                </div>
                <div className="mt-2">
                  <Skeleton className="h-4 w-full" />
                </div>
                <div className="mt-3 flex items-center justify-between">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-8 w-16" />
                </div>
              </div>
            ))
          ) : activeTasks.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-10 text-center text-muted-foreground">
              <Inbox className="h-10 w-10 mb-2" />
              <p>No active tasks</p>
              <p className="text-sm">Upload files to start processing</p>
            </div>
          ) : (
            activeTasks.map((task) => (
              <div key={task.id} className="rounded-lg border p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {getStatusIcon(task.status)}
                    <span className="font-medium truncate max-w-[200px]">
                      {task.file_name || task.description || "Task"}
                    </span>
                  </div>
                  {getStatusBadge(task.status)}
                </div>

                <div className="mt-2">
                  <div className="text-xs text-muted-foreground mb-1">
                    {task.status === TaskStatus.IN_PROGRESS ? "Processing..." : task.status}
                  </div>
                  {(task.status === TaskStatus.PENDING || task.status === TaskStatus.IN_PROGRESS) && (
                    <Progress value={task.status === TaskStatus.PENDING ? 10 : 50} className="h-1.5" />
                  )}
                </div>

                <div className="mt-3 flex items-center justify-between">
                  <div className="text-xs text-muted-foreground">ID: {task.id.substring(0, 8)}...</div>
                  <div className="flex space-x-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 text-xs text-red-500 hover:text-red-700 hover:bg-red-50"
                      onClick={() => handleDeleteTask(task.id)}
                      disabled={deleteTaskMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                    {(task.status === TaskStatus.COMPLETED ||
                      task.status === TaskStatus.FAILED ||
                      task.status === TaskStatus.CANCELED) && (
                      <Button variant="ghost" size="sm" className="h-7 text-xs" onClick={() => removeTask(task.id)}>
                        Dismiss
                      </Button>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </SheetContent>
    </Sheet>
  )
}
