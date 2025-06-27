import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { 
  Layout, 
  Card, 
  Typography, 
  Button, 
  Space, 
  Tabs, 
  Row, 
  Col, 
  Progress, 
  Alert, 
  Spin, 
  Empty,
  message,
  Input,
  Select,
  Tag,
  Divider,
  List
} from 'antd'
import { 
  ArrowLeftOutlined, 
  DownloadOutlined, 
  ReloadOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ExportOutlined,
  UpOutlined,
  DownOutlined
} from '@ant-design/icons'
import { useProjectStore } from '../store/useProjectStore'
import { projectApi } from '../services/api'
import ClipCard from '../components/ClipCard'
import CollectionCard from '../components/CollectionCard'
import CollectionCardMini from '../components/CollectionCardMini'
import CollectionPreviewModal from '../components/CollectionPreviewModal'
import CreateCollectionModal from '../components/CreateCollectionModal'

const { Content } = Layout
const { Title, Text } = Typography
const { TabPane } = Tabs
const { TextArea } = Input
const { Option } = Select

const ProjectDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { 
    currentProject, 
    loading, 
    error,
    setCurrentProject,
    updateClip,
    updateCollection,
    addCollection,
    deleteCollection,
    removeClipFromCollection,
    reorderCollectionClips
  } = useProjectStore()
  
  const [processingStatus, setProcessingStatus] = useState<any>(null)
  const [statusLoading, setStatusLoading] = useState(false)
  const [showCreateCollection, setShowCreateCollection] = useState(false)
  // 移除不再需要的状态变量，新组件内部管理
  const [sortBy, setSortBy] = useState<'time' | 'score'>('time')
  const [progressCollapsed, setProgressCollapsed] = useState(false)
  const [showCollectionDetail, setShowCollectionDetail] = useState(false)
  const [selectedCollection, setSelectedCollection] = useState<any>(null)

  useEffect(() => {
    if (id) {
      loadProject()
      loadProcessingStatus()
    }
  }, [id])

  // 当任务完成时自动折叠进度显示
  useEffect(() => {
    if (processingStatus && (processingStatus.status === 'completed' || processingStatus.status === 'error')) {
      setProgressCollapsed(true)
    } else if (processingStatus && processingStatus.status === 'processing') {
      setProgressCollapsed(false)
    }
  }, [processingStatus])

  const loadProject = async () => {
    if (!id) return
    try {
      const project = await projectApi.getProject(id)
      setCurrentProject(project)
    } catch (error) {
      console.error('Failed to load project:', error)
      message.error('加载项目失败')
    }
  }

  const loadProcessingStatus = async () => {
    if (!id) return
    setStatusLoading(true)
    try {
      const status = await projectApi.getProcessingStatus(id)
      setProcessingStatus(status)
    } catch (error) {
      console.error('Failed to load processing status:', error)
    } finally {
      setStatusLoading(false)
    }
  }

  const handleStartProcessing = async () => {
    if (!id) return
    try {
      await projectApi.startProcessing(id)
      message.success('开始处理')
      loadProcessingStatus()
    } catch (error) {
      console.error('Failed to start processing:', error)
      message.error('启动处理失败')
    }
  }

  const handleDownloadProject = async () => {
    if (!id) return
    try {
      await projectApi.downloadVideo(id)
      message.success('下载开始')
    } catch (error) {
      console.error('Failed to download:', error)
      message.error('下载失败')
    }
  }

  const handleExportMetadata = async () => {
    if (!id) return
    try {
      await projectApi.exportMetadata(id)
      message.success('导出成功')
    } catch (error) {
      console.error('Failed to export:', error)
      message.error('导出失败')
    }
  }

  const handleRestartStep = async (step: number) => {
    if (!id) return
    try {
      await projectApi.restartStep(id, step)
      message.success(`步骤 ${step} 重启成功`)
      loadProcessingStatus()
    } catch (error) {
      console.error('Failed to restart step:', error)
      message.error(`步骤 ${step} 重启失败`)
    }
  }

  const getStepDetails = () => {
    return [
      { number: 1, name: '提取大纲', description: '从字幕文件中提取内容大纲' },
      { number: 2, name: '时间定位', description: '定位每个大纲对应的时间区间' },
      { number: 3, name: '内容评分', description: '对内容片段进行评分和筛选' },
      { number: 4, name: '标题生成', description: '为高分片段生成爆点标题' },
      { number: 5, name: '主题聚类', description: '将相似主题的片段聚类成合集' },
      { number: 6, name: '视频生成', description: '生成切片视频和合集视频' }
    ]
  }

  const getStepStatus = (stepNumber: number, status: any) => {
    if (!status) return 'pending'
    
    // 处理部分完成状态
    if (status.status === 'partial' || status.status === 'completed') {
      if (status.current_step >= stepNumber) return 'completed'
      return 'pending'
    }
    
    if (status.status === 'error' && status.current_step === stepNumber) return 'error'
    if (status.current_step > stepNumber) return 'completed'
    if (status.current_step === stepNumber && status.status === 'processing') return 'processing'
    if (status.current_step < stepNumber) return 'pending'
    return 'pending'
  }

  const getStepStatusColor = (stepNumber: number, status: any) => {
    const stepStatus = getStepStatus(stepNumber, status)
    switch (stepStatus) {
      case 'completed': return '#52c41a'
      case 'processing': return '#1890ff'
      case 'error': return '#ff4d4f'
      default: return '#d9d9d9'
    }
  }

  const getStepBackgroundColor = (stepNumber: number, status: any) => {
    const stepStatus = getStepStatus(stepNumber, status)
    switch (stepStatus) {
      case 'completed': return '#f6ffed'
      case 'processing': return '#e6f7ff'
      case 'error': return '#fff2f0'
      default: return '#fafafa'
    }
  }

  const getStepStatusIcon = (stepNumber: number, status: any) => {
    const stepStatus = getStepStatus(stepNumber, status)
    switch (stepStatus) {
      case 'completed': return '✓'
      case 'processing': return '⟳'
      case 'error': return '✗'
      default: return stepNumber.toString()
    }
  }

  const handleCreateCollection = async (title: string, summary: string, clipIds: string[]) => {
    if (!currentProject) {
      message.error('项目信息不存在')
      return
    }
    
    try {
      await projectApi.createCollection(currentProject.id, {
        collection_title: title,
        collection_summary: summary,
        clip_ids: clipIds
      })
      
      message.success('合集创建成功')
      setShowCreateCollection(false)
      
      // 重新加载项目数据
      loadProject()
    } catch (error) {
      console.error('创建合集失败:', error)
      message.error('创建合集失败')
    }
  }

  const handleViewCollection = (collection: any) => {
    setSelectedCollection(collection)
    setShowCollectionDetail(true)
  }

  const handleRemoveClipFromCollection = (collectionId: string, clipId: string) => {
    if (!id) return
    removeClipFromCollection(id, collectionId, clipId)
  }

  const handleDeleteCollection = async (collectionId: string) => {
    if (!id) return
    try {
      await projectApi.deleteCollection(id, collectionId)
      deleteCollection(id, collectionId)
      message.success('合集删除成功')
      // 如果当前正在查看被删除的合集，关闭详情页
      if (selectedCollection?.id === collectionId) {
        setShowCollectionDetail(false)
        setSelectedCollection(null)
      }
    } catch (error) {
      console.error('Failed to delete collection:', error)
      message.error('删除合集失败')
    }
  }

  const handleReorderCollectionClips = (collectionId: string, newClipIds: string[]) => {
    if (!id) return
    reorderCollectionClips(id, collectionId, newClipIds)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success'
      case 'processing': return 'processing'
      case 'error': return 'exception'
      default: return 'normal'
    }
  }

  const getProgressPercent = (status: any) => {
    if (!status) return 0
    if (status.status === 'completed') return 100
    if (status.status === 'error') return 0
    return status.progress || 0
  }

  // 排序视频片段
  const getSortedClips = () => {
    if (!currentProject?.clips) return []
    
    const clips = [...currentProject.clips]
    
    if (sortBy === 'score') {
      return clips.sort((a, b) => b.final_score - a.final_score)
    } else {
      // 按时间排序 - 将时间字符串转换为秒数进行比较
      return clips.sort((a, b) => {
        const getTimeInSeconds = (timeStr: string) => {
          const parts = timeStr.split(':')
          const hours = parseInt(parts[0])
          const minutes = parseInt(parts[1])
          const seconds = parseFloat(parts[2].replace(',', '.'))
          return hours * 3600 + minutes * 60 + seconds
        }
        
        const aTime = getTimeInSeconds(a.start_time)
        const bTime = getTimeInSeconds(b.start_time)
        return aTime - bTime
      })
    }
  }

  if (loading) {
    return (
      <Content style={{ padding: '24px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Spin size="large" />
      </Content>
    )
  }

  if (error || !currentProject) {
    return (
      <Content style={{ padding: '24px' }}>
        <Alert
          message="加载失败"
          description={error || '项目不存在'}
          type="error"
          action={
            <Button size="small" onClick={() => navigate('/')}>
              返回首页
            </Button>
          }
        />
      </Content>
    )
  }

  return (
    <Content style={{ padding: '24px' }}>
      {/* 简化的项目头部 */}
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <Button 
            type="link" 
            icon={<ArrowLeftOutlined />} 
            onClick={() => navigate('/')}
            style={{ padding: 0, marginBottom: '8px' }}
          >
            返回项目列表
          </Button>
          <Title level={2} style={{ margin: 0 }}>
            {currentProject.name}
          </Title>
        </div>
        
        <Space>
          {currentProject.status === 'uploading' && (
            <Button 
              type="primary" 
              onClick={handleStartProcessing}
              loading={statusLoading}
            >
              开始处理
            </Button>
          )}
          
          {currentProject.status === 'completed' && (
            <>
              <Button 
                icon={<ExportOutlined />}
                onClick={handleExportMetadata}
              >
                导出数据
              </Button>
              <Button 
                type="primary" 
                icon={<DownloadOutlined />}
                onClick={handleDownloadProject}
              >
                下载视频
              </Button>
            </>
          )}
        </Space>
      </div>

      {/* 主要内容 */}
      {currentProject.status === 'completed' ? (
        <div>
          {/* AI合集横向滚动区域 */}
          {currentProject.collections && currentProject.collections.length > 0 && (
            <Card style={{ marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <Title level={4} style={{ margin: 0 }}>AI推荐合集</Title>
                  <Text type="secondary">
                    AI 已为您推荐了 {currentProject.collections.length} 个主题合集
                  </Text>
                </div>
                <Button 
                  type="primary" 
                  icon={<PlusOutlined />}
                  onClick={() => setShowCreateCollection(true)}
                >
                  创建合集
                </Button>
              </div>
              
              <div 
                className="collections-scroll-container"
                style={{ 
                  display: 'flex',
                  gap: '16px',
                  overflowX: 'auto',
                  paddingBottom: '8px'
                }}
              >
                {currentProject.collections
                  .sort((a, b) => {
                    // 按创建时间倒序排列，最新的在前面
                    const timeA = a.created_at ? new Date(a.created_at).getTime() : 0
                    const timeB = b.created_at ? new Date(b.created_at).getTime() : 0
                    return timeB - timeA
                  })
                  .map((collection) => (
                  <CollectionCardMini
                    key={collection.id}
                    collection={collection}
                    clips={currentProject.clips || []}
                    onView={handleViewCollection}
                    onGenerateVideo={(collectionId) => {
                      message.info('开始生成合集视频...')
                      // TODO: 实现合集视频生成
                    }}
                    onDelete={handleDeleteCollection}
                  />
                ))}
              </div>
            </Card>
          )}
          
          {/* 视频片段区域 */}
          <Card 
            style={{
              borderRadius: '16px',
              border: '1px solid #303030',
              background: 'linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
              <div>
                <Title level={4} style={{ margin: 0, color: '#ffffff', fontWeight: 600 }}>视频片段</Title>
                <Text type="secondary" style={{ color: '#b0b0b0', fontSize: '14px' }}>
                  AI 已为您生成了 {currentProject.clips?.length || 0} 个精彩片段
                </Text>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                {/* 排序控件 */}
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px',
                  padding: '8px 12px',
                  background: 'rgba(255,255,255,0.05)',
                  borderRadius: '12px',
                  border: '1px solid #404040'
                }}>
                  <Text style={{ fontSize: '12px', color: '#888', fontWeight: 500 }}>排序</Text>
                  <Select
                    value={sortBy}
                    onChange={(value) => setSortBy(value)}
                    size="small"
                    style={{ width: 100 }}
                    dropdownStyle={{
                      background: '#1f1f1f',
                      border: '1px solid #404040'
                    }}
                    options={[
                      { 
                        value: 'time', 
                        label: (
                          <span style={{ color: '#fff', fontSize: '12px' }}>时间</span>
                        )
                      },
                      { 
                        value: 'score', 
                        label: (
                          <span style={{ color: '#fff', fontSize: '12px' }}>评分</span>
                        )
                      }
                    ]}
                  />
                </div>
                
                {(!currentProject.collections || currentProject.collections.length === 0) && (
                  <Button 
                    type="primary" 
                    icon={<PlusOutlined />}
                    onClick={() => setShowCreateCollection(true)}
                    style={{
                      borderRadius: '8px',
                      background: 'linear-gradient(45deg, #1890ff, #36cfc9)',
                      border: 'none',
                      fontWeight: 500,
                      height: '36px'
                    }}
                  >
                    创建合集
                  </Button>
                )}
              </div>
            </div>
            
            {currentProject.clips && currentProject.clips.length > 0 ? (
              <div 
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
                  gap: '20px',
                  padding: '8px 0'
                }}
              >
                {getSortedClips().map((clip) => (
                  <ClipCard
                    key={clip.id}
                    clip={clip}
                    videoUrl={projectApi.getClipVideoUrl(currentProject.id, clip.id, clip.generated_title || clip.title)}
                    onDownload={(clipId) => projectApi.downloadVideo(currentProject.id, clipId)}
                  />
                ))}
              </div>
            ) : (
              <div style={{ 
                padding: '60px 0',
                textAlign: 'center',
                background: 'rgba(255,255,255,0.02)',
                borderRadius: '12px',
                border: '1px dashed #404040'
              }}>
                <Empty 
                  description={
                    <Text style={{ color: '#888', fontSize: '14px' }}>暂无视频片段</Text>
                  }
                  image={<PlayCircleOutlined style={{ fontSize: '48px', color: '#555' }} />}
                />
              </div>
            )}
          </Card>
        </div>
      ) : (
        <Card>
          <Empty 
            image={<PlayCircleOutlined style={{ fontSize: '64px', color: '#d9d9d9' }} />}
            description={
              <div>
                <Text>项目还未完成处理</Text>
                <br />
                <Text type="secondary">处理完成后可查看视频片段和AI合集</Text>
              </div>
            }
          />
        </Card>
      )}

      {/* 创建合集模态框 */}
      <CreateCollectionModal
        visible={showCreateCollection}
        clips={currentProject.clips || []}
        onCancel={() => setShowCreateCollection(false)}
        onCreate={handleCreateCollection}
      />
      
      {/* 合集预览模态框 */}
      <CollectionPreviewModal
        visible={showCollectionDetail}
        collection={selectedCollection}
        clips={currentProject.clips || []}
        projectId={currentProject.id}
        onClose={() => {
          setShowCollectionDetail(false)
          setSelectedCollection(null)
        }}
        onUpdateCollection={(collectionId, updates) => 
          updateCollection(currentProject.id, collectionId, updates)
        }
        onRemoveClip={handleRemoveClipFromCollection}
        onReorderClips={handleReorderCollectionClips}
        onDelete={handleDeleteCollection}
      />
    </Content>
  )
}

export default ProjectDetailPage