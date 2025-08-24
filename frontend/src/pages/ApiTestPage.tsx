import React, { useState, useEffect } from 'react'
import { Card, Button, Space, Typography, Alert, List } from 'antd'
import { projectApi } from '../services/api'
import ENV_CONFIG from '../config/env'

const { Title, Text } = Typography

interface ApiTestResult {
  endpoint: string
  url: string
  status: 'success' | 'error' | 'loading'
  response?: any
  error?: string
  timestamp: string
}

export const ApiTestPage: React.FC = () => {
  const [testResults, setTestResults] = useState<ApiTestResult[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const addTestResult = (result: ApiTestResult) => {
    setTestResults(prev => [result, ...prev.slice(0, 9)]) // 保留最近10条记录
  }

  const testVideoCategories = async () => {
    const endpoint = '/video-categories'
    const expectedUrl = `${ENV_CONFIG.getApiBaseUrl()}${endpoint}`
    
    addTestResult({
      endpoint,
      url: expectedUrl,
      status: 'loading',
      timestamp: new Date().toLocaleTimeString()
    })

    try {
      const response = await projectApi.getVideoCategories()
      addTestResult({
        endpoint,
        url: expectedUrl,
        status: 'success',
        response: `获取到 ${response.categories?.length || 0} 个分类`,
        timestamp: new Date().toLocaleTimeString()
      })
    } catch (error: any) {
      addTestResult({
        endpoint,
        url: expectedUrl,
        status: 'error',
        error: error.message || '未知错误',
        timestamp: new Date().toLocaleTimeString()
      })
    }
  }

  const testProjects = async () => {
    const endpoint = '/projects'
    const expectedUrl = `${ENV_CONFIG.getApiBaseUrl()}${endpoint}`
    
    addTestResult({
      endpoint,
      url: expectedUrl,
      status: 'loading',
      timestamp: new Date().toLocaleTimeString()
    })

    try {
      const response = await projectApi.getProjects()
      addTestResult({
        endpoint,
        url: expectedUrl,
        status: 'success',
        response: `获取到 ${response?.length || 0} 个项目`,
        timestamp: new Date().toLocaleTimeString()
      })
    } catch (error: any) {
      addTestResult({
        endpoint,
        url: expectedUrl,
        status: 'error',
        error: error.message || '未知错误',
        timestamp: new Date().toLocaleTimeString()
      })
    }
  }

  const testAllEndpoints = async () => {
    setIsLoading(true)
    await testVideoCategories()
    await new Promise(resolve => setTimeout(resolve, 500)) // 稍作延迟
    await testProjects()
    setIsLoading(false)
  }

  const clearResults = () => {
    setTestResults([])
  }

  useEffect(() => {
    // 页面加载时显示当前配置
    console.log('=== API 配置信息 ===')
    console.log('当前API Base URL:', ENV_CONFIG.getApiBaseUrl())
    console.log('当前页面URL:', window.location.href)
    console.log('当前端口:', window.location.port)
  }, [])

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <Title level={2}>🧪 API 接口测试</Title>
      
      <Alert
        message="API 配置信息"
        description={
          <div>
            <Text strong>当前API地址: </Text>
            <Text code>{ENV_CONFIG.getApiBaseUrl()}</Text>
            <br />
            <Text strong>网络环境: </Text>
            <Text code>{ENV_CONFIG.getNetworkEnvironment().description}</Text>
            <br />
            <Text strong>页面地址: </Text>
            <Text code>{window.location.hostname}:{window.location.port || '默认'}</Text>
          </div>
        }
        type="info"
        style={{ marginBottom: '20px' }}
      />

      <Card title="API 端点测试" style={{ marginBottom: '20px' }}>
        <Space wrap>
          <Button 
            type="primary" 
            onClick={testVideoCategories}
            loading={isLoading}
          >
            测试视频分类接口
          </Button>
          <Button 
            type="primary" 
            onClick={testProjects}
            loading={isLoading}
          >
            测试项目接口
          </Button>
          <Button 
            onClick={testAllEndpoints}
            loading={isLoading}
          >
            测试所有接口
          </Button>
          <Button onClick={clearResults} disabled={testResults.length === 0}>
            清空结果
          </Button>
        </Space>
      </Card>

      {testResults.length > 0 && (
        <Card title="测试结果" style={{ marginBottom: '20px' }}>
          <List
            dataSource={testResults}
            renderItem={(item) => (
              <List.Item>
                <div style={{ width: '100%' }}>
                  <div style={{ 
                    display: 'flex', 
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px'
                  }}>
                    <Text strong>{item.endpoint}</Text>
                    <Text type="secondary">{item.timestamp}</Text>
                  </div>
                  
                  <div style={{ marginBottom: '4px' }}>
                    <Text type="secondary">URL: </Text>
                    <Text code style={{ fontSize: '12px' }}>{item.url}</Text>
                  </div>
                  
                  {item.status === 'loading' && (
                    <Alert message="请求中..." type="info" showIcon />
                  )}
                  
                  {item.status === 'success' && (
                    <Alert 
                      message="请求成功" 
                      description={item.response}
                      type="success" 
                      showIcon 
                    />
                  )}
                  
                  {item.status === 'error' && (
                    <Alert 
                      message="请求失败" 
                      description={item.error}
                      type="error" 
                      showIcon 
                    />
                  )}
                </div>
              </List.Item>
            )}
          />
        </Card>
      )}

      <Card title="💡 调试提示">
        <Text type="secondary">
          1. 检查浏览器开发者工具的Network标签，查看实际发出的请求URL
          <br />
          2. 如果仍然请求8000端口，请刷新页面重新加载代码
          <br />
          3. 确保Docker容器正在8063端口运行
          <br />
          4. 检查控制台输出的调试信息
        </Text>
      </Card>
    </div>
  )
}

export default ApiTestPage