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
   API_URL = "API url"
   MODEL = "模型名称"
   ```
   
   **注意**：`config.py` 已被 `.gitignore` 排除，不会提交到版本库，保护你的API密钥安全。

4. **启动插件**
   - 打开Fusion 360
   - 进入 **工具** > **附加模块** > **脚本和附加模块**
   - 找到 "AIModelBuilder" 并点击运行

## 使用方法

### 基本流程

1. **启动插件**后，在工具栏会出现"AI 建模助手"面板
2. **点击按钮**打开聊天窗口
3. **分步输入指令**，每次只描述一个零件或一个操作
4. **等待AI响应**并确认执行结果
5. **继续下一步**操作，逐步构建完整模型

### 分步建模原则

**重要**：复杂模型需要分步构建，每次只让AI完成一个任务：

- 每次只创建一个组件或一个实体
- 先完成基础形状，再添加特征
- 按照从下到上、从大到小的顺序构建

### 示例：创建台灯

```
步骤1: 创建灯座
用户: 创建一个圆柱体作为灯座，直径150mm，高度15mm
AI: [创建组件"灯座"，创建圆柱体...]

步骤2: 创建灯杆
用户: 创建一个圆柱体作为灯杆，直径15mm，高度350mm，放在灯座上方
AI: [创建组件"灯杆"，创建圆柱体...]

步骤3: 创建灯罩
用户: 创建一个圆台作为灯罩，底面直径200mm，顶面直径80mm，高度120mm
AI: [创建组件"灯罩"，创建圆台...]

步骤4: 添加细节
用户: 给灯罩底部抽壳，厚度3mm
AI: [执行抽壳操作...]
```

### 示例：创建带孔的盒子

```
步骤1: 创建盒子主体
用户: 创建一个长方体，长100mm，宽60mm，高40mm
AI: [创建长方体...]

步骤2: 添加圆角
用户: 给所有边添加5mm圆角
AI: [执行圆角操作...]

步骤3: 打孔
用户: 在顶面中心打一个通孔，直径20mm
AI: [执行打孔操作...]
```

### 简单模型

对于简单形状，可以直接描述：

```
用户: 创建一个球体，直径50mm
用户: 创建一个圆柱体，直径30mm，高度100mm
用户: 在长方体上打一个10mm的通孔
```

### 修改已有模型

```
用户: 把刚才的灯座直径改成180mm
用户: 给灯杆添加10mm的圆角
用户: 在灯座上打4个螺丝孔，直径5mm
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

1. **分步建模**：复杂模型必须分步构建，每次只描述一个零件或操作
2. **坐标系**：使用绝对坐标系，Z轴向上，单位为毫米(mm)
3. **组件化**：每个独立零件建议创建单独的组件
4. **操作顺序**：先创建组件，再在组件内创建实体
5. **构建顺序**：建议从底座开始，自下而上逐步构建
6. **简单优先**：先创建基础形状，再添加圆角、打孔等特征

## 常见问题

**Q: 为什么AI没有响应？**
A: 检查config.py中的API密钥是否正确，网络连接是否正常。

**Q: 为什么输入"创建台灯"没有成功？**
A: 复杂模型需要分步构建。请按照"分步建模"的方式，每次只描述一个零件或操作，例如先说"创建一个圆柱体作为灯座"，再说"创建一个圆柱体作为灯杆"。

**Q: AI执行的操作位置不对怎么办？**
A: 可以明确指定位置，例如"创建一个圆柱体，直径50mm，高度100mm，位置在(0,0,0)"，或者"放在灯座上方"。

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
