import React, { useState, useEffect } from 'react'
import { Card, Tag, Button, Space, Typography, Progress, Popconfirm, message } from 'antd'
import { PlayCircleOutlined, DeleteOutlined, EyeOutlined, DownloadOutlined, ReloadOutlined, LoadingOutlined } from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import { Project } from '../store/useProjectStore'
import { projectApi } from '../services/api'
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

dayjs.extend(relativeTime)

const { Text, Title } = Typography
const { Meta } = Card

interface ProjectCardProps {
  project: Project
  onDelete: (id: string) => void
  onRetry?: (id: string) => void
  onClick?: () => void
}

interface LogEntry {
  timestamp: string
  module: string
  level: string
  message: string
}

const ProjectCard: React.FC<ProjectCardProps> = ({ project, onDelete, onRetry, onClick }) => {
  const navigate = useNavigate()
  const [videoThumbnail, setVideoThumbnail] = useState<string | null>(null)
  const [isRetrying, setIsRetrying] = useState(false)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const [currentLogIndex, setCurrentLogIndex] = useState(0)

  // 生成项目视频缩略图
  useEffect(() => {
    const generateThumbnail = async () => {
      if (!project.video_path) return
      
      try {
        const video = document.createElement('video')
        video.crossOrigin = 'anonymous'
        video.muted = true
        
        const videoUrl = projectApi.getProjectFileUrl(project.id, 'input/input.mp4')
        
        video.onloadedmetadata = () => {
          console.log('开始加载视频:', video.src)
          video.currentTime = Math.min(5, video.duration / 4) // 取视频1/4处或5秒处的帧
        }
        
        video.onseeked = () => {
          try {
            console.log('尝试加载视频:', videoUrl)
            const canvas = document.createElement('canvas')
            const ctx = canvas.getContext('2d')
            if (!ctx) return
            
            canvas.width = video.videoWidth
            canvas.height = video.videoHeight
            ctx.drawImage(video, 0, 0)
            
            const thumbnail = canvas.toDataURL('image/jpeg', 0.8)
            setVideoThumbnail(thumbnail)
            console.log('项目缩略图生成成功')
          } catch (error) {
            console.error('生成缩略图失败:', error)
          }
        }
        
        video.onerror = (error) => {
          console.error('视频加载失败:', error)
        }
        
        video.src = videoUrl
      } catch (error) {
        console.error('生成缩略图时发生错误:', error)
      }
    }
    
    generateThumbnail()
  }, [project.id, project.video_path])

  // 获取项目日志（仅在处理中时）
  useEffect(() => {
    if (project.status !== 'processing') {
      setLogs([])
      return
    }

    const fetchLogs = async () => {
      try {
        const response = await projectApi.getProjectLogs(project.id, 20)
        setLogs(response.logs.filter(log => 
          log.message.includes('Step') || 
          log.message.includes('开始') || 
          log.message.includes('完成') ||
          log.message.includes('处理') ||
          log.level === 'ERROR'
        ))
      } catch (error) {
        console.error('获取日志失败:', error)
      }
    }

    // 立即获取一次
    fetchLogs()
    
    // 每3秒更新一次日志
    const logInterval = setInterval(fetchLogs, 3000)
    
    return () => clearInterval(logInterval)
  }, [project.id, project.status])

  // 日志轮播
  useEffect(() => {
    if (logs.length <= 1) return
    
    const interval = setInterval(() => {
      setCurrentLogIndex(prev => (prev + 1) % logs.length)
    }, 2000) // 每2秒切换一条日志
    
    return () => clearInterval(interval)
  }, [logs.length])

  const getStatusColor = (status: Project['status']) => {
    switch (status) {
      case 'completed': return 'success'
      case 'processing': return 'processing'
      case 'error': return 'error'
      case 'uploading': return 'default'
      default: return 'default'
    }
  }

  const getStatusText = (status: Project['status']) => {
    switch (status) {
      case 'completed': return '已完成'
      case 'processing': return '处理中'
      case 'error': return '处理失败'
      case 'uploading': return '上传中'
      default: return '未知状态'
    }
  }

  const getProgressPercent = () => {
    if (project.status === 'completed') return 100
    if (project.status === 'error') return 0
    if (project.current_step && project.total_steps) {
      return Math.round((project.current_step / project.total_steps) * 100)
    }
    return 0
  }

  const handleRetry = async () => {
    if (isRetrying) return
    
    setIsRetrying(true)
    try {
      await projectApi.retryProcessing(project.id)
      message.success('已开始重试处理项目')
      if (onRetry) {
        onRetry(project.id)
      }
    } catch (error) {
      console.error('重试失败:', error)
      message.error('重试失败，请稍后再试')
    } finally {
      setIsRetrying(false)
    }
  }

  return (
    <Card
      hoverable
      className="project-card"
      style={{ 
        width: 200, 
        height: 240,
        borderRadius: '12px',
        overflow: 'hidden',
        background: 'linear-gradient(145deg, #1e1e1e 0%, #2a2a2a 100%)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
        cursor: 'pointer',
        marginBottom: '0px'
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'translateY(-4px)'
        e.currentTarget.style.boxShadow = '0 8px 30px rgba(0, 0, 0, 0.4)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'translateY(0)'
        e.currentTarget.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)'
      }}
      bodyStyle={{
        padding: '12px',
        background: 'transparent',
        height: 'calc(100% - 120px)',
        display: 'flex',
        flexDirection: 'column'
      }}
      cover={
        <div 
          style={{ 
            height: 120, 
            position: 'relative',
            background: videoThumbnail 
              ? `url(${videoThumbnail}) center/cover` 
              : 'linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            overflow: 'hidden'
          }}
          onClick={() => {
            if (onClick) {
              onClick()
            } else {
              navigate(`/project/${project.id}`)
            }
          }}
        >
          {!videoThumbnail && (
            <div style={{ textAlign: 'center' }}>
              <PlayCircleOutlined 
                style={{ 
                  fontSize: '40px', 
                  color: 'rgba(255, 255, 255, 0.9)',
                  marginBottom: '4px',
                  filter: 'drop-shadow(0 2px 8px rgba(0,0,0,0.3))'
                }} 
              />
              <div style={{ 
                color: 'rgba(255, 255, 255, 0.8)', 
                fontSize: '12px',
                fontWeight: 500
              }}>
                点击预览
              </div>
            </div>
          )}
          
          {/* 状态标签 */}
          <div style={{
            position: 'absolute',
            top: '8px',
            right: '8px'
          }}>
            <Tag 
              color={getStatusColor(project.status)}
              style={{
                borderRadius: '4px',
                border: 'none',
                fontWeight: 500,
                fontSize: '10px',
                padding: '1px 6px',
                lineHeight: '16px',
                height: '18px'
              }}
            >
              {getStatusText(project.status)}
            </Tag>
          </div>
          
          {/* 更新时间和操作按钮 - 移动到封面底部 */}
          <div style={{
            position: 'absolute',
            bottom: '6px',
            left: '8px',
            right: '8px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            background: 'rgba(0, 0, 0, 0.7)',
            backdropFilter: 'blur(10px)',
            borderRadius: '4px',
            padding: '4px 6px',
            height: '24px'
          }}>
            <Text style={{ fontSize: '12px', color: 'rgba(255, 255, 255, 0.8)' }}>
              {dayjs(project.updated_at).fromNow()}
            </Text>
            
            {/* 操作按钮 */}
            <div style={{
              display: 'flex',
              gap: '4px'
            }}>
              {/* 失败状态：只显示重试和删除按钮 */}
              {project.status === 'error' ? (
                <>
                  <Button
                    type="text"
                    icon={<ReloadOutlined />}
                    loading={isRetrying}
                    onClick={(e) => {
                      e.stopPropagation()
                      handleRetry()
                    }}
                    style={{
                      height: '20px',
                      width: '20px',
                      borderRadius: '3px',
                      color: '#52c41a',
                      border: '1px solid rgba(82, 196, 26, 0.5)',
                      background: 'rgba(82, 196, 26, 0.1)',
                      padding: 0,
                      minWidth: '20px',
                      fontSize: '10px'
                    }}
                  />
                  
                  <Popconfirm
                    title="确定要删除这个项目吗？"
                    description="删除后无法恢复"
                    onConfirm={(e) => {
                      e?.stopPropagation()
                      onDelete(project.id)
                    }}
                    onCancel={(e) => {
                      e?.stopPropagation()
                    }}
                    okText="确定"
                    cancelText="取消"
                  >
                    <Button
                      type="text"
                      icon={<DeleteOutlined />}
                      onClick={(e) => {
                        e.stopPropagation()
                      }}
                      style={{
                        height: '20px',
                        width: '20px',
                        borderRadius: '3px',
                        color: '#ff6b6b',
                        border: '1px solid rgba(255, 107, 107, 0.5)',
                        background: 'rgba(255, 107, 107, 0.1)',
                        padding: 0,
                        minWidth: '20px',
                        fontSize: '10px'
                      }}
                    />
                  </Popconfirm>
                </>
              ) : (
                /* 其他状态：显示下载和删除按钮 */
                <>
                  <Space size={4}>
                    {/* 下载按钮 - 仅在完成状态显示 */}
                    {project.status === 'completed' && (
                      <Button
                        type="text"
                        icon={<DownloadOutlined />}
                        onClick={(e) => {
                          e.stopPropagation()
                          // 实现下载功能
                          message.info('下载功能开发中...')
                        }}
                        style={{
                          width: '20px',
                          height: '20px',
                          borderRadius: '3px',
                          color: 'rgba(255, 255, 255, 0.8)',
                          border: '1px solid rgba(255, 255, 255, 0.2)',
                          background: 'rgba(255, 255, 255, 0.1)',
                          padding: 0,
                          minWidth: '20px',
                          fontSize: '10px'
                        }}
                      />
                    )}
                    
                    {/* 删除按钮 */}
                    <Popconfirm
                      title="确定要删除这个项目吗？"
                      description="删除后无法恢复"
                      onConfirm={(e) => {
                        e?.stopPropagation()
                        onDelete(project.id)
                      }}
                      onCancel={(e) => {
                        e?.stopPropagation()
                      }}
                      okText="确定"
                      cancelText="取消"
                    >
                      <Button
                        type="text"
                        icon={<DeleteOutlined />}
                        onClick={(e) => {
                          e.stopPropagation()
                        }}
                        style={{
                          width: '20px',
                          height: '20px',
                          borderRadius: '3px',
                          color: 'rgba(255, 255, 255, 0.8)',
                          border: '1px solid rgba(255, 255, 255, 0.2)',
                          background: 'rgba(255, 255, 255, 0.1)',
                          padding: 0,
                          minWidth: '20px',
                          fontSize: '10px'
                        }}
                      />
                    </Popconfirm>
                  </Space>
                 </>
               )}
            </div>
          </div>
        </div>
      }
    >
      <div style={{ padding: '0', flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
        <div>
          {/* 进度条和日志显示 */}
          {project.status === 'processing' && (
            <div style={{ marginBottom: '8px' }}>
              {/* 进度条 */}
              {project.current_step && project.total_steps && (
                <div style={{ marginBottom: '6px' }}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between', 
                    alignItems: 'center',
                    marginBottom: '3px'
                  }}>
                    <Text style={{ fontSize: '11px', color: '#999999' }}>
                      处理进度
                    </Text>
                    <Text style={{ fontSize: '11px', color: '#ffffff', fontWeight: 500 }}>
                      {Math.round((project.current_step / project.total_steps) * 100)}%
                    </Text>
                  </div>
                  <Progress 
                    percent={Math.round((project.current_step / project.total_steps) * 100)} 
                    size="small" 
                    showInfo={false}
                    strokeColor={{
                      '0%': '#667eea',
                      '100%': '#764ba2',
                    }}
                    trailColor="rgba(255, 255, 255, 0.1)"
                    strokeWidth={4}
                  />
                </div>
              )}
              
              {/* 实时日志轮播 */}
              {logs.length > 0 && (
                <div style={{
                  background: 'rgba(0, 0, 0, 0.3)',
                  borderRadius: '4px',
                  padding: '6px 8px',
                  minHeight: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  border: '1px solid rgba(102, 126, 234, 0.2)'
                }}>
                  <LoadingOutlined style={{ color: '#667eea', fontSize: '12px' }} />
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <Text style={{ 
                      fontSize: '10px', 
                      color: '#ffffff',
                      lineHeight: '12px',
                      display: 'block',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis'
                    }}>
                      {logs[currentLogIndex]?.message || '正在处理...'}
                    </Text>
                    <Text style={{ 
                      fontSize: '9px', 
                      color: '#999999',
                      lineHeight: '10px'
                    }}>
                      {logs[currentLogIndex]?.timestamp ? 
                        dayjs(logs[currentLogIndex].timestamp).format('HH:mm:ss') : 
                        ''
                      }
                    </Text>
                  </div>
                  {logs.length > 1 && (
                    <div style={{
                      display: 'flex',
                      gap: '2px'
                    }}>
                      {logs.slice(0, Math.min(3, logs.length)).map((_, index) => (
                        <div
                          key={index}
                          style={{
                            width: '4px',
                            height: '4px',
                            borderRadius: '50%',
                            background: index === currentLogIndex % Math.min(3, logs.length) ? '#667eea' : 'rgba(255, 255, 255, 0.3)',
                            transition: 'background 0.3s'
                          }}
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          {/* 项目名称 */}
          <div style={{ marginBottom: '8px' }}>
            <Text strong style={{ 
              fontSize: '15px', 
              color: '#ffffff',
              fontWeight: 600,
              lineHeight: '18px',
              display: '-webkit-box',
              WebkitLineClamp: 2,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden'
            }}>
              {project.name}
            </Text>
          </div>
          
          {/* 统计信息 */}
          <div style={{ 
            display: 'flex', 
            gap: '6px'
          }}>
            <div style={{
              background: 'rgba(102, 126, 234, 0.15)',
              border: '1px solid rgba(102, 126, 234, 0.3)',
              borderRadius: '4px',
              padding: '4px 6px',
              textAlign: 'center',
              flex: 1
            }}>
              <div style={{ color: '#667eea', fontSize: '12px', fontWeight: 600, lineHeight: '14px' }}>
                {project.clips?.length || 0}
              </div>
              <div style={{ color: '#999999', fontSize: '9px', lineHeight: '10px' }}>
                切片
              </div>
            </div>
            <div style={{
              background: 'rgba(118, 75, 162, 0.15)',
              border: '1px solid rgba(118, 75, 162, 0.3)',
              borderRadius: '4px',
              padding: '4px 6px',
              textAlign: 'center',
              flex: 1
            }}>
              <div style={{ color: '#764ba2', fontSize: '12px', fontWeight: 600, lineHeight: '14px' }}>
                {project.collections?.length || 0}
              </div>
              <div style={{ color: '#999999', fontSize: '9px', lineHeight: '10px' }}>
                合集
              </div>
            </div>
          </div>

        </div>
      </div>
    </Card>
  )
}

export default ProjectCard