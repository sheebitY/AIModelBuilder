"""UI 事件处理模块"""

import json
import os
import traceback
import threading
import time
from datetime import datetime
import adsk.core
import adsk.fusion

from modules.state_manager import state
from modules.prompts import SYSTEM_PROMPT
from modules.ai_client import call_ai_api
from modules.operations import execute_operations

# 全局变量存储面板引用
_palette = None
_handlers = []
_is_processing = False  # 标志位，防止重复处理

# 数据文件路径
_data_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'response.json')
_log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'debug.log')


def log(msg):
    """写入日志文件"""
    try:
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        with open(_log_file, 'a', encoding='utf-8') as f:
            f.write("[{}] {}\n".format(timestamp, msg))
    except:
        pass


class CommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self, ui):
        super().__init__()
        self.ui = ui

    def notify(self, args):
        try:
            show_chat_panel(self.ui)
        except:
            if self.ui:
                self.ui.messageBox(
                    "创建界面失败:\n{}".format(traceback.format_exc())
                )


def show_chat_panel(ui):
    """显示聊天面板"""
    global _palette

    try:
        # 清空日志文件和数据文件
        with open(_log_file, 'w', encoding='utf-8') as f:
            f.write("=== AI Model Builder 调试日志 ===\n")
        
        # 清空响应文件
        with open(_data_file, 'w', encoding='utf-8') as f:
            json.dump({"status": "ready"}, f, ensure_ascii=False)
        
        log("show_chat_panel 被调用")

        # 获取面板集合
        app = adsk.core.Application.get()
        palettes = ui.palettes

        # 检查面板是否已存在
        _palette = palettes.itemById('AIModelBuilderChat')
        if _palette:
            _palette.isVisible = True
            log("面板已存在，设为可见")
            return

        # 获取HTML文件路径
        addin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html_file = os.path.join(addin_dir, 'chat_panel.html')
        html_url = html_file.replace('\\', '/')

        log("HTML文件路径: {}".format(html_url))

        # 创建面板
        _palette = palettes.add(
            'AIModelBuilderChat',
            'AI 建模助手',
            html_url,
            True,
            True,
            True,
            400,
            500
        )

        # 设置面板位置
        _palette.dockingState = adsk.core.PaletteDockingStates.PaletteDockStateRight

        # 注册面板事件处理
        onPaletteHTMLHandler = PaletteHTMLHandler()
        _palette.incomingFromHTML.add(onPaletteHTMLHandler)
        _handlers.append(onPaletteHTMLHandler)

        onClosedHandler = PaletteClosedHandler()
        _palette.closed.add(onClosedHandler)
        _handlers.append(onClosedHandler)

        log("面板创建成功")

    except Exception as e:
        log("面板创建失败: {}".format(str(e)))
        log(traceback.format_exc())
        ui.messageBox("面板创建失败:\n{}".format(traceback.format_exc()))


class PaletteHTMLHandler(adsk.core.HTMLEventHandler):
    """处理来自HTML面板的消息"""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        try:
            action = args.action
            data = args.data

            log("PaletteHTMLHandler.notify 被调用")
            log("action: {}".format(action))

            # 处理 JavaScript 发来的消息
            if action == 'send_message':
                global _is_processing
                if _is_processing:
                    log("正在处理中，忽略重复请求")
                    return
                
                user_text = data.strip()
                if user_text:
                    _is_processing = True
                    log("启动处理线程，用户输入: {}".format(user_text[:50]))
                    thread = threading.Thread(target=process_user_input, args=(user_text,))
                    thread.daemon = True
                    thread.start()
            
            # 处理 JavaScript 的轮询请求
            elif action == 'poll':
                # 检查响应文件是否有新数据
                try:
                    if os.path.exists(_data_file):
                        with open(_data_file, 'r', encoding='utf-8') as f:
                            file_content = f.read().strip()
                            if file_content:
                                response_data = json.loads(file_content)
                                if response_data.get('status') != 'ready':
                                    log("响应文件有数据: {}".format(file_content[:100]))
                                    # 清空文件
                                    with open(_data_file, 'w', encoding='utf-8') as f:
                                        json.dump({"status": "ready"}, f, ensure_ascii=False)
                                    log("已清空响应文件")
                except Exception as e:
                    log("读取响应文件失败: {}".format(str(e)))

        except Exception as e:
            log("PaletteHTMLHandler 异常: {}".format(str(e)))
            log(traceback.format_exc())


