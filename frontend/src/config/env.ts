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
    
    // 判断是否为本地开发环境
    const isLocalDev = this.isLocalDevelopment(hostname, currentPort)
    
    if (isLocalDev) {
      // 本地开发环境处理
      return this.getLocalDevApiUrl(protocol, hostname, currentPort)
    } else {
      // 生产环境或内网/外网环境处理
      return this.getProductionApiUrl(protocol, hostname, currentPort)
    }
  },
  
  // 判断是否为本地开发环境
  isLocalDevelopment(hostname: string, currentPort: string): boolean {
    // 1. localhost或127.0.0.1且端口为3000（前端开发服务器）
    if ((hostname === 'localhost' || hostname === '127.0.0.1') && currentPort === '3000') {
      return true
    }
    // 2. 其他情况视为生产环境或容器化环境
    return false
  },
  
  // 获取本地开发环境API URL
  getLocalDevApiUrl(protocol: string, hostname: string, currentPort: string): string {
    // 前端开发服务器模式：动态使用当前端口构建 API 地址
    // 在 Docker 环境中，前后端使用相同的映射端口
    // 在本地开发中 (localhost:3000)，使用后端端口 8000
    if (currentPort === '3000') {
      // 纯本地开发环境：前端3000 -> 后端8000
      return `${protocol}//${hostname}:8000/api`
    } else {
      // Docker环境或其他环境：使用当前端口
      return `${protocol}//${hostname}:${currentPort}/api`
    }
  },
  
  // 获取生产环境API URL（包括内网、外网、Docker等）
  getProductionApiUrl(protocol: string, hostname: string, currentPort: string): string {
    // 策略：使用当前页面的hostname和配置的端口
    // 这样可以适配内网IP、外网IP、Docker容器等各种场景
    
    if (currentPort) {
      // 有端口：说明是非标准端口（非80/443）
      // 通常是Docker环境或自定义端口，前后端使用同一端口
      return `${protocol}//${hostname}:${currentPort}/api`
    } else {
      // 无端口：标准端口（80/443）
      // 通常是生产环境，前后端可能使用不同端口或通过代理
      return `${protocol}//${hostname}/api`
    }
  },
  
  // 获取网络环境类型（用于调试）
  getNetworkEnvironment(): { type: string; description: string } {
    const hostname = window.location.hostname
    const currentPort = window.location.port
    
    // 本地环境
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      if (currentPort === '3000') {
        return { type: 'local-dev', description: '本地开发环境（前端开发服务器）' }
      } else if (currentPort === '8063') {
        return { type: 'local-docker', description: '本地Docker环境' }
      } else if (currentPort) {
        return { type: 'local-custom', description: `本地自定义端口环境（${currentPort}）` }
      } else {
        return { type: 'local-standard', description: '本地标准端口环境' }
      }
    }
    
    // 内网环境
    if (this.isPrivateIP(hostname)) {
      return { 
        type: 'intranet', 
        description: `内网环境（${hostname}${currentPort ? ':' + currentPort : ''}）` 
      }
    }
    
    // 外网环境
    return { 
      type: 'internet', 
      description: `外网环境（${hostname}${currentPort ? ':' + currentPort : ''}）` 
    }
  },
  
  // 判断是否为内网IP
  isPrivateIP(hostname: string): boolean {
    // 检查是否为IP地址格式
    const ipRegex = /^(\d{1,3}\.){3}\d{1,3}$/
    if (!ipRegex.test(hostname)) {
      return false // 不是IP地址，可能是域名
    }
    
    // 内网IP范围
    const parts = hostname.split('.').map(num => parseInt(num, 10))
    
    // 10.0.0.0/8
    if (parts[0] === 10) return true
    
    // 172.16.0.0/12
    if (parts[0] === 172 && parts[1] >= 16 && parts[1] <= 31) return true
    
    // 192.168.0.0/16
    if (parts[0] === 192 && parts[1] === 168) return true
    
    return false
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
  const networkEnv = ENV_CONFIG.getNetworkEnvironment()
  return {
    environment: ENV_CONFIG.isProduction ? 'production' : 'development',
    networkType: networkEnv.type,
    networkDescription: networkEnv.description,
    apiBaseUrl: ENV_CONFIG.getApiBaseUrl(),
    currentUrl: window.location.href,
    hostname: window.location.hostname,
    port: window.location.port,
    protocol: window.location.protocol,
    isLocalDev: ENV_CONFIG.isLocalDevelopment(window.location.hostname, window.location.port),
    isPrivateIP: ENV_CONFIG.isPrivateIP(window.location.hostname)
  }
}

export default ENV_CONFIG