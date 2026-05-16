"""AI Model Builder - Fusion 360 AI 建模助手

入口文件，负责初始化和注册插件。
具体实现在 modules 目录下的各个模块中。
"""

import adsk.core
import traceback

from modules.ui_handlers import CommandCreatedHandler

_app = None
_ui = None
_handlers = []


def run(context):
    try:
        global _app, _ui
        _app = adsk.core.Application.get()
        _ui = _app.userInterface

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
        workspaces = _app.userInterface.workspaces
        modelingWorkspace = workspaces.itemById("FusionSolidEnvironment")
        toolbarPanels = modelingWorkspace.toolbarPanels
        panel = toolbarPanels.add(
            "AIModelBuilderPanelId", "AI 建模助手", "ToolsPanel", False
        )
        panel.controls.addCommand(cmdDef)

    except:
        if _ui:
            _ui.messageBox("加载失败:\n{}".format(traceback.format_exc()))


def stop(context):
    try:
        workspaces = _app.userInterface.workspaces
        modelingWorkspace = workspaces.itemById("FusionSolidEnvironment")
        toolbarPanels = modelingWorkspace.toolbarPanels
        panel = toolbarPanels.itemById("AIModelBuilderPanelId")
        if panel:
            panel.deleteMe()
        cmdDef = _app.userInterface.commandDefinitions.itemById("AIModelBuilderCmdId")
        if cmdDef:
            cmdDef.deleteMe()
    except:
        pass
