import asyncio
import enum
import json
from typing import Any, Dict

import websockets

from expression_parser import evaluate_expression
from game_object import GameObject


class Actions:
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
        self.move_object(player_name, source_name, destination_name)
        self.objects[player_name].parent = destination_name

    def execute_action(self, target_1, action: Dict[str, Any], target_2: str) -> bool:
        context = self.get_object_context(target_1)
        if target_2 is not None:
            context["obj"] = target_2

        if "if" in action:
            condition = evaluate_expression(action["if"]["exp"], context)
            block = action["if"]["do"] if condition else action["if"].get("else", {})
            return self.execute_action(target_1, block, target_2)

        if "message" in action:
            return {"message": action["message"]}
        if "set_gattr" in action:
            self.gattrs.update(action["set_gattr"])
        return action.get("success", True)

    def perform_actions(self, player_name: str, action_type: str, target_1: str, target_2: str = None) -> Dict[
        str, Any]:
        current_player = self.objects[player_name]
        current_player_parent = self.objects[current_player.parent]

        if action_type == "enter" and not target_1 and current_player_parent.parent is not None:
            self.move_player(player_name, current_player_parent.parent)
            return {"message": f"Player {player_name} moved to {current_player_parent.parent}"}

        if not target_1:
            target_1 = current_player.parent

        if target_1 not in self.objects:
            return {"error": f"Target {target_1} not found"}

        target = self.objects[target_1]

        if target_2 is None:
            target_2 = ""

        if current_player.parent != target_1 and target_1 not in current_player_parent.objects:
            return {"error": "Can't find objects"}

        if action_type == "put" and target_2 not in current_player.objects:
            return {
                "error": f"Object {target_1} must be in player's inventory",
                "inventory": current_player.objects,
            }

        target_actions = target.on_action

        if action_type not in target_actions.keys():
            return {"error": f"Action type {action_type} not supported"}

        # success = True

        if isinstance(target_actions[action_type], list):
            for action_element in target_actions[action_type]:
                execution_result = self.execute_action(target_1, action_element, target_2)
                if not execution_result.get("success", True):
                    break
        else:
            execution_result = self.execute_action(target_1, target_actions[action_type], target_2)
        success = execution_result.get("success", True)

        if success and action_type == Actions.ENTER:
            self.move_player(player_name, target_1)
            return {"message": f"Player {player_name} entered {target_1}"}

        if success and action_type == Actions.TAKE:
            self.move_object(target_1, current_player.parent, player_name)
            return {"message": f"Player {player_name} took {target_1}"}

        if success and action_type == Actions.PUT:
            self.move_object(target_2, player_name, target_1)
            return {"message": f"Player {player_name} put {target_2} in {target_1}"}

        if success:
            return success
        return {"error": "Unknown action result"}

    def __repr__(self):
        return f"<Quest(title={self.title}, objects={list(self.objects.keys())})>"


# Для тестирования:
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
#         print(quest.perform_actions(current_player, action_type, target, extra_target))

connected_clients = {}


def all_players_connected():
    return len(connected_clients) == 3


def get_id_name_image(objects):
    r_list = []
    for obj in objects:
        r_list.append({"id": obj, "name": quest.objects[obj].name, "image": quest.objects[obj].image})
    return r_list


async def handler(websocket):
    global connected_clients
    async for message in websocket:
        try:
            data = json.loads(message)
        except Exception:
            await websocket.send(json.dumps({"error": "Wrong input"}))
            continue

        if "player" not in data or "action_type" not in data:
            await websocket.send(json.dumps({"error": "Wrong input (missing keys: 'player' or 'action_type')"}))
            continue

        if data["action_type"] == "connect":
            player_name = data["player"]
            connected_clients[player_name] = websocket
            await websocket.send(json.dumps({"message": f"Welcome, {player_name}!"}))
            # if all_players_connected():
            #     for client in connected_clients.values():
            #         await client.send(json.dumps({"message": "All players connected. Let the game begin!"}))
            continue

        player_name = data["player"]
        if player_name not in quest.players:
            await websocket.send(json.dumps({"error": "Player not found"}))
            continue

        action_type = data["action_type"]
        target_1 = data.get("target_1", None)
        target_2 = data.get("target_2", None)

        # Выполнение действия и отправка результата
        response = quest.perform_actions(player_name, action_type, target_1, target_2)
        print(response)
        parent_objects = quest.objects[quest.objects[player_name].parent].objects.copy()
        parent_objects.remove(player_name)
        objects_dict = {"surroundings":get_id_name_image(parent_objects)}
        inventory_dict = {"inventory":get_id_name_image(quest.objects[player_name].objects)}
        current_image = {"image": quest.objects[quest.objects[player_name].parent].image}
        response |= current_image
        response |= inventory_dict
        response |= objects_dict
        print(response)


        await websocket.send(json.dumps(response))


# {"player":"player1","action_type":"connect"}

# if "action" in data:
#     player_name = data["player"]
#     action_type = data["action"]["type"]
#     target = data["action"].get("target", "")
#     context = data["action"].get("context", {})


if __name__ == "__main__":
    with open("logic.json", mode="r", encoding="utf-8") as file:
        quest_data = json.load(file)
        quest = Quest(quest_data)


    async def main():
        # Убедитесь, что здесь передается ссылка на функцию handler, а не ее вызов
        server = await websockets.serve(handler, "localhost", 8765)
        print("Server started on ws://localhost:8765")
        await server.wait_closed()


    asyncio.run(main())
