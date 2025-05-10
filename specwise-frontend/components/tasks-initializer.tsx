"use client"

import { useEffect } from "react"
import { useAllTasks } from "@/hooks/use-tasks"
import { useAllFiles } from "@/hooks/use-files"
import { useTasksStore } from "@/store/tasks-store"
import { toast } from "@/components/ui/use-toast"
import { TaskStatus, type TaskDto } from "@/types/api"

export function TasksInitializer() {
  const { data: tasksData, isLoading: isLoadingTasks, error: tasksError } = useAllTasks()
  const { data: filesData, isLoading: isLoadingFiles, error: filesError } = useAllFiles()
  const { addTasks, clearTasks } = useTasksStore()

  console.log("TasksInitializer: tasksData", tasksData)
  useEffect(() => {
    if (tasksData && Array.isArray(tasksData)) {
      clearTasks()
      addTasks(tasksData)
    }
    else if (filesData && Array.isArray(filesData)) {
      const tasksFromFiles = new Map<string, TaskDto>()

      filesData.forEach((file) => {
        if (file.task_id) {
          if (!tasksFromFiles.has(file.task_id)) {
            tasksFromFiles.set(file.task_id, {
              id: file.task_id,
              collection_id: file.task_id, 
              file_name: file.filename,
              status: TaskStatus.COMPLETED,
              created_at: file.created_at,
            })
          }
        }
      })

      if (tasksFromFiles.size > 0) {
        clearTasks()
        addTasks(Array.from(tasksFromFiles.values()))
      }
    }
  }, [tasksData, filesData, addTasks, clearTasks])

  useEffect(() => {
    if (tasksError && filesError) {
      toast({
        title: "Error loading tasks",
        description: "Failed to load existing tasks. Please refresh the page.",
        variant: "destructive",
      })
    }
  }, [tasksError, filesError])

  return null // This component doesn't render anything
}
