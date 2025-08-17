# AutoClip - 智能视频切片工具

🎬 基于AI的智能视频切片和合集推荐系统，支持从B站视频自动下载、字幕提取、智能切片和合集生成。

## 📋 版本更新记录

### v1.1.1 (2025-08-17)
- 🐳 **Docker一键部署**：支持Docker容器化部署，简化环境配置
- 🚀 **多阶段构建**：优化Docker镜像大小，提升构建效率
- 🔧 **生产环境支持**：提供生产环境Docker配置和部署脚本
- 📦 **数据持久化**：支持数据卷挂载，确保数据安全
- 🛡️ **健康检查**：集成容器健康检查，提升服务可靠性
- 📚 **部署文档**：完善Docker部署指南和快速开始文档

### v1.1.0 (2025-08-03)
- ✨ **新增硅基流动API支持**：支持使用硅基流动(SiliconFlow)作为AI服务提供商
- 🔧 **多API提供商支持**：支持通义千问和硅基流动两种AI服务
- 🎯 **智能API选择**：根据配置自动选择合适的AI服务提供商
- 📝 **配置优化**：新增API提供商配置选项，支持动态切换
- 🐛 **Bug修复**：修复API连接测试相关问题

### v1.0.0 (2025-07)
- 🎉 **首次发布**：完整的智能视频切片系统
- 🔥 **核心功能**：AI视频分析、智能切片、合集推荐
- 📺 **B站支持**：自动下载B站视频和字幕
- 🎨 **Web界面**：现代化React前端界面
- ⚡ **实时处理**：实时显示处理进度和状态

## ✨ 功能特性

- 🔥 **智能视频切片**：基于AI分析视频内容，自动生成高质量切片
- 📺 **B站视频下载**：支持B站视频自动下载和字幕提取
- 🎯 **智能合集推荐**：AI自动分析切片内容，推荐相关合集
- 🎨 **手动合集编辑**：支持拖拽排序、添加/删除切片
- 📦 **一键打包下载**：支持所有切片和合集的一键打包下载
- 🌐 **现代化Web界面**：React + TypeScript + Ant Design
- ⚡ **实时处理状态**：实时显示处理进度和日志

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- AI服务API密钥（支持通义千问或硅基流动）

### 安装步骤

1. **克隆项目**
```bash
git clone git@github.com:zhouxiaoka/autoclip_mvp.git
cd autoclip_mvp
```

2. **安装后端依赖**
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

3. **安装前端依赖**
```bash
cd frontend
npm install
cd ..
```

4. **配置API密钥**
```bash
# 复制示例配置文件
cp data/settings.example.json data/settings.json

# 编辑配置文件，填入你的API密钥
{
  "api_provider": "dashscope",  # 或 "siliconflow"
  "dashscope_api_key": "你的通义千问API密钥",
  "siliconflow_api_key": "你的硅基流动API密钥",
  "siliconflow_model": "Qwen/Qwen3-8B",  # 硅基流动模型名称
  "model_name": "qwen-plus",
  "chunk_size": 5000,
  "min_score_threshold": 0.7,
  "max_clips_per_collection": 5,
  "default_browser": "chrome"
}
```

### 启动服务

#### 方式一：使用启动脚本（推荐）
```bash
chmod +x start_dev.sh
./start_dev.sh
```

#### 方式二：手动启动
```bash
# 启动后端服务
source venv/bin/activate
python backend_server.py

# 新开终端，启动前端服务
cd frontend
npm run dev
```

#### 方式三：命令行工具
```bash
# 处理本地视频文件
python main.py --video input.mp4 --srt input.srt --project-name "我的项目"

# 处理现有项目
python main.py --project-id <project_id>

# 列出所有项目
python main.py --list-projects
```

### 访问地址

- 🌐 **前端界面**: http://localhost:3000
- 🔌 **后端API**: http://localhost:8000
- 📚 **API文档**: http://localhost:8000/docs

## 📁 项目结构

