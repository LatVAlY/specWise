import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { filesApi } from "@/lib/api-client"

export function useAllFiles() {
  return useQuery({
    queryKey: ["files"],
    queryFn: () => filesApi.getAllFiles(),
  })
}

export function useFileById(fileId: string) {
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ["file", fileId],
    queryFn: () => filesApi.getFileById(fileId),
    enabled: !!fileId,
  })

  return {
    ...query,
    refetch: () => {
      return queryClient.invalidateQueries({ queryKey: ["file", fileId] })
    },
  }
}

export function useFilesByTask(taskId: string) {
  return useQuery({
    queryKey: ["files", "task", taskId],
    queryFn: () => filesApi.getFilesByTask(taskId),
    enabled: !!taskId,
  })
}

export function useUpdateItemClassification() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      fileId,
      refNo,
      data,
    }: {
      fileId: string
      refNo: string
      data: { match: boolean; relevant: boolean }
    }) => filesApi.updateItemClassification(fileId, refNo, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["file", variables.fileId] })
    },
  })
}

export function useGenerateXml() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (fileId: string) => filesApi.generateXml(fileId),
    onSuccess: (_, fileId) => {
      queryClient.invalidateQueries({ queryKey: ["file", fileId] })
      queryClient.invalidateQueries({ queryKey: ["files"] })
    },
  })
}
