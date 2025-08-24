import React from 'react'
import { Card, Typography, Space, Button, Divider } from 'antd'
import { getEnvironmentInfo, ENV_CONFIG } from '../config/env'

const { Text } = Typography

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
      
      // 测试多个API端点
      const testEndpoints = [
        '/health',
        '/video-categories', 
        '/projects'
      ]
      
      for (const endpoint of testEndpoints) {
        const testUrl = `${apiUrl}${endpoint}`
        console.log(`测试端点: ${testUrl}`)
        
        try {
          const response = await fetch(testUrl)
          console.log(`${endpoint}: ${response.status} ${response.statusText}`)
        } catch (error) {
          console.error(`${endpoint} 失败:`, error)
        }
      }
      
    } catch (error) {
      console.error('API连接测试失败:', error)
    }
  }
  
  // 分析当前环境
  const analyzeEnvironment = () => {
    const port = envInfo.port
    const networkType = envInfo.networkType
    const isLocalDev = envInfo.isLocalDev
    
    let environmentType = envInfo.networkDescription
    let expectedApiUrl = ''
    
    if (isLocalDev) {
      // 本地开发环境
      expectedApiUrl = 'http://localhost:8000/api'
    } else {
      // 生产环境或容器化环境
      if (port) {
        expectedApiUrl = `${envInfo.protocol}//${envInfo.hostname}:${port}/api`
      } else {
        expectedApiUrl = `${envInfo.protocol}//${envInfo.hostname}/api`
      }
    }
    
    return { environmentType, expectedApiUrl, networkType }
  }
  
  const { environmentType, expectedApiUrl, networkType } = analyzeEnvironment()
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
          <Text code style={{ color: networkType === 'local-dev' ? '#52c41a' : networkType.includes('local') ? '#1890ff' : '#722ed1' }}>
            {environmentType}
          </Text>
        </div>
        
        <div>
          <Text strong>📶 网络类型: </Text>
          <Text code>{networkType}</Text>
        </div>
        
        {envInfo.isPrivateIP && (
          <div>
            <Text strong>🏠 IP类型: </Text>
            <Text code style={{ color: '#fa8c16' }}>内网IP</Text>
          </div>
        )}
        
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
            <li><strong>本地开发:</strong> localhost:3000 → API: localhost:8000</li>
            <li><strong>Docker本地:</strong> localhost:8063 → API: localhost:8063</li>
            <li><strong>内网部署:</strong> 192.168.x.x:8063 → API: 192.168.x.x:8063</li>
            <li><strong>外网部署:</strong> domain.com:8063 → API: domain.com:8063</li>
            <li><strong>标准端口:</strong> domain.com → API: domain.com/api</li>
            <li><strong>自定义端口:</strong> 使用当前页面的hostname和端口</li>
          </ul>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            系统会根据当前访问的hostname和端口自动适配各种网络环境
          </Text>
        </div>
      </Space>
    </Card>
  )
}

export default DebugInfo