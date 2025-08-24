// 环境配置
export const ENV_CONFIG = {
  // 判断是否为生产环境
  isProduction: import.meta.env.PROD,
  
  // 判断是否为开发环境
  isDevelopment: import.meta.env.DEV,
  
  // API基础URL配置
  getApiBaseUrl(): string {
    // 获取当前页面信息
    const protocol = window.location.protocol
    const hostname = window.location.hostname
    const currentPort = window.location.port
    
    // 生产环境：非localhost/127.0.0.1，使用当前域名+/api
    if (hostname !== 'localhost' && hostname !== '127.0.0.1') {
      return `${protocol}//${window.location.host}/api`
    }
    
    // 开发环境：localhost/127.0.0.1
    // 根据env.example配置：
    // - FRONTEND_DEV_PORT=3000 (前端开发服务器)
    // - DEV_PORT=8063 (Docker开发环境对外端口)
    // - PORT=8000 (后端服务内部端口)
    
    if (currentPort === '3000') {
      // 前端开发服务器模式：直接访问后端服务的内部端口
      return 'http://localhost:8000/api'
    } else if (currentPort === '8063') {
      // Docker开发环境：前后端在同一端口
      return `${protocol}//${hostname}:${currentPort}/api`
    } else if (currentPort) {
      // 其他端口：使用当前端口（可能是自定义配置）
      return `${protocol}//${hostname}:${currentPort}/api`
    } else {
      // 无端口：默认80/443，尝试同域名
      return `${protocol}//${hostname}/api`
    }
  },
  
  // WebSocket URL配置
  getWebSocketUrl(): string {
    const apiUrl = this.getApiBaseUrl()
    return apiUrl.replace('http://', 'ws://').replace('https://', 'wss://').replace('/api', '/ws')
  },
  
  // 静态资源URL配置
  getStaticUrl(path: string): string {
    const baseUrl = this.getApiBaseUrl().replace('/api', '')
    return `${baseUrl}${path}`
  },
  
  // 调试配置
  debug: {
    enabled: import.meta.env.DEV,
    logApiRequests: true,
    logApiResponses: false
  },
  
  // 超时配置
  timeout: {
    api: 300000, // 5分钟
    upload: 600000, // 10分钟
    download: 1800000 // 30分钟
  },
  
  // 文件上传配置
  upload: {
    maxFileSize: 2048 * 1024 * 1024, // 2GB
    allowedVideoFormats: ['mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv'],
    allowedSubtitleFormats: ['srt', 'vtt', 'ass']
  }
}

// 调试工具
export const debugLog = (category: string, ...args: any[]) => {
  if (ENV_CONFIG.debug.enabled) {
    console.log(`[${category}]`, ...args)
  }
}

// 获取当前环境信息
export const getEnvironmentInfo = () => {
  return {
    environment: ENV_CONFIG.isProduction ? 'production' : 'development',
    apiBaseUrl: ENV_CONFIG.getApiBaseUrl(),
    currentUrl: window.location.href,
    hostname: window.location.hostname,
    port: window.location.port,
    protocol: window.location.protocol
  }
}

export default ENV_CONFIG