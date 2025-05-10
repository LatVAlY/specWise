import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { tasksApi } from "@/lib/api-client"
import { TaskStatus } from "@/types/api"

export function useAllTasks() {
  return useQuery({
    queryKey: ["tasks"],
    queryFn: () => tasksApi.getAllTasks(),
  })
}

export function useTaskStatus(taskId: string, pollingInterval = 5000) {
  return useQuery({
    queryKey: ["task", "status", taskId],
    queryFn: () => tasksApi.getTaskStatus(taskId),
    enabled: !!taskId,
    refetchInterval: (data) => {
      // Stop polling when task is completed, failed, or canceled
      if (
        data?.task?.status === TaskStatus.COMPLETED ||
        data?.task?.status === TaskStatus.FAILED ||
        data?.task?.status === TaskStatus.CANCELED
      ) {
        return false
      }
      return pollingInterval
    },
  })
}

export function useUpdateTaskStatus() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      taskId,
      status,
      additionalInfo,
    }: {
      taskId: string
      status: TaskStatus
      additionalInfo?: string
    }) => tasksApi.updateTaskStatus(taskId, status, additionalInfo),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["task", "status", variables.taskId] })
      queryClient.invalidateQueries({ queryKey: ["files", "task", variables.taskId] })
    },
  })
}

export function useDeleteTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (taskId: string) => tasksApi.deleteTask(taskId),
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: ["task", "status", taskId] })
      queryClient.invalidateQueries({ queryKey: ["files", "task", taskId] })
      queryClient.invalidateQueries({ queryKey: ["files"] })
      queryClient.invalidateQueries({ queryKey: ["tasks"] })
    },
  })
}