class PaletteClosedHandler(adsk.core.UserInterfaceGeneralEventHandler):
    """面板关闭事件处理"""
    def __init__(self):
        super().__init__()

    def notify(self, args):
        global _palette
        _palette = None
        log("面板已关闭")


def send_to_panel(data):
    """发送数据到面板（通过文件）"""
    log("===== send_to_panel 被调用 =====")
    
    try:
        json_data = json.dumps(data, ensure_ascii=False)
        log("数据长度: {}".format(len(json_data)))
        
        # 将数据写入响应文件
        with open(_data_file, 'w', encoding='utf-8') as f:
            f.write(json_data)
        log("数据已写入响应文件")
        
        return True
    except Exception as e:
        log("send_to_panel 异常: {}".format(str(e)))
        log(traceback.format_exc())
        return False


def process_user_input(user_text):
    """处理用户输入（在单独线程中运行）"""
    global _is_processing
    log("===== process_user_input 开始 =====")
    log("用户输入: {}".format(user_text))

    try:
        # 检查是否要重置
        if user_text.lower() in ["重置", "reset", "清除", "clear"]:
            state.reset()
            send_to_panel({'reply': '已重置建模状态。请描述你想要创建的模型。'})
            log("已重置状态")
            _is_processing = False
            return

        # 添加用户消息到历史
        state.add_user_message(user_text)
        log("用户消息已添加到历史")

        # 获取AI消息
        log("准备调用AI API...")
        try:
            messages = state.get_messages_for_ai(user_text, SYSTEM_PROMPT)
            log("消息数组已构建，包含 {} 条消息".format(len(messages)))
            ai_reply = call_ai_api(messages)
            log("AI回复成功，长度: {} 字符".format(len(ai_reply)))
            log("AI回复前100字符: {}".format(ai_reply[:100]))
        except Exception as e:
            error_msg = 'AI调用失败 - {}'.format(str(e))
            log(error_msg)
            log(traceback.format_exc())
            send_to_panel({'error': error_msg})
            _is_processing = False
            return

        # 记录AI回复
        state.add_assistant_message(ai_reply)
        log("AI回复已添加到历史")

        # 解析并执行操作
        result_text = ""
        try:
            log("解析AI回复为JSON...")
            operations = json.loads(ai_reply)
            log("JSON解析成功，操作类型: {}".format(type(operations).__name__))
            
            log("执行操作...")
            results = execute_operations(operations, None)
            log("操作执行完成")

            if results:
                result_text = "\n  ".join(results)
                log("执行结果: {}".format(result_text[:200]))

        except json.JSONDecodeError as e:
            log("JSON解析失败: {}".format(str(e)))
            log("AI回复内容: {}".format(ai_reply[:500]))
            pass
        except Exception as e:
            error_msg = "执行错误: {}".format(str(e))
            log(error_msg)
            log(traceback.format_exc())
            result_text = error_msg

        # 发送结果到面板
        log("===== 准备发送结果到面板 =====")
        scene = state.get_scene_summary()
        response = {
            'reply': ai_reply,
            'result': result_text if result_text else None,
            'scene': scene['total_entities']
        }
        log("响应数据构建完成")
        
        log("调用 send_to_panel...")
        send_result = send_to_panel(response)
        log("send_to_panel 返回: {}".format(send_result))
        
        log("===== process_user_input 完成 =====")
        _is_processing = False

    except Exception as e:
        error_msg = "处理异常: {}".format(str(e))
        log(error_msg)
        log(traceback.format_exc())
        send_to_panel({'error': error_msg})
        _is_processing = False
