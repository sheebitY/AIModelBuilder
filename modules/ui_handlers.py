"""UI 事件处理模块"""

import json
import traceback
import adsk.core

from .state_manager import state
from .prompts import SYSTEM_PROMPT
from .ai_client import call_ai_api
from .operations import execute_operations


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui

    def notify(self, args):
        try:
            cmd = args.command
            cmd.isExecutedWhenPreEmpted = False
            inputs = cmd.commandInputs

            inputs.addTextBoxCommandInput(
                "chatHistory",
                "对话历史",
                "欢迎使用 AI 建模助手！\n请描述你想要创建的模型。\n\n例如：创建一个台灯",
                15,
                True,
            )

            inputs.addTextBoxCommandInput("userInput", "输入", "", 3, False)

            onExecuteHandler = CommandExecuteHandler(self.ui)
            cmd.execute.add(onExecuteHandler)

        except:
            if self.ui:
                self.ui.messageBox(
                    "创建界面失败:\n{}".format(traceback.format_exc())
                )


class CommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui

    def notify(self, args):
        try:
            eventArgs = adsk.core.CommandEventArgs.cast(args)
            inputs = eventArgs.command.commandInputs

            userInput = inputs.itemById("userInput")
            chatHistory = inputs.itemById("chatHistory")

            user_text = userInput.text.strip()
            if not user_text:
                return

            current_history = chatHistory.text
            new_history = current_history + f"\n\n[用户]: {user_text}"

            # 检查是否要重置
            if user_text.lower() in ["重置", "reset", "清除", "clear"]:
                state.reset()
                chatHistory.text = "已重置建模状态。请描述你想要创建的模型。"
                userInput.text = ""
                return

            # 添加用户消息到历史
            state.add_user_message(user_text)

            # 获取AI消息
            try:
                messages = state.get_messages_for_ai(user_text, SYSTEM_PROMPT)
                ai_reply = call_ai_api(messages)
            except Exception as e:
                new_history += f"\n\n[错误]: AI调用失败 - {str(e)}"
                chatHistory.text = new_history
                return

            # 记录AI回复
            state.add_assistant_message(ai_reply)
            new_history += f"\n\n[AI]: {ai_reply}"

            # 解析并执行操作
            try:
                operations = json.loads(ai_reply)
                results = execute_operations(operations, self.ui)

                if results:
                    result_text = "\n  ".join(results)
                    new_history += f"\n\n[执行结果]:\n  {result_text}"

                scene = state.get_scene_summary()
                new_history += f"\n\n[场景]: {scene['total_entities']}个实体"

            except json.JSONDecodeError:
                pass  # AI没有返回JSON，可能是说明性回复
            except Exception as e:
                new_history += f"\n\n[执行错误]: {str(e)}"

            chatHistory.text = new_history
            userInput.text = ""

        except:
            if self.ui:
                self.ui.messageBox(
                    "执行失败:\n{}".format(traceback.format_exc())
                )
