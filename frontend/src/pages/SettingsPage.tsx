import React, { useState, useEffect } from 'react'
import { Layout, Card, Form, Input, Button, message, Typography, Space, Alert, Divider } from 'antd'
import { KeyOutlined, SaveOutlined, ApiOutlined } from '@ant-design/icons'
import { settingsApi } from '../services/api'

const { Content } = Layout
const { Title, Text } = Typography
const { TextArea } = Input

interface ApiSettings {
  dashscope_api_key: string
  model_name: string
  chunk_size: number
  min_score_threshold: number
  max_clips_per_collection: number
}

const SettingsPage: React.FC = () => {
  const [form] = Form.useForm()
  const [loading, setLoading] = useState(false)
  const [testLoading, setTestLoading] = useState(false)
  const [settings, setSettings] = useState<ApiSettings | null>(null)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const data = await settingsApi.getSettings()
      setSettings(data)
      form.setFieldsValue(data)
    } catch (error) {
      message.error('加载配置失败')
      console.error('Load settings error:', error)
    }
  }

  const handleSave = async (values: ApiSettings) => {
    setLoading(true)
    try {
      await settingsApi.updateSettings(values)
      setSettings(values)
      message.success('配置保存成功')
    } catch (error) {
      message.error('保存配置失败')
      console.error('Save settings error:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleTestConnection = async () => {
    setTestLoading(true)
    try {
      const values = form.getFieldsValue()
      const result = await settingsApi.testApiKey(values.dashscope_api_key)
      if (result.success) {
        message.success('API密钥测试成功')
      } else {
        message.error(`API密钥测试失败: ${result.error}`)
      }
    } catch (error) {
      message.error('测试连接失败')
      console.error('Test connection error:', error)
    } finally {
      setTestLoading(false)
    }
  }

  return (
    <Content style={{ padding: '24px', maxWidth: '800px', margin: '0 auto' }}>
      <Title level={2}>
        <KeyOutlined /> 系统配置
      </Title>
      
      <Card title="API 配置" style={{ marginBottom: '24px' }}>
        <Alert
          message="配置说明"
          description="请配置通义千问API密钥以启用AI自动切片功能。您可以在阿里云控制台获取API密钥。"
          type="info"
          showIcon
          style={{ marginBottom: '24px' }}
        />
        
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{
            model_name: 'qwen-plus',
            chunk_size: 5000,
            min_score_threshold: 0.7,
            max_clips_per_collection: 5
          }}
        >
          <Form.Item
            label="DashScope API Key"
            name="dashscope_api_key"
            rules={[
              { required: true, message: '请输入API密钥' },
              { min: 10, message: 'API密钥长度不能少于10位' }
            ]}
          >
            <Input.Password
              placeholder="请输入通义千问API密钥"
              prefix={<KeyOutlined />}
            />
          </Form.Item>

          <Space>
            <Button
              type="default"
              icon={<ApiOutlined />}
              onClick={handleTestConnection}
              loading={testLoading}
            >
              测试连接
            </Button>
          </Space>

          <Divider />

          <Title level={4}>模型配置</Title>
          
          <Form.Item
            label="模型名称"
            name="model_name"
            rules={[{ required: true, message: '请选择模型' }]}
          >
            <Input placeholder="qwen-plus" />
          </Form.Item>

          <Form.Item
            label="文本分块大小"
            name="chunk_size"
            rules={[{ required: true, message: '请输入分块大小' }]}
          >
            <Input type="number" placeholder="5000" addonAfter="字符" />
          </Form.Item>

          <Form.Item
            label="最低评分阈值"
            name="min_score_threshold"
            rules={[{ required: true, message: '请输入评分阈值' }]}
          >
            <Input type="number" step="0.1" min="0" max="1" placeholder="0.7" />
          </Form.Item>

          <Form.Item
            label="每个合集最大切片数"
            name="max_clips_per_collection"
            rules={[{ required: true, message: '请输入最大切片数' }]}
          >
            <Input type="number" placeholder="5" addonAfter="个" />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              icon={<SaveOutlined />}
              loading={loading}
              size="large"
            >
              保存配置
            </Button>
          </Form.Item>
        </Form>
      </Card>

      <Card title="使用说明">
        <Space direction="vertical" size="middle" style={{ width: '100%' }}>
          <div>
            <Text strong>1. 获取API密钥</Text>
            <br />
            <Text type="secondary">
              访问阿里云控制台 → 人工智能 → 通义千问 → API密钥管理，创建新的API密钥
            </Text>
          </div>
          
          <div>
            <Text strong>2. 配置参数说明</Text>
            <br />
            <Text type="secondary">
              • 文本分块大小：影响处理速度和精度，建议5000字符<br />
              • 评分阈值：只有高于此分数的片段才会被保留<br />
              • 合集切片数：控制每个主题合集包含的片段数量
            </Text>
          </div>
          
          <div>
            <Text strong>3. 测试连接</Text>
            <br />
            <Text type="secondary">
              保存前建议先测试API密钥是否有效，确保服务正常运行
            </Text>
          </div>
        </Space>
      </Card>
    </Content>
  )
}

export default SettingsPage