import React, { useState, useEffect } from 'react'
import { Card, Button, Space, Typography, Alert, Table, Tag } from 'antd'
import ENV_CONFIG, { getEnvironmentInfo } from '../config/env'

const { Title, Text } = Typography

interface NetworkTestResult {
  scenario: string
  hostname: string
  port: string
  expectedApi: string
  actualApi: string
  isCorrect: boolean
  networkType: string
}

export const NetworkTestPage: React.FC = () => {
  const [currentEnv, setCurrentEnv] = useState(getEnvironmentInfo())
  const [testResults, setTestResults] = useState<NetworkTestResult[]>([])

  useEffect(() => {
    runAllNetworkTests()
  }, [])

  const runAllNetworkTests = () => {
    const testScenarios = [
      // 本地开发场景
      {
        scenario: '本地前端开发',
        hostname: 'localhost',
        port: '3000',
        expectedApi: 'http://localhost:8000/api'
      },
      {
        scenario: '本地Docker',
        hostname: 'localhost', 
        port: '8063',
        expectedApi: 'http://localhost:8063/api'
      },
      {
        scenario: '本地自定义端口',
        hostname: 'localhost',
        port: '9000',
        expectedApi: 'http://localhost:9000/api'
      },
      // 内网场景
      {
        scenario: '内网IP访问',
        hostname: '192.168.1.100',
        port: '8063',
        expectedApi: 'http://192.168.1.100:8063/api'
      },
      {
        scenario: '内网标准端口',
        hostname: '192.168.1.100',
        port: '',
        expectedApi: 'http://192.168.1.100/api'
      },
      // 外网场景
      {
        scenario: '外网域名',
        hostname: 'example.com',
        port: '8063',
        expectedApi: 'http://example.com:8063/api'
      },
      {
        scenario: '外网标准端口',
        hostname: 'example.com',
        port: '',
        expectedApi: 'http://example.com/api'
      },
      {
        scenario: 'HTTPS生产环境',
        hostname: 'app.example.com',
        port: '',
        expectedApi: 'https://app.example.com/api'
      }
    ]

    const results: NetworkTestResult[] = testScenarios.map(scenario => {
      // 模拟不同环境
      const mockWindow = {
        location: {
          protocol: scenario.hostname === 'app.example.com' ? 'https:' : 'http:',
          hostname: scenario.hostname,
          port: scenario.port,
          host: scenario.port ? `${scenario.hostname}:${scenario.port}` : scenario.hostname
        }
      }

      // 临时模拟window.location
      const originalLocation = window.location
      Object.defineProperty(window, 'location', {
        value: mockWindow.location,
        writable: true
      })

      try {
        const actualApi = ENV_CONFIG.getApiBaseUrl()
        const networkEnv = ENV_CONFIG.getNetworkEnvironment()
        
        const result: NetworkTestResult = {
          scenario: scenario.scenario,
          hostname: scenario.hostname,
          port: scenario.port || '默认',
          expectedApi: scenario.expectedApi,
          actualApi,
          isCorrect: actualApi === scenario.expectedApi,
          networkType: networkEnv.type
        }

        return result
      } finally {
        // 恢复原始window.location
        Object.defineProperty(window, 'location', {
          value: originalLocation,
          writable: true
        })
      }
    })

    setTestResults(results)
  }

  const columns = [
    {
      title: '测试场景',
      dataIndex: 'scenario',
      key: 'scenario',
      width: 120
    },
    {
      title: '主机名',
      dataIndex: 'hostname',
      key: 'hostname',
      width: 120,
      render: (hostname: string) => <Text code>{hostname}</Text>
    },
    {
      title: '端口',
      dataIndex: 'port',
      key: 'port',
      width: 80,
      render: (port: string) => <Text code>{port}</Text>
    },
    {
      title: '网络类型',
      dataIndex: 'networkType',
      key: 'networkType',
      width: 100,
      render: (type: string) => {
        const colorMap: Record<string, string> = {
          'local-dev': 'green',
          'local-docker': 'blue',
          'local-custom': 'cyan',
          'intranet': 'orange',
          'internet': 'purple'
        }
        return <Tag color={colorMap[type] || 'default'}>{type}</Tag>
      }
    },
    {
      title: '期望API',
      dataIndex: 'expectedApi',
      key: 'expectedApi',
      width: 200,
      render: (api: string) => <Text code style={{ fontSize: '12px' }}>{api}</Text>
    },
    {
      title: '实际API',
      dataIndex: 'actualApi',
      key: 'actualApi',
      width: 200,
      render: (api: string) => <Text code style={{ fontSize: '12px' }}>{api}</Text>
    },
    {
      title: '结果',
      dataIndex: 'isCorrect',
      key: 'isCorrect',
      width: 80,
      render: (isCorrect: boolean) => (
        <Tag color={isCorrect ? 'success' : 'error'}>
          {isCorrect ? '✅ 正确' : '❌ 错误'}
        </Tag>
      )
    }
  ]

  const successCount = testResults.filter(r => r.isCorrect).length
  const totalCount = testResults.length

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>🌐 网络环境适配测试</Title>
      
      <Alert
        message="当前网络环境"
        description={
          <div>
            <Text strong>环境类型: </Text>
            <Text code>{currentEnv.networkDescription}</Text>
            <br />
            <Text strong>网络类型: </Text>
            <Text code>{currentEnv.networkType}</Text>
            <br />
            <Text strong>当前API: </Text>
            <Text code>{currentEnv.apiBaseUrl}</Text>
            <br />
            <Text strong>是否内网IP: </Text>
            <Text code>{currentEnv.isPrivateIP ? '是' : '否'}</Text>
          </div>
        }
        type="info"
        style={{ marginBottom: '20px' }}
      />

      <Card 
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span>网络场景测试结果</span>
            <Space>
              <Tag color={successCount === totalCount ? 'success' : 'warning'}>
                {successCount}/{totalCount} 通过
              </Tag>
              <Button size="small" onClick={runAllNetworkTests}>
                重新测试
              </Button>
            </Space>
          </div>
        }
        style={{ marginBottom: '20px' }}
      >
        <Table
          dataSource={testResults}
          columns={columns}
          rowKey="scenario"
          pagination={false}
          size="small"
          scroll={{ x: 1000 }}
        />
      </Card>

      <Card title="📋 测试说明">
        <div style={{ fontSize: '14px' }}>
          <Text strong>测试内容：</Text>
          <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
            <li><strong>本地开发：</strong>前端开发服务器(3000端口)应该访问localhost:8000的后端</li>
            <li><strong>Docker环境：</strong>容器化环境中前后端使用相同端口</li>
            <li><strong>内网部署：</strong>内网IP地址应该使用相同的hostname和端口</li>
            <li><strong>外网部署：</strong>公网域名应该使用相同的hostname和端口</li>
            <li><strong>标准端口：</strong>80/443端口不需要显式指定端口号</li>
          </ul>
          
          <Text strong style={{ marginTop: '16px', display: 'block' }}>适配策略：</Text>
          <ul style={{ marginTop: '8px', paddingLeft: '20px' }}>
            <li>🏠 本地开发(localhost:3000) → API使用localhost:8000</li>
            <li>🐳 其他所有情况 → API使用当前页面的hostname和端口</li>
            <li>🌐 这样可以自动适配内网IP、外网域名、Docker等各种部署场景</li>
          </ul>
        </div>
      </Card>
    </div>
  )
}

export default NetworkTestPage