```
autoclip_mvp/
├── backend_server.py          # FastAPI后端服务
├── main.py                   # 命令行入口
├── start_dev.sh              # 开发环境启动脚本
├── requirements.txt           # Python依赖
├── .gitignore               # Git忽略文件
├── README.md                # 项目文档
│
├── frontend/                # React前端
│   ├── src/
│   │   ├── components/      # React组件
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API服务
│   │   ├── store/          # 状态管理
│   │   └── hooks/          # 自定义Hooks
│   ├── package.json        # 前端依赖
│   └── vite.config.ts      # Vite配置
│
├── src/                    # 核心业务逻辑
│   ├── main.py            # 主处理逻辑
│   ├── config.py          # 配置管理
│   ├── api.py             # API接口
│   ├── pipeline/          # 处理流水线
│   │   ├── step1_outline.py    # 大纲提取
│   │   ├── step2_timeline.py   # 时间轴生成
│   │   ├── step3_scoring.py    # 评分计算
│   │   ├── step4_title.py      # 标题生成
│   │   ├── step5_clustering.py # 聚类分析
│   │   └── step6_video.py      # 视频生成
│   ├── utils/             # 工具函数
│   │   ├── llm_client.py      # AI客户端
│   │   ├── video_processor.py # 视频处理
│   │   ├── text_processor.py  # 文本处理
│   │   ├── project_manager.py # 项目管理
│   │   ├── error_handler.py   # 错误处理
│   │   └── bilibili_downloader.py # B站下载
│   └── upload/            # 文件上传
│       └── upload_manager.py
│
├── data/                  # 数据文件
│   ├── projects.json     # 项目数据
│   └── settings.json     # 配置文件
│
├── uploads/              # 上传文件存储
│   ├── tmp/             # 临时下载文件
│   └── {project_id}/    # 项目文件
│       ├── input/       # 原始文件
│       └── output/      # 处理结果
│           ├── clips/   # 切片视频
│           └── collections/ # 合集视频
│
├── prompt/               # AI提示词模板
│   ├── business/        # 商业财经
│   ├── knowledge/       # 知识科普
│   ├── entertainment/   # 娱乐内容
│   └── ...
│
└── tests/               # 测试文件
    ├── test_config.py
    └── test_error_handler.py
```

## 🔧 配置说明

### API密钥配置
在 `data/settings.json` 中配置你的AI服务API密钥：

#### 通义千问配置
```json
{
  "api_provider": "dashscope",
  "dashscope_api_key": "your-dashscope-api-key",
  "model_name": "qwen-plus",
  "chunk_size": 5000,
  "min_score_threshold": 0.7,
  "max_clips_per_collection": 5,
  "default_browser": "chrome"
}
```

#### 硅基流动配置
```json
{
  "api_provider": "siliconflow",
  "siliconflow_api_key": "your-siliconflow-api-key",
  "siliconflow_model": "Qwen/Qwen3-8B",
  "chunk_size": 5000,
  "min_score_threshold": 0.7,
  "max_clips_per_collection": 5,
  "default_browser": "chrome"
}
```

### 浏览器配置
支持Chrome、Firefox、Safari等浏览器用于B站视频下载：
```json
{
  "default_browser": "chrome"
}
```

## 📖 使用指南

### 1. 上传本地视频
1. 访问 http://localhost:3000
2. 点击"上传视频"按钮
3. 选择视频文件和字幕文件（必须）
4. 填写项目名称和分类
5. 点击"开始处理"

### 2. 下载B站视频
1. 在首页点击"B站视频下载"
2. 输入B站视频链接（必须是有字幕的视频）
3. 选择浏览器（用于获取登录状态）
4. 点击"开始下载"

### 3. 编辑合集
1. 进入项目详情页面
2. 点击合集卡片进入编辑模式
3. 拖拽切片调整顺序
4. 添加或删除切片
5. 保存更改

### 4. 下载项目
1. 在项目卡片上点击下载按钮
2. 自动打包所有切片和合集
3. 下载完整的zip文件

## 🛠️ 开发指南

### 后端开发
```bash
# 启动开发服务器（支持热重载）
python backend_server.py

# 运行测试
pytest tests/
```

### 前端开发
```bash
cd frontend
npm run dev    # 开发模式
npm run build  # 生产构建
npm run lint   # 代码检查
```

### 添加新的视频分类
1. 在 `prompt/` 目录下创建新的分类文件夹
2. 添加对应的提示词模板文件
3. 在前端 `src/services/api.ts` 中添加分类选项

## 🐛 常见问题

### Q: 下载B站视频失败？
A: 确保已登录B站账号，并选择正确的浏览器。建议使用Chrome浏览器。

### Q: AI分析速度慢？
A: 可以调整 `chunk_size` 参数，较小的值会提高速度但可能影响质量。也可以尝试切换不同的API提供商（通义千问或硅基流动）来获得更好的性能。

### Q: 切片质量不高？
A: 调整 `min_score_threshold` 参数，较高的值会提高切片质量但减少数量。

### Q: 合集数量太少？
A: 调整 `max_clips_per_collection` 参数，增加每个合集的最大切片数量。

### Q: 如何切换AI服务提供商？
A: 在 `data/settings.json` 中修改 `api_provider` 字段，可选值：`"dashscope"`（通义千问）或 `"siliconflow"`（硅基流动）。确保对应的API密钥已正确配置。

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📞 联系方式

如有问题或建议，请通过以下方式联系：

### 💬 QQ  
<img src="./qq_qr.jpg" alt="QQ二维码" width="150">

### 📱 飞书  
<img src="./feishu_qr.jpg" alt="飞书二维码" width="150">

### 📧 其他联系方式
- 提交 [GitHub Issue](https://github.com/zhouxiaoka/autoclip_mvp/issues)
- 发送邮件至：christine_zhouye@163.com
- 添加上述QQ或飞书联系

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE)。

---

⭐ 如果这个项目对你有帮助，请给它一个星标！
