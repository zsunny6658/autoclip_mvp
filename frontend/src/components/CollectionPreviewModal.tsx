import React, { useState, useRef, useEffect } from 'react'
import { Modal, Row, Col, List, Button, Space, Typography, Tag, Tooltip, message, Popconfirm } from 'antd'
import { PlayCircleOutlined, PauseCircleOutlined, DownloadOutlined, DeleteOutlined, DragOutlined, CloseOutlined, LeftOutlined, RightOutlined } from '@ant-design/icons'
import ReactPlayer from 'react-player'
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd'
import { Collection, Clip } from '../store/useProjectStore'
import { projectApi } from '../services/api'
import './CollectionPreviewModal.css'

const { Title, Text } = Typography

interface CollectionPreviewModalProps {
  visible: boolean
  collection: Collection | null
  clips: Clip[]
  projectId: string
  onClose: () => void
  onUpdateCollection: (collectionId: string, updates: Partial<Collection>) => void
  onRemoveClip: (collectionId: string, clipId: string) => void
  onReorderClips: (collectionId: string, newClipIds: string[]) => void
  onDelete?: (collectionId: string) => void
}

const CollectionPreviewModal: React.FC<CollectionPreviewModalProps> = ({
  visible,
  collection,
  clips,
  projectId,
  onClose,
  onUpdateCollection,
  onRemoveClip,
  onReorderClips,
  onDelete
}) => {
  const [currentClipIndex, setCurrentClipIndex] = useState(0)
  const [playing, setPlaying] = useState(false)
  const [autoPlay, setAutoPlay] = useState(true)
  const [downloadingClip, setDownloadingClip] = useState<string | null>(null)
  const [downloadingCollection, setDownloadingCollection] = useState(false)
  const [generatingVideo, setGeneratingVideo] = useState(false)
  const [showVideoOverlay, setShowVideoOverlay] = useState(true)
  const playerRef = useRef<ReactPlayer>(null)
  const hideTimeoutRef = useRef<number | null>(null)

  const collectionClips = collection ? clips.filter(clip => collection.clip_ids.includes(clip.id)) : []
  const currentClip = collectionClips[currentClipIndex]

  useEffect(() => {
    if (visible && collectionClips.length > 0) {
      setCurrentClipIndex(0)
      setPlaying(false)
    }
  }, [visible, collection])

  // 处理视频覆盖层的自动隐藏
  const resetHideTimer = () => {
    if (hideTimeoutRef.current) {
      clearTimeout(hideTimeoutRef.current)
    }
    setShowVideoOverlay(true)
    hideTimeoutRef.current = setTimeout(() => {
      setShowVideoOverlay(false)
    }, 3000)
  }

  const handleMouseMove = () => {
    resetHideTimer()
  }

  const handleMouseEnter = () => {
    if (hideTimeoutRef.current) {
      clearTimeout(hideTimeoutRef.current)
    }
    setShowVideoOverlay(true)
  }

  const handleMouseLeave = () => {
    resetHideTimer()
  }

  useEffect(() => {
    if (visible && playing) {
      resetHideTimer()
    }
    return () => {
      if (hideTimeoutRef.current) {
        clearTimeout(hideTimeoutRef.current)
      }
    }
  }, [visible, playing])

  const handleClipSelect = (index: number) => {
    setCurrentClipIndex(index)
    setPlaying(true)
  }

  const handlePlayNext = () => {
    if (currentClipIndex < collectionClips.length - 1) {
      setCurrentClipIndex(currentClipIndex + 1)
      if (autoPlay) {
        setPlaying(true)
      }
    } else {
      setPlaying(false)
    }
  }

  const handlePlayPrevious = () => {
    if (currentClipIndex > 0) {
      setCurrentClipIndex(currentClipIndex - 1)
      if (autoPlay) {
        setPlaying(true)
      }
    }
  }

  const handleVideoEnd = () => {
    if (autoPlay && currentClipIndex < collectionClips.length - 1) {
      handlePlayNext()
    } else {
      setPlaying(false)
    }
  }

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination || !collection) return

    const newClipIds = Array.from(collection.clip_ids)
    const [reorderedItem] = newClipIds.splice(result.source.index, 1)
    newClipIds.splice(result.destination.index, 0, reorderedItem)

    onReorderClips(collection.id, newClipIds)
    
    // 更新当前播放索引
    const currentClipId = collectionClips[currentClipIndex]?.id
    if (currentClipId) {
      const newIndex = newClipIds.indexOf(currentClipId)
      setCurrentClipIndex(newIndex)
    }
  }

  const handleRemoveClip = (clipId: string) => {
    if (!collection) return
    
    onRemoveClip(collection.id, clipId)
    
    // 调整当前播放索引
    const removedIndex = collection.clip_ids.indexOf(clipId)
    if (removedIndex <= currentClipIndex && currentClipIndex > 0) {
      setCurrentClipIndex(currentClipIndex - 1)
    } else if (removedIndex === currentClipIndex && currentClipIndex >= collectionClips.length - 1) {
      setCurrentClipIndex(Math.max(0, collectionClips.length - 2))
    }
  }

  const handleDownloadClip = async (clipId: string) => {
    setDownloadingClip(clipId)
    try {
      await projectApi.downloadVideo(projectId, clipId)
      message.success('切片下载成功')
    } catch (error) {
      console.error('Download clip failed:', error)
      message.error('切片下载失败')
    } finally {
      setDownloadingClip(null)
    }
  }

  const handleDownloadCollection = async () => {
    if (!collection) return
    
    setDownloadingCollection(true)
    try {
      await projectApi.downloadVideo(projectId, undefined, collection.id)
      message.success('合集下载成功')
    } catch (error) {
      console.error('Download collection failed:', error)
      message.error('合集下载失败')
    } finally {
      setDownloadingCollection(false)
    }
  }

  const handleGenerateVideo = async () => {
    if (!collection) return
    
    try {
      setGeneratingVideo(true)
      await projectApi.generateCollectionVideo(projectId, collection.id)
      message.success('开始生成合集视频，请稍后查看下载')
    } catch (error) {
      message.error('生成合集视频失败')
    } finally {
      setGeneratingVideo(false)
    }
  }

  const formatDuration = (clip: Clip) => {
    const start = clip.start_time.split(':')
    const end = clip.end_time.split(':')
    const startSeconds = parseInt(start[0]) * 3600 + parseInt(start[1]) * 60 + parseFloat(start[2].replace(',', '.'))
    const endSeconds = parseInt(end[0]) * 3600 + parseInt(end[1]) * 60 + parseFloat(end[2].replace(',', '.'))
    const duration = endSeconds - startSeconds
    const mins = Math.floor(duration / 60)
    const secs = Math.floor(duration % 60)
    return `${mins}:${String(secs).padStart(2, '0')}`
  }

  if (!collection) return null

  return (
    <Modal
      title={null}
      open={visible}
      onCancel={onClose}
      footer={null}
      width="90vw"
      style={{ top: 20 }}
      bodyStyle={{ padding: 0, height: '90vh' }}
      className="collection-preview-modal"
      closable={false}
      maskClosable={false}
    >
      <div className="collection-preview-container">
        {/* 头部标题栏 */}
        <div className="preview-header">
          <div className="header-left">
            <Title level={4} style={{ margin: 0, color: 'white', display: 'inline-block', marginRight: '12px' }}>
              {collection.collection_title}
            </Title>
            <Text style={{ color: 'rgba(255,255,255,0.6)', fontSize: '13px' }}>
              ({collectionClips.length} 个切片)
            </Text>
          </div>
          <div className="header-right">
            <Space>
              <Button 
                type="primary" 
                icon={<DownloadOutlined />}
                loading={downloadingCollection}
                onClick={handleDownloadCollection}
              >
                下载合集
              </Button>
              <Button 
                type="primary" 
                loading={generatingVideo}
                onClick={handleGenerateVideo}
              >
                生成合集视频
              </Button>
              {onDelete && (
                <Popconfirm
                  title="删除合集"
                  description="确定要删除这个合集吗？此操作不可撤销。"
                  onConfirm={() => onDelete(collection.id)}
                  okText="确定"
                  cancelText="取消"
                >
                  <Button 
                    type="text" 
                    icon={<DeleteOutlined />}
                    style={{ color: 'white' }}
                  >
                    删除
                  </Button>
                </Popconfirm>
              )}
              <Button 
                type="text" 
                icon={<CloseOutlined />} 
                onClick={onClose}
                style={{ color: 'white' }}
              />
            </Space>
          </div>
        </div>

        {/* 主体内容 */}
        <div className="preview-content">
          <Row style={{ height: '100%' }}>
            {/* 左侧视频播放器 */}
            <Col span={16} className="video-section">
              <div 
                className="video-container"
                onMouseMove={handleMouseMove}
                onMouseEnter={handleMouseEnter}
                onMouseLeave={handleMouseLeave}
              >
                {currentClip ? (
                  <>
                    <ReactPlayer
                      ref={playerRef}
                      url={projectApi.getClipVideoUrl(projectId, currentClip.id, currentClip.title || currentClip.generated_title)}
                      width="100%"
                      height="100%"
                      playing={playing}
                      controls
                      onEnded={handleVideoEnd}
                      onPlay={() => setPlaying(true)}
                      onPause={() => setPlaying(false)}
                    />
                    
                    {/* 视频信息覆盖层 */}
                    <div className={`video-info-overlay ${showVideoOverlay ? 'visible' : 'hidden'}`}>
                      <div className="video-header">
                        <div className="video-title">
                          {currentClip.title || currentClip.generated_title}
                        </div>
                        <div className="video-controls">
                          <Button 
                            type="text" 
                            icon={<LeftOutlined />}
                            disabled={currentClipIndex === 0}
                            onClick={handlePlayPrevious}
                            title="上一个切片"
                            className="control-btn"
                          />
                          <Button 
                            type="text" 
                            icon={<RightOutlined />}
                            disabled={currentClipIndex === collectionClips.length - 1}
                            onClick={handlePlayNext}
                            title="下一个切片"
                            className="control-btn"
                          />
                        </div>
                      </div>
                      <div className="video-meta">
                        <Tag color="blue">{formatDuration(currentClip)}</Tag>
                        <Tag color="green">分数: {(currentClip.final_score * 100).toFixed(0)}</Tag>
                        <Text style={{ color: 'white', marginLeft: 8 }}>
                          {currentClipIndex + 1} / {collectionClips.length}
                        </Text>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="empty-video">
                    <PlayCircleOutlined style={{ fontSize: '64px', color: '#d9d9d9' }} />
                    <Text style={{ color: '#999', marginTop: 16 }}>暂无视频内容</Text>
                  </div>
                )}
              </div>
            </Col>

            {/* 右侧切片列表 */}
            <Col span={8} className="playlist-section">
              <div className="playlist-container">
                <div className="playlist-header">
                  <Title level={5} style={{ margin: 0 }}>播放列表</Title>
                  <Text type="secondary">拖拽调整顺序</Text>
                </div>
                
                <DragDropContext onDragEnd={handleDragEnd}>
                  <Droppable droppableId="clips">
                    {(provided) => (
                      <div
                        {...provided.droppableProps}
                        ref={provided.innerRef}
                        className="clips-list"
                      >
                        {collectionClips.map((clip, index) => (
                          <Draggable key={clip.id} draggableId={clip.id} index={index}>
                            {(provided, snapshot) => (
                              <div
                                ref={provided.innerRef}
                                {...provided.draggableProps}
                                className={`clip-item ${
                                  index === currentClipIndex ? 'active' : ''
                                } ${snapshot.isDragging ? 'dragging' : ''}`}
                                onClick={() => handleClipSelect(index)}
                              >
                                <div className="clip-drag-handle" {...provided.dragHandleProps}>
                                  <DragOutlined />
                                </div>
                                
                                <div className="clip-content">
                                  <div className="clip-title">
                                    {clip.title || clip.generated_title}
                                  </div>
                                  <div className="clip-meta">
                                    <Text type="secondary" style={{ fontSize: '12px' }}>
                                      {formatDuration(clip)} • 分数: {(clip.final_score * 100).toFixed(0)}
                                    </Text>
                                  </div>
                                  {clip.recommend_reason && (
                                    <div className="clip-reason">
                                      <Text type="secondary" style={{ fontSize: '11px' }}>
                                        {clip.recommend_reason}
                                      </Text>
                                    </div>
                                  )}
                                </div>

                                <div className="clip-actions">
                                  <Tooltip title="下载切片">
                                    <Button
                                      type="text"
                                      size="small"
                                      icon={<DownloadOutlined />}
                                      loading={downloadingClip === clip.id}
                                      onClick={(e) => {
                                        e.stopPropagation()
                                        handleDownloadClip(clip.id)
                                      }}
                                    />
                                  </Tooltip>
                                  <Popconfirm
                                    title="确定要从合集中移除这个切片吗？"
                                    onConfirm={(e) => {
                                      e?.stopPropagation()
                                      handleRemoveClip(clip.id)
                                    }}
                                    okText="确定"
                                    cancelText="取消"
                                  >
                                    <Button
                                      type="text"
                                      size="small"
                                      icon={<DeleteOutlined />}
                                      danger
                                      onClick={(e) => e.stopPropagation()}
                                    />
                                  </Popconfirm>
                                </div>
                              </div>
                            )}
                          </Draggable>
                        ))}
                        {provided.placeholder}
                      </div>
                    )}
                  </Droppable>
                </DragDropContext>
              </div>
            </Col>
          </Row>
        </div>
      </div>
    </Modal>
  )
}

export default CollectionPreviewModal