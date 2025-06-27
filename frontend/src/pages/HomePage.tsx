import React, { useState, useEffect } from 'react'
import { 
  Layout, 
  Card, 
  Typography, 
  Button, 
  Select, 
  Space, 
  Spin, 
  Empty,
  message 
} from 'antd'
import { 
  PlusOutlined, 
  VideoCameraOutlined 
} from '@ant-design/icons'
import { useNavigate } from 'react-router-dom'
import ProjectCard from '../components/ProjectCard'
import FileUpload from '../components/FileUpload'
import backgroundSvg from '../assets/background.svg'
import { projectApi } from '../services/api'
import { Project, useProjectStore } from '../store/useProjectStore'

const { Content } = Layout
const { Title, Text } = Typography
const { Option } = Select

const HomePage: React.FC = () => {
  const navigate = useNavigate()
  const { projects, setProjects, deleteProject, loading, setLoading } = useProjectStore()
  const [statusFilter, setStatusFilter] = useState<string>('all')

  useEffect(() => {
    loadProjects()
  }, [])

  const loadProjects = async () => {
    setLoading(true)
    try {
      // 从后端API获取真实项目数据
      const projects = await projectApi.getProjects()
      setProjects(projects || [])
    } catch (error) {
      message.error('加载项目失败')
      console.error('Load projects error:', error)
      // 如果API调用失败，设置空数组
      setProjects([])
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteProject = async (id: string) => {
    try {
      await projectApi.deleteProject(id)
      deleteProject(id)
      message.success('项目删除成功')
    } catch (error) {
      message.error('删除项目失败')
      console.error('Delete project error:', error)
    }
  }

  const handleRetryProject = async (id: string) => {
    // 重新加载项目列表以获取最新状态
    await loadProjects()
  }

  const handleStartProcessing = async (projectId: string) => {
    try {
      await projectApi.startProcessing(projectId)
      message.success('开始处理项目')
    } catch (error: any) {
      const errorMessage = error.userMessage || '启动处理失败'
      message.error(errorMessage)
      console.error('Start processing error:', error)
    }
  }

  const handleProjectCardClick = (project: Project) => {
    // 直接导航到项目详情页，无论什么状态
    navigate(`/project/${project.id}`)
  }

  const filteredProjects = projects
    .filter(project => {
      const matchesStatus = statusFilter === 'all' || project.status === statusFilter
      return matchesStatus
    })
    .sort((a, b) => {
      // 按创建时间倒序排列，最新的在前面
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    })

  return (
    <Layout style={{ 
      minHeight: '100vh', 
      background: '#0f0f0f',
      backgroundImage: `url(${backgroundSvg})`,
      backgroundSize: 'cover',
      backgroundPosition: 'center',
      backgroundRepeat: 'no-repeat',
      backgroundAttachment: 'fixed'
    }}>
      <Content style={{ padding: '40px 24px', position: 'relative' }}>
        <div style={{ maxWidth: '1600px', margin: '0 auto', position: 'relative', zIndex: 1 }}>
          {/* 页面标题区域 */}
          <div style={{ 
            marginBottom: '48px',
            textAlign: 'center',
            padding: '20px 0'
          }}>
            <Title 
              level={1} 
              style={{ 
                color: '#ffffff',
                fontSize: '48px',
                fontWeight: 700,
                marginBottom: '12px',
                background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                textShadow: '0 4px 20px rgba(79, 172, 254, 0.3)',
                letterSpacing: '1px'
              }}
            >
              AI视频切片工具
            </Title>
            <Text style={{ 
              color: '#cccccc',
              fontSize: '18px',
              display: 'block',
              marginBottom: '32px',
              fontWeight: 300,
              letterSpacing: '0.5px'
            }}>
              智能分析视频内容，自动生成精彩片段
            </Text>
          </div>

          {/* 文件上传区域 */}
          <div style={{ 
            marginBottom: '48px',
            display: 'flex',
            justifyContent: 'center'
          }}>
            <div style={{
              width: '100%',
              maxWidth: '900px',
              background: 'rgba(26, 26, 46, 0.8)',
              backdropFilter: 'blur(20px)',
              borderRadius: '24px',
              border: '1px solid rgba(79, 172, 254, 0.2)',
              padding: '32px',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.05)'
            }}>
              <FileUpload onUploadSuccess={(projectId: string) => {
                // 处理完成后刷新项目列表
                loadProjects()
                // 开始处理项目
                handleStartProcessing(projectId)
              }} />
            </div>
          </div>

          {/* 项目管理区域 */}
          <div style={{
            background: 'rgba(26, 26, 46, 0.7)',
            backdropFilter: 'blur(20px)',
            borderRadius: '24px',
            border: '1px solid rgba(79, 172, 254, 0.15)',
            padding: '32px',
            marginBottom: '32px',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2), 0 0 0 1px rgba(255, 255, 255, 0.03)'
          }}>
            {/* 项目列表标题区域 */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              marginBottom: '24px',
              paddingBottom: '16px',
              borderBottom: '1px solid rgba(79, 172, 254, 0.1)'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <Title 
                  level={2} 
                  style={{ 
                    margin: 0,
                    color: '#ffffff',
                    fontSize: '24px',
                    fontWeight: 600,
                    background: 'linear-gradient(135deg, #ffffff 0%, #cccccc 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                    backgroundClip: 'text'
                  }}
                >
                  我的项目
                </Title>
                <div style={{
                  padding: '8px 16px',
                  background: 'rgba(79, 172, 254, 0.1)',
                  borderRadius: '20px',
                  border: '1px solid rgba(79, 172, 254, 0.3)',
                  backdropFilter: 'blur(10px)'
                }}>
                  <Text style={{ color: '#4facfe', fontWeight: 600, fontSize: '14px' }}>
                    共 {filteredProjects.length} 个项目
                  </Text>
                </div>
              </div>
              
              {/* 状态筛选移到右侧 */}
              <div style={{ 
                display: 'flex', 
                alignItems: 'center'
              }}>
                <Select
                  placeholder="状态筛选"
                  value={statusFilter}
                  onChange={setStatusFilter}
                  style={{ 
                    minWidth: '160px',
                    height: '40px',
                    background: 'rgba(38, 38, 38, 0.8)',
                    border: '1px solid rgba(79, 172, 254, 0.3)',
                    borderRadius: '12px',
                    color: '#ffffff'
                  }}
                  dropdownStyle={{
                    background: 'rgba(38, 38, 38, 0.95)',
                    border: '1px solid rgba(79, 172, 254, 0.3)',
                    backdropFilter: 'blur(20px)'
                  }}
                  allowClear
                >
                  <Option value="all">全部状态</Option>
                  <Option value="completed">已完成</Option>
                  <Option value="processing">处理中</Option>
                  <Option value="error">处理失败</Option>
                </Select>
              </div>
            </div>

            {/* 项目列表内容 */}
             <div>
               {loading ? (
                 <div style={{ 
                   textAlign: 'center', 
                   padding: '60px 0',
                   background: '#262626',
                   borderRadius: '12px',
                   border: '1px solid #404040'
                 }}>
                   <Spin size="large" />
                   <div style={{ 
                     marginTop: '20px', 
                     color: '#cccccc',
                     fontSize: '16px'
                   }}>
                     正在加载项目列表...
                   </div>
                 </div>
               ) : filteredProjects.length === 0 ? (
                 <div style={{
                   textAlign: 'center',
                   padding: '60px 0',
                   background: '#262626',
                   borderRadius: '12px',
                   border: '1px solid #404040'
                 }}>
                   <Empty
                     image={Empty.PRESENTED_IMAGE_SIMPLE}
                     description={
                       <div>
                         <Text type="secondary">
                           {projects.length === 0 ? '还没有项目，请使用上方的导入区域创建第一个项目' : '没有找到匹配的项目'}
                         </Text>
                       </div>
                     }
                   />
                 </div>
               ) : (
                 <div style={{
                   display: 'grid',
                   gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
                   gap: '16px',
                   justifyContent: 'start',
                   padding: '6px 0'
                 }}>
                   {filteredProjects.map((project: Project) => (
                     <div key={project.id} style={{ position: 'relative', zIndex: 1 }}>
                       <ProjectCard 
                         project={project} 
                         onDelete={handleDeleteProject}
                         onRetry={handleRetryProject}
                         onClick={() => handleProjectCardClick(project)}
                       />
                     </div>
                   ))}
                 </div>
               )}
             </div>
           </div>
         </div>
      </Content>
    </Layout>
  )
}

export default HomePage