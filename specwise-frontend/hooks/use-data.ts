import { useMutation, useQueryClient } from "@tanstack/react-query"
import { dataApi } from "@/lib/api-client"

export function useUploadData() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (formData: FormData) => dataApi.uploadData(formData),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["files"] })
    },
  })
}
