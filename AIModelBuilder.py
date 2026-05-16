"""AI Model Builder - Fusion 360 AI 建模助手

入口文件，负责初始化和注册插件。
具体实现在 modules 目录下的各个模块中。
"""

# ===== 强制清空模块缓存 =====
import sys
import os
import shutil

# 获取当前插件目录
_addin_dir = os.path.dirname(os.path.abspath(__file__))

# 删除 __pycache__ 目录
_pycache_dir = os.path.join(_addin_dir, '__pycache__')
if os.path.exists(_pycache_dir):
    try:
        shutil.rmtree(_pycache_dir)
        print("[AI Model Builder] 已删除 __pycache__ 目录")
    except Exception as e:
        print("[AI Model Builder] 删除 __pycache__ 失败: {}".format(str(e)))

# 删除 modules 目录下的 __pycache__
_modules_pycache_dir = os.path.join(_addin_dir, 'modules', '__pycache__')
if os.path.exists(_modules_pycache_dir):
    try:
        shutil.rmtree(_modules_pycache_dir)
        print("[AI Model Builder] 已删除 modules/__pycache__ 目录")
    except Exception as e:
        print("[AI Model Builder] 删除 modules/__pycache__ 失败: {}".format(str(e)))

# 从 sys.modules 中删除所有已加载的本插件模块
_modules_to_remove = []
for module_name in list(sys.modules.keys()):
    if module_name.startswith('modules') or module_name == 'AIModelBuilder':
        _modules_to_remove.append(module_name)

for module_name in _modules_to_remove:
    del sys.modules[module_name]
    print("[AI Model Builder] 已卸载模块: {}".format(module_name))

# 确保插件目录在路径中（放在最前面）
if _addin_dir in sys.path:
    sys.path.remove(_addin_dir)
sys.path.insert(0, _addin_dir)

print("[AI Model Builder] 缓存清理完成")

# ===== 正常导入 =====
import adsk.core
import traceback

_app = None
_ui = None
_handlers = []


def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

        print("[AI Model Builder] 插件启动中...")

        # 尝试导入模块
        try:
            from modules.ui_handlers import CommandCreatedHandler
            print("[AI Model Builder] 模块导入成功")
        except ImportError as e:
            error_msg = "模块导入失败，请检查 modules 目录是否存在所有文件。\n\n错误详情: {}".format(str(e))
            print("[AI Model Builder] {}".format(error_msg))
            _ui.messageBox(error_msg)
            return

        # 注册命令
        cmdDef = _ui.commandDefinitions.addButtonDefinition(
            "AIModelBuilderCmdId",
            "AI 建模助手",
            "用自然语言创建3D模型（聊天式）",
        )

        handler = CommandCreatedHandler(_ui)
        cmdDef.commandCreated.add(handler)
        _handlers.append(handler)

        # 创建面板
        workspaces = _ui.workspaces
        modelingWorkspace = workspaces.itemById("FusionSolidEnvironment")
        toolbarPanels = modelingWorkspace.toolbarPanels
        panel = toolbarPanels.add(
            "AIModelBuilderPanelId", "AI 建模助手", "ToolsPanel", False
        )
        panel.controls.addCommand(cmdDef)

        print("[AI Model Builder] 插件启动成功")

    except:
        error_msg = "加载失败:\n{}".format(traceback.format_exc())
        print("[AI Model Builder] {}".format(error_msg))
        if _ui:
            _ui.messageBox(error_msg)


def stop(context):
    try:
        print("[AI Model Builder] 插件停止中...")
        
        workspaces = _app.userInterface.workspaces
        modelingWorkspace = workspaces.itemById("FusionSolidEnvironment")
        toolbarPanels = modelingWorkspace.toolbarPanels
        panel = toolbarPanels.itemById("AIModelBuilderPanelId")
        if panel:
            panel.deleteMe()
        cmdDef = _app.userInterface.commandDefinitions.itemById("AIModelBuilderCmdId")
        if cmdDef:
            cmdDef.deleteMe()
        
        print("[AI Model Builder] 插件已停止")
    except:
        pass
