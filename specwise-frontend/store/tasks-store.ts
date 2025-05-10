import { create } from "zustand"
import type { TaskDto } from "@/types/api"

interface TasksState {
  activeTasks: TaskDto[]
  addTask: (task: TaskDto) => void
  addTasks: (tasks: TaskDto[]) => void
  removeTask: (taskId: string) => void
  updateTask: (taskId: string, updates: Partial<TaskDto>) => void
  clearTasks: () => void
}

export const useTasksStore = create<TasksState>((set) => ({
  activeTasks: [],
  addTask: (task) =>
    set((state) => ({
      activeTasks: state.activeTasks.some((t) => t.id === task.id) ? state.activeTasks : [...state.activeTasks, task],
    })),
  addTasks: (tasks) =>
    set((state) => {
      const existingTaskIds = new Set(state.activeTasks.map((t) => t.id))
      const newTasks = tasks.filter((task) => !existingTaskIds.has(task.id))
      return {
        activeTasks: [...state.activeTasks, ...newTasks],
      }
    }),
  removeTask: (taskId) =>
    set((state) => ({
      activeTasks: state.activeTasks.filter((task) => task.id !== taskId),
    })),
  updateTask: (taskId, updates) =>
    set((state) => ({
      activeTasks: state.activeTasks.map((task) => (task.id === taskId ? { ...task, ...updates } : task)),
    })),
  clearTasks: () => set({ activeTasks: [] }),
}))
