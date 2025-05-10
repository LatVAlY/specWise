import type { TaskStatus } from "@/types/api"

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"

// Helper function for API requests
async function fetchAPI<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`
  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// Files API
export const filesApi = {
  getAllFiles: () => fetchAPI("/files/"),
  getFileById: (fileId: string) => fetchAPI(`/files/${fileId}`),
  getFilesByCustomer: (customerNumber: string) => fetchAPI(`/files/customer/${customerNumber}`),
  getFilesByTask: (taskId: string) => fetchAPI(`/files/task/${taskId}`),
  updateItemClassification: (fileId: string, refNo: string, data: { match: boolean; relevant: boolean }) =>
    fetchAPI(`/files/${fileId}/items/${refNo}/classification`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  generateXml: (fileId: string) => fetchAPI(`/files/${fileId}/xml`, { method: "PUT" }),
}

// Tasks API
export const tasksApi = {
  getAllTasks: () => fetchAPI("/tasks/"),
  getTaskStatus: (taskId: string) => fetchAPI(`/tasks/task/${taskId}/status`),
  updateTaskStatus: (taskId: string, status: TaskStatus, additionalInfo?: string) => {
    let url = `/tasks/task/${taskId}/status?status=${status}`
    if (additionalInfo) {
      url += `&additional_info=${encodeURIComponent(additionalInfo)}`
    }
    return fetchAPI(url, { method: "PUT" })
  },
  deleteTask: (taskId: string) => fetchAPI(`/tasks/${taskId}`, { method: "DELETE" }),
}

// Data API
export const dataApi = {
  uploadData: (formData: FormData) =>
    fetch(`${API_BASE_URL}/data/`, {
      method: "POST",
      body: formData,
    }).then((res) => res.json()),
}
