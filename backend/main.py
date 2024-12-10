import asyncio
import enum
import json
from typing import Any, Dict

import websockets

from expression_parser import evaluate_expression
from game_object import GameObject


class Actions(enum.Enum):
    VIEW = "view"
    TAKE = "take"
    PUT = "put"
    ENTER = "enter"
    SEND_INFO = "send"


class Quest:
    def __init__(self, data: Dict[str, Any]):
        self.title = data["title"]
        self.meta = data["meta"]
        self.gattrs = data["gattrs"]
        self.objects = self._parse_objects(data["objects"])
        self.objects_names = set(self.objects.keys())
        self.end_actions = data.get("end_actions", {})
        self.players = data["players"]
        self.checking_script_correctness()

    def checking_script_correctness(self):
        for player_name in self.players:
            if player_name not in self.objects_names:
                raise KeyError(f"У игрока {player_name} нет объекта")

            player_parent = self.objects[player_name].parent
            if player_name not in self.objects[player_parent].objects:
                raise ValueError(f"Не корректное местоположение игрока {player_name}")

    def _parse_objects(self, objects_data: Dict[str, Any]) -> Dict[str, GameObject]:
        parsed_objects = {}
        for obj_id, obj_data in objects_data.items():
            parsed_objects[obj_id] = GameObject(obj_data)
        return parsed_objects

    def get_object_context(self, obj):
        return {**self.objects[obj].to_dict(), **self.gattrs}

    def move_object(self, object_name, source_name, destination_name):
        self.objects[source_name].objects.remove(object_name)
        self.objects[destination_name].objects.append(object_name)

    def move_player(self, player_name, destination_name):
        source_name = self.objects[player_name].parent
        self.move_object(source_name, destination_name, player_name)
        self.objects[player_name].parent = destination_name

    def execute_action(self, target_name, action: Dict[str, Any], context: dict) -> bool:
        context |= self.get_object_context(target_name)

        if "if" in action:
            condition = evaluate_expression(action["if"]["exp"], context)
            block = action["if"]["do"] if condition else action["if"].get("else", {})
            return self.execute_action(target_name, block, context)

        if "message" in action:
            print(action["message"])
        if "set_gattr" in action:
            self.gattrs.update(action["set_gattr"])
        return action.get("success", True)

    def perform_actions(self, player_name: str, action_type: str, target_name: str, context: dict = None) -> None:
        current_player = self.objects[player_name]
        current_player_parent = self.objects[current_player.parent]

        if action_type == "enter" and not target_name and current_player_parent.parent is not None:
            self.objects[player_name].parent = current_player_parent.parent
            return

        if not target_name:
            target_name = current_player.parent

        target = self.objects[target_name]

        if context is None:
            context = {}

        if current_player.parent != target_name and target_name not in current_player_parent.objects:
            print(f"Error: can't find objects")
            return

        if action_type == "put" and context["obj"] not in current_player.objects:
            print(f"Error: object {target_name} must be in player's inventory")
            print(current_player.objects)
            return

        target_actions = target.on_action

        if action_type not in target_actions.keys():
            print(f"Error: action type {action_type} not supported")
            return

        success = True

        if isinstance(target_actions[action_type], list):
            for action_element in target_actions[action_type]:
                success = self.execute_action(target_name, action_element, context)
                if not success:
                    break
        else:
            success = self.execute_action(target_name, target_actions[action_type], context)

        if success and action_type == Actions.ENTER:
            self.move_player(player_name, target_name)

        if success and action_type == Actions.TAKE:
            self.move_object(target_name, current_player.parent, player_name)

        if success and action_type == Actions.PUT:
            self.move_object(context["obj"], player_name, target_name)

    def __repr__(self):
        return f"<Quest(title={self.title}, objects={list(self.objects.keys())})>"


# # Для тестирования:
# if __name__ == "__main__":
#     with open("demo.json", mode="r", encoding="utf-8") as file:
#         quest_data = json.load(file)
#         quest = Quest(quest_data)
#
#     current_player = "player"
#
#     while True:
#         command = input("> ")
#
#         if command == "q":
#             break
#
#         attrs = command.split(" ", 2)
#         action_type, target, extra_target = attrs + [""] * (3 - len(attrs))
#         quest.perform_actions(current_player, action_type, target, {"obj": extra_target})

connected_clients = {}


async def handler(websocket):
    global connected_clients
    async for message in websocket:
        data = json.loads(message)

        if "connect" in data:
            player_name = data["connect"]
            connected_clients[player_name] = websocket
            await websocket.send(json.dumps({"message": f"Welcome, {player_name}!"}))
            continue

        if "action" in data:
            player_name = data["player"]
            action_type = data["action"]["type"]
            target = data["action"].get("target", "")
            context = data["action"].get("context", {})

            if player_name not in quest.players:
                await websocket.send(json.dumps({"error": "Player not found"}))
                continue

            response = quest.perform_actions(player_name, action_type, target, context)
            await websocket.send(json.dumps(response))

if __name__ == "__main__":
    with open("demo.json", mode="r", encoding="utf-8") as file:
        quest_data = json.load(file)
        quest = Quest(quest_data)

    async def main():
        # Убедитесь, что здесь передается ссылка на функцию handler, а не ее вызов
        server = await websockets.serve(handler, "localhost", 8765)
        print("Server started on ws://localhost:8765")
        await server.wait_closed()

    asyncio.run(main())
