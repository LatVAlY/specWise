import { useMutation, useQueryClient } from "@tanstack/react-query"
import { dataApi } from "@/lib/api-client"

export function useCancelTask() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (taskId: string) => dataApi.cancelTask(taskId),
    onSuccess: (_, taskId) => {
      queryClient.invalidateQueries({ queryKey: ["task", "status", taskId] })
      queryClient.invalidateQueries({ queryKey: ["files", "task", taskId] })
    },
  })
}
