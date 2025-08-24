import React from 'react'
import { Card, Typography, Space, Button, Divider } from 'antd'
import { getEnvironmentInfo, ENV_CONFIG } from '../config/env'

const { Text, Paragraph } = Typography

export const DebugInfo: React.FC = () => {
  const [envInfo, setEnvInfo] = React.useState(getEnvironmentInfo())
  
  const refreshInfo = () => {
    setEnvInfo(getEnvironmentInfo())
  }
  
  const testApiConnection = async () => {
    try {
      console.log('=== API连接测试 ===')
      const apiUrl = ENV_CONFIG.getApiBaseUrl()
      console.log('测试URL:', `${apiUrl}/health`)
      
      const response = await fetch(`${apiUrl}/health`)
      const result = {
        url: `${apiUrl}/health`,
        status: response.status,
        ok: response.ok,
        statusText: response.statusText
      }
      
      console.log('API连接测试结果:', result)
      
      if (response.ok) {
        const data = await response.text()
        console.log('响应内容:', data)
      }
    } catch (error) {
      console.error('API连接测试失败:', error)
    }
  }
  
  // 分析当前环境
  const analyzeEnvironment = () => {
    const port = envInfo.port
    let environmentType = '未知'
    let expectedApiUrl = ''
    
    if (envInfo.hostname !== 'localhost' && envInfo.hostname !== '127.0.0.1') {
      environmentType = '生产环境'
      expectedApiUrl = `${envInfo.protocol}//${envInfo.hostname}/api`
    } else if (port === '3000') {
      environmentType = '前端开发环境'
      expectedApiUrl = 'http://localhost:8000/api'
    } else if (port === '8063') {
      environmentType = 'Docker开发环境'
      expectedApiUrl = `${envInfo.protocol}//${envInfo.hostname}:8063/api`
    } else if (port) {
      environmentType = '自定义端口环境'
      expectedApiUrl = `${envInfo.protocol}//${envInfo.hostname}:${port}/api`
    } else {
      environmentType = '默认端口环境'
      expectedApiUrl = `${envInfo.protocol}//${envInfo.hostname}/api`
    }
    
    return { environmentType, expectedApiUrl }
  }
  
  const { environmentType, expectedApiUrl } = analyzeEnvironment()
  const isApiUrlCorrect = envInfo.apiBaseUrl === expectedApiUrl
  
  return (
    <Card 
      title="🛠️ 环境调试信息" 
      style={{ margin: '16px 0' }} 
      size="small"
      extra={
        <Space>
          <Button size="small" onClick={refreshInfo}>
            🔄 刷新
          </Button>
          <Button size="small" type="primary" onClick={testApiConnection}>
            🔍 测试API
          </Button>
        </Space>
      }
    >
      <Space direction="vertical" style={{ width: '100%' }}>
        {/* 基本环境信息 */}
        <div>
          <Text strong>🌍 环境类型: </Text>
          <Text code style={{ color: environmentType.includes('Docker') ? '#52c41a' : '#1890ff' }}>
            {environmentType}
          </Text>
        </div>
        
        <Divider style={{ margin: '8px 0' }} />
        
        {/* URL信息 */}
        <div>
          <Text strong>🔗 当前URL: </Text>
          <Text code>{envInfo.currentUrl}</Text>
        </div>
        
        <div>
          <Text strong>🏠 主机名: </Text>
          <Text code>{envInfo.hostname}</Text>
        </div>
        
        <div>
          <Text strong>🔌 端口: </Text>
          <Text code>{envInfo.port || '无（默认80/443）'}</Text>
        </div>
        
        <div>
          <Text strong>🔒 协议: </Text>
          <Text code>{envInfo.protocol}</Text>
        </div>
        
        <Divider style={{ margin: '8px 0' }} />
        
        {/* API配置信息 */}
        <div>
          <Text strong>📡 当前API地址: </Text>
          <Text code style={{ color: isApiUrlCorrect ? '#52c41a' : '#ff4d4f' }}>
            {envInfo.apiBaseUrl}
          </Text>
        </div>
        
        <div>
          <Text strong>✅ 预期API地址: </Text>
          <Text code>{expectedApiUrl}</Text>
        </div>
        
        {!isApiUrlCorrect && (
          <div style={{ 
            padding: '8px', 
            background: '#fff2f0', 
            border: '1px solid #ffccc7',
            borderRadius: '4px'
          }}>
            <Text type="danger">
              ⚠️ API地址不匹配！当前使用的API地址与预期不符。
            </Text>
          </div>
        )}
        
        {isApiUrlCorrect && (
          <div style={{ 
            padding: '8px', 
            background: '#f6ffed', 
            border: '1px solid #b7eb8f',
            borderRadius: '4px'
          }}>
            <Text type="success">
              ✅ API地址配置正确！
            </Text>
          </div>
        )}
        
        <Divider style={{ margin: '8px 0' }} />
        
        {/* 配置说明 */}
        <div style={{ fontSize: '12px', color: '#666' }}>
          <Text strong>📝 环境配置说明:</Text>
          <ul style={{ margin: '4px 0', paddingLeft: '16px' }}>
            <li>端口3000: 前端开发服务器 → API: localhost:8000</li>
            <li>端叠8063: Docker开发环境 → API: localhost:8063</li>
            <li>其他端口: 自定义配置 → API: 当前端口</li>
            <li>非本地: 生产环境 → API: 当前域名/api</li>
          </ul>
        </div>
      </Space>
    </Card>
  )
}

export default DebugInfo