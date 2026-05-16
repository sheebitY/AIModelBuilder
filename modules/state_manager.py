"""状态管理模块 - 管理建模过程中的组件、实体和对话历史"""


class ModelState:
    """管理整个建模状态"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.entities = {}  # id -> BRepBody 映射
        self.components = {}  # id -> Component 映射
        self.current_component = None  # 当前活动组件
        self.entity_counter = 0
        self.component_counter = 0
        self.history = []  # 操作历史记录
        self.message_history = []  # AI对话历史

    def generate_entity_id(self, prefix="body"):
        """生成唯一实体ID"""
        self.entity_counter += 1
        return f"{prefix}_{self.entity_counter}"

    def generate_component_id(self, prefix="comp"):
        """生成唯一组件ID"""
        self.component_counter += 1
        return f"{prefix}_{self.component_counter}"

    def register_entity(self, body, entity_id=None, component_id=None):
        """注册新实体"""
        if entity_id is None:
            entity_id = self.generate_entity_id()
        self.entities[entity_id] = {
            "body": body,
            "component_id": component_id
            or (self.current_component["id"] if self.current_component else "root"),
            "z_offset": 0,
        }
        return entity_id

    def register_component(self, component, name=None):
        """注册新组件"""
        comp_id = self.generate_component_id()
        if name is None:
            name = f"Component_{comp_id}"
        comp_info = {"id": comp_id, "name": name, "component": component}
        self.components[comp_id] = comp_info
        return comp_id

    def get_entity(self, entity_id):
        """获取实体"""
        if entity_id in self.entities:
            return self.entities[entity_id]["body"]
        return None

    def get_component(self, component_id):
        """获取组件"""
        if component_id in self.components:
            return self.components[component_id]["component"]
        return None

    def get_entity_info(self):
        """获取所有实体信息，用于AI上下文"""
        info = []
        for eid, edata in self.entities.items():
            body = edata["body"]
            if body.isValid:
                bbox = body.boundingBox
                info.append(
                    {
                        "id": eid,
                        "component": edata["component_id"],
                        "z_min": round(bbox.minPoint.z * 10, 2),
                        "z_max": round(bbox.maxPoint.z * 10, 2),
                        "width": round(
                            (bbox.maxPoint.x - bbox.minPoint.x) * 10, 2
                        ),
                        "depth": round(
                            (bbox.maxPoint.y - bbox.minPoint.y) * 10, 2
                        ),
                        "height": round(
                            (bbox.maxPoint.z - bbox.minPoint.z) * 10, 2
                        ),
                    }
                )
        return info

    def get_scene_summary(self):
        """获取场景摘要，用于AI上下文"""
        summary = {
            "components": list(self.components.keys()),
            "current_component": (
                self.current_component["id"] if self.current_component else "root"
            ),
            "entities": self.get_entity_info(),
            "total_entities": len(
                [e for e in self.entities.values() if e["body"].isValid]
            ),
        }
        return summary

    def add_to_history(self, operation, result):
        """记录操作历史"""
        self.history.append(
            {
                "operation": operation,
                "result": result,
                "entity_count": len(
                    [e for e in self.entities.values() if e["body"].isValid]
                ),
            }
        )

    def get_messages_for_ai(self, user_input, system_prompt):
        """构建发送给AI的消息数组"""
        from .prompts import describe_scene

        system_msg = {"role": "system", "content": system_prompt}
        scene_desc = describe_scene(self)
        scene_msg = {"role": "system", "content": f"【当前场景状态】\n{scene_desc}"}

        messages = [system_msg, scene_msg] + self.message_history
        messages.append({"role": "user", "content": user_input})
        return messages

    def add_user_message(self, content):
        """添加用户消息到历史"""
        self.message_history.append({"role": "user", "content": content})

    def add_assistant_message(self, content):
        """添加AI回复到历史"""
        self.message_history.append({"role": "assistant", "content": content})


# 全局状态实例
state = ModelState()
