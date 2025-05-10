export enum TaskStatus {
  PENDING = "PENDING",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  CANCELED = "CANCELED",
  UPDATING = "UPDATING",
}

export interface ClassificationItem {
  classification: string
  confidence: number
  match: boolean
  relevant: boolean
  [key: string]: any
}

export interface ItemDto {
  ref_no: string
  description: string
  quantity: number
  unit: string
  classification_item?: ClassificationItem
  [key: string]: any
}

export interface FileModel {
  id: string
  filename: string
  filepath: string
  customer_number: string
  task_id?: string
  items: ItemDto[]
  is_xml_generated: boolean
  xml_content?: string
  created_at: number
  updated_at?: number
  [key: string]: any
}

export interface TaskDto {
  id: string
  collection_id: string
  description?: string
  file_name?: string
  status: TaskStatus
  created_at?: number
  updated_at?: number
  [key: string]: any
}

export interface FileResponse {
  file: FileModel
  message: string
}

export interface FilesListResponse {
  files: FileModel[]
  count: number
  message: string
}

export interface TaskResponse {
  task: TaskDto
  message: string
}
