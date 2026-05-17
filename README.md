# AI Model Builder - Fusion 360 AI 建模助手

一个基于AI的Autodesk Fusion 360插件，允许用户通过自然语言描述创建3D模型。只需输入"创建一个台灯"，AI就会自动生成相应的3D模型。

## 功能特性

### 核心功能
- **自然语言建模**：用中文描述你想要的模型，AI自动生成
- **聊天式界面**：在Fusion 360内直接与AI对话
- **多组件支持**：可创建复杂的装配体（如台灯、椅子、机器人等）
- **实时反馈**：显示建模进度和执行结果

### 支持的建模操作

#### 基础实体创建
| 形状 | 参数 |
|------|------|
| 长方体 (box) | length, width, height |
| 圆柱体 (cylinder) | diameter, height |
| 球体 (sphere) | diameter |
| 圆锥/圆台 (cone) | bottom_diameter, top_diameter, height |
| 圆环体 (torus) | major_diameter, minor_diameter |

#### 特征操作
- **打孔** (hole) - 指定直径、深度、偏移
- **通孔** (hole_through) - 贯穿打孔
- **圆角** (fillet) - 支持全部/顶部/底部/垂直边
- **倒角** (chamfer) - 等距倒角
- **抽壳** (shell) - 指定厚度和移除面
- **拔模** (draft) - 指定拔模角度
- **口袋槽** (pocket) - 圆形或矩形
- **槽** (slot) - 标准槽特征

#### 阵列与镜像
- **线性阵列** - 指定方向、数量、间距
- **圆形阵列** - 指定数量、角度、轴
- **镜像** - 支持XY/YZ/XZ平面

#### 变换操作
- **移动** (move) - 绝对坐标定位
- **旋转** (rotate) - 指定轴和角度

#### 布尔运算
- **合并** (join) - 合并实体
- **切割** (cut) - 从目标实体切割工具体
- **相交** (intersect) - 获取交集

## 安装方法

### 前置要求
- Autodesk Fusion 360
- Python 3.x（Fusion 360自带）
- 有效的AI API密钥

### 安装步骤

1. **下载插件**
   ```bash
   git clone https://github.com/yourusername/AIModelBuilder.git
   ```

2. **复制到Fusion 360 AddIns目录**
   - Windows: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`
   - macOS: `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/`

3. **配置API密钥**
   
   复制配置模板并填入你的API密钥：
   ```bash
   cp modules/config.example.py modules/config.py
   ```
   
   编辑 `modules/config.py` 文件：
   ```python
   API_KEY = "你的API密钥"
   API_URL = "https://api.xiaomimimo.com/v1/chat/completions"
   MODEL = "mimo-v2.5"
   ```
   
   **注意**：`config.py` 已被 `.gitignore` 排除，不会提交到版本库，保护你的API密钥安全。

4. **启动插件**
   - 打开Fusion 360
   - 进入 **工具** > **附加模块** > **脚本和附加模块**
   - 找到 "AIModelBuilder" 并点击运行

## 使用方法

1. **启动插件**后，在工具栏会出现"AI 建模助手"面板
2. **点击按钮**打开聊天窗口
3. **输入描述**，例如：
   - "创建一个台灯"
   - "做一个带孔的长方体"
   - "创建一个齿轮"
4. **等待AI响应**并自动执行建模操作
5. **继续对话**进行修改或添加更多特征

### 示例对话

```
用户：创建一个台灯
AI：[执行操作：创建灯座组件、创建圆柱体底座、创建灯杆组件...]
执行结果：创建组件: comp_1 (灯座)、创建实体: 灯座底座...

用户：灯罩太大了，改成直径150
AI：[执行操作：修改灯罩尺寸...]
```

### 特殊命令
- `重置` / `reset` - 清除所有建模状态，重新开始

## 项目结构

```
AIModelBuilder/
├── AIModelBuilder.py          # 插件入口文件
├── AIModelBuilder.manifest    # 插件配置文件
├── chat_panel.html            # 聊天面板界面
├── modules/
│   ├── __init__.py
│   ├── ai_client.py           # AI API调用模块
│   ├── config.py              # 配置文件（API密钥等）
│   ├── operations.py          # 建模操作执行模块
│   ├── prompts.py             # AI提示词模块
│   ├── state_manager.py       # 状态管理模块
│   └── ui_handlers.py         # UI事件处理模块
└── README.md
```

## 技术架构

- **前端**：HTML/CSS/JavaScript 聊天面板
- **后端**：Python (Fusion 360 API)
- **通信**：JSON文件轮询机制
- **AI模型**：支持OpenAI兼容API（默认使用小米MiMo模型）

## 配置说明

### config.py 配置项

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| API_KEY | AI服务的API密钥 | - |
| API_URL | AI服务的API地址 | https://api.xiaomimimo.com/v1/chat/completions |
| MODEL | 使用的AI模型名称 | mimo-v2.5 |

### 支持的AI服务

本插件支持所有兼容OpenAI API格式的服务，包括：
- OpenAI GPT系列
- 小米MiMo模型
- 其他兼容API的服务

## 注意事项

1. **坐标系**：使用绝对坐标系，Z轴向上，单位为毫米(mm)
2. **组件化**：每个独立零件建议创建单独的组件
3. **操作顺序**：先创建组件，再在组件内创建实体
4. **复杂模型**：复杂形状需要分多次操作完成

## 常见问题

**Q: 为什么AI没有响应？**
A: 检查config.py中的API密钥是否正确，网络连接是否正常。

**Q: 如何修改AI模型？**
A: 编辑config.py中的MODEL和API_URL配置。

**Q: 支持哪些语言？**
A: 目前主要支持中文，AI也能理解英文描述。

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 致谢

- Autodesk Fusion 360 API
- 小米MiMo AI模型
