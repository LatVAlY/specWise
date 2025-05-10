export enum TaskStatus {
  PENDING = "PENDING",
  IN_PROGRESS = "IN_PROGRESS",
  COMPLETED = "COMPLETED",
  FAILED = "FAILED",
  CANCELED = "CANCELED",
  UPDATING = "UPDATING",
}

export interface ItemDto {
  sku: string
  name: string
  text: string
  quantity: number
  quantityunit: string
  price: number
  priceunit: string
  commission: string
  confidence: number
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
