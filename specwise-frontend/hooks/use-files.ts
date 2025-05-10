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

export function useGenerateXml() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ fileId, itemIds }: { fileId: string; itemIds: string[] }) =>
      filesApi.generateXml(fileId, itemIds),
    onSuccess: (_, { fileId }) => {
      queryClient.invalidateQueries({ queryKey: ["file", fileId] });
      queryClient.invalidateQueries({ queryKey: ["files"] });
    },
  })
}

export function useDeleteFile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (fileId: string) => filesApi.deleteFile(fileId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["files"] })
    },
  })
}
