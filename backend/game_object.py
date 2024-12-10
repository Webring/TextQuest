from typing import Dict, Any


class GameObject:
    """Базовый класс для всех объектов сценария."""

    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "")
        self.image = data.get("image", "")
        self.objects = data.get("objects", [])
        self.on_action = data.get("on_action", {})
        self.parent = data.get("parent", None)

    def __repr__(self):
        return f"<GameObject(name={self.name}, objects={self.objects})>"

    def to_dict(self):
        return {key: value for key, value in self.__dict__.items() if key not in {"on_action"}}