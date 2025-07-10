# GitHub 配置目录

此目录用于存放GitHub相关的配置文件。

## 🖼️ 项目头图 (Repository Banner)

### 文件要求
- **文件名**：`banner.png` 或 `banner.jpg`
- **位置**：`.github/banner.png`
- **尺寸**：1280x320 像素 (4:1 宽高比)
- **格式**：PNG、JPG 或 GIF
- **大小**：最大 1MB

### 设计建议
- **分辨率**：建议使用 2x 分辨率 (2560x640) 以获得更好的显示效果
- **安全区域**：重要内容放在中间区域，避免被裁剪
- **主题兼容**：考虑与GitHub深色/浅色主题的兼容性
- **文字清晰**：确保文字在缩小时仍然清晰可读

### 上传步骤
1. 将头图文件命名为 `banner.png` 或 `banner.jpg`
2. 将文件放在 `.github/` 目录下
3. 提交到Git：
   ```bash
   git add .github/banner.png
   git commit -m "Add repository banner"
   git push origin main
   ```

### 显示效果
- 头图会显示在GitHub仓库页面的顶部
- 在仓库列表和搜索结果中也会显示
- 支持深色和浅色主题自动适配

## 📁 目录结构
```
.github/
├── README.md          # 本说明文件
└── banner.png         # 项目头图（需要上传）
``` 