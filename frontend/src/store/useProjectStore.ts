import { create } from 'zustand'
import { projectApi } from '../services/api'

export interface Clip {
  id: string
  title?: string  // 可能没有原始title
  start_time: string
  end_time: string
  final_score: number  // 匹配后端字段名
  recommend_reason: string  // 匹配后端字段名
  generated_title?: string
  outline: string
  content: string[]
  chunk_index?: number  // 添加缺失字段
}

export interface Collection {
  id: string
  collection_title: string
  collection_summary: string
  clip_ids: string[]
  collection_type?: string // "ai_recommended" or "manual"
  created_at?: string
}

export interface Project {
  id: string
  name: string
  video_path: string
  status: 'uploading' | 'processing' | 'completed' | 'error'
  created_at: string
  updated_at: string
  clips: Clip[]
  collections: Collection[]
  current_step?: number
  total_steps?: number
  error_message?: string
}

interface ProjectStore {
  projects: Project[]
  currentProject: Project | null
  loading: boolean
  error: string | null
  
  // Actions
  setProjects: (projects: Project[]) => void
  setCurrentProject: (project: Project | null) => void
  addProject: (project: Project) => void
  updateProject: (id: string, updates: Partial<Project>) => void
  deleteProject: (id: string) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  updateClip: (projectId: string, clipId: string, updates: Partial<Clip>) => void
  updateCollection: (projectId: string, collectionId: string, updates: Partial<Collection>) => void
  addCollection: (projectId: string, collection: Collection) => void
  deleteCollection: (projectId: string, collectionId: string) => void
  removeClipFromCollection: (projectId: string, collectionId: string, clipId: string) => void
  reorderCollectionClips: (projectId: string, collectionId: string, newClipIds: string[]) => Promise<void>
}

export const useProjectStore = create<ProjectStore>((set, get) => ({
  projects: [],
  currentProject: null,
  loading: false,
  error: null,

  setProjects: (projects) => set({ projects }),
  
  setCurrentProject: (project) => set({ currentProject: project }),
  
  addProject: (project) => set((state) => ({ 
    projects: [project, ...state.projects] 
  })),
  
  updateProject: (id, updates) => set((state) => ({
    projects: state.projects.map(p => p.id === id ? { ...p, ...updates } : p),
    currentProject: state.currentProject?.id === id 
      ? { ...state.currentProject, ...updates } 
      : state.currentProject
  })),
  
  deleteProject: (id) => set((state) => ({
    projects: state.projects.filter(p => p.id !== id),
    currentProject: state.currentProject?.id === id ? null : state.currentProject
  })),
  
  setLoading: (loading) => set({ loading }),
  
  setError: (error) => set({ error }),
  
  updateClip: (projectId, clipId, updates) => set((state) => ({
    projects: state.projects.map(p => 
      p.id === projectId 
        ? { ...p, clips: p.clips.map(c => c.id === clipId ? { ...c, ...updates } : c) }
        : p
    ),
    currentProject: state.currentProject?.id === projectId
      ? { 
          ...state.currentProject, 
          clips: state.currentProject.clips.map(c => c.id === clipId ? { ...c, ...updates } : c)
        }
      : state.currentProject
  })),
  
  updateCollection: (projectId, collectionId, updates) => set((state) => ({
    projects: state.projects.map(p => 
      p.id === projectId 
        ? { ...p, collections: p.collections.map(c => c.id === collectionId ? { ...c, ...updates } : c) }
        : p
    ),
    currentProject: state.currentProject?.id === projectId
      ? { 
          ...state.currentProject, 
          collections: state.currentProject.collections.map(c => c.id === collectionId ? { ...c, ...updates } : c)
        }
      : state.currentProject
  })),

  addCollection: (projectId: string, collection: Collection) => {
    set((state) => ({
      projects: state.projects.map(project => 
        project.id === projectId 
          ? {
              ...project,
              collections: [...(project.collections || []), collection]
            }
          : project
      ),
      currentProject: state.currentProject?.id === projectId
        ? {
            ...state.currentProject,
            collections: [...(state.currentProject.collections || []), collection]
          }
        : state.currentProject
    }))
  },

  deleteCollection: (projectId: string, collectionId: string) => {
    set((state) => ({
      projects: state.projects.map(project => 
        project.id === projectId 
          ? {
              ...project,
              collections: project.collections.filter(c => c.id !== collectionId)
            }
          : project
      ),
      currentProject: state.currentProject?.id === projectId
        ? {
            ...state.currentProject,
            collections: state.currentProject.collections.filter(c => c.id !== collectionId)
          }
        : state.currentProject
    }))
  },

  removeClipFromCollection: (projectId: string, collectionId: string, clipId: string) => {
    set((state) => ({
      projects: state.projects.map(project => 
        project.id === projectId 
          ? {
              ...project,
              collections: project.collections.map(collection =>
                collection.id === collectionId
                  ? {
                      ...collection,
                      clip_ids: collection.clip_ids.filter(id => id !== clipId)
                    }
                  : collection
              )
            }
          : project
      ),
      currentProject: state.currentProject?.id === projectId
        ? {
            ...state.currentProject,
            collections: state.currentProject.collections.map(collection =>
              collection.id === collectionId
                ? {
                    ...collection,
                    clip_ids: collection.clip_ids.filter(id => id !== clipId)
                  }
                : collection
            )
          }
        : state.currentProject
    }))
  },

  reorderCollectionClips: async (projectId: string, collectionId: string, newClipIds: string[]) => {
    // 先更新前端状态
    set((state) => ({
      projects: state.projects.map(project => 
        project.id === projectId 
          ? {
              ...project,
              collections: project.collections.map(collection =>
                collection.id === collectionId
                  ? {
                      ...collection,
                      clip_ids: newClipIds
                    }
                  : collection
              )
            }
          : project
      ),
      currentProject: state.currentProject?.id === projectId
        ? {
            ...state.currentProject,
            collections: state.currentProject.collections.map(collection =>
              collection.id === collectionId
                ? {
                    ...collection,
                    clip_ids: newClipIds
                  }
                : collection
            )
          }
        : state.currentProject
    }))
    
    // 调用后端API保存新顺序
    try {
      await projectApi.updateCollection(projectId, collectionId, { clip_ids: newClipIds })
    } catch (error) {
      console.error('Failed to update collection order:', error)
      // 如果后端更新失败，可以考虑回滚前端状态或显示错误提示
    }
  }
}))