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

    def execute_action(self, player_name,target_1, action: Dict[str, Any], target_2: str) -> bool:
        context = self.get_object_context(target_1)
        if target_2 is not None:
            context["obj"] = target_2

        if "if" in action:
            condition = evaluate_expression(action["if"]["exp"], context)
            block = action["if"]["do"] if condition else action["if"].get("else", {})
            return self.execute_action(player_name, target_1, block, target_2)

        result = {}
        if "message" in action:
            result.update({"message": action["message"]})
        if "set_gattr" in action:
            self.gattrs.update(action["set_gattr"])
        if "ch_pos" in action:
            self.move_player(player_name, action["ch_pos"])
        if "success" in action:
            result.update({"success": action.get("success")})

        return result
    def get_name(self, obj_id):
        return self.objects[obj_id].name
    def perform_actions(self, player_name: str, action_type: str, target_1: str, target_2: str = None) -> Dict[
        str, Any]:
        current_player = self.objects[player_name]
        current_player_parent = self.objects[current_player.parent]

        if action_type == "enter" and not target_1 and current_player_parent.parent is not None:
            self.move_player(player_name, current_player_parent.parent)
            return {"message": f"Игрок {self.get_name(player_name)} переместился в {self.get_name(current_player_parent.parent)}"}

        if not target_1:
            target_1 = current_player.parent

        if target_1 not in self.objects:
            return {"error": f"Цель {self.get_name(target_1)} не найдена"}

        target = self.objects[target_1]

        if target_2 is None:
            target_2 = ""

        if current_player.parent != target_1 and target_1 not in current_player_parent.objects:
            return {"error": "Невозможно найти объекты"}

        if action_type == "put" and target_2 not in current_player.objects:
            return {
                "error": f"Объект {self.get_name(target_1)} должен быть в интвентаре игрока",
                "inventory": current_player.objects,
            }

        target_actions = target.on_action

        if action_type not in target_actions.keys():
            return {"error": f"Тип взаимодействия {self.get_name(action_type)} недоступен"}

        # success = True

        if isinstance(target_actions[action_type], list):
            for action_element in target_actions[action_type]:
                execution_result = self.execute_action(player_name, target_1, action_element, target_2)
                if not execution_result.get("success", True):
                    break
        else:
            execution_result = self.execute_action(player_name, target_1, target_actions[action_type], target_2)
        success = execution_result.get("success", True)

        if success and action_type == Actions.ENTER:
            self.move_player(player_name, target_1)
            return {"message": f"Игрок {self.get_name(player_name)} вошёл в {self.get_name(target_1)}"}

        if success and action_type == Actions.TAKE:
            self.move_object(target_1, current_player.parent, player_name)
            return {"message": f"Игрок {self.get_name(player_name)} взял {self.get_name(target_1)}"}

        if success and action_type == Actions.PUT:
            self.move_object(target_2, player_name, target_1)
            return {"message": f"Игрок {self.get_name(player_name)} вставил(положил) {self.get_name(target_2)} в {self.get_name(target_1)}"}

        if success:
            return execution_result
        return {"message":execution_result.get("message")}

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

def broadcast(message):
    for player in quest.players:
        connected_clients[player].send(json.dumps({"message": message}))
    return

def sent_to(target_1,message):
    if target_1 in quest.players:
        connected_clients[target_1].send(json.dumps({"message": message}))
    return

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
            await websocket.send(json.dumps({"error": "Неверный ввод"}))
            continue

        if "player" not in data or "action_type" not in data:
            await websocket.send(json.dumps({"error": "Неверный ввод (missing keys: 'player' or 'action_type')"}))
            continue

        if data["action_type"] == "connect":
            player_name = data["player"]
            connected_clients[player_name] = websocket
            await websocket.send(json.dumps({"message": f"Добро пожаловать, {player_name}!"}))
            if all_players_connected():
                for client in connected_clients.values():
                    await client.send(json.dumps({"message": "Все игроки подключены. Пусть игра начнётся!"}))
            continue
        if data["action_type"] == Actions.SEND_INFO:
            target_1 = data.get("target_1", None)
            message = data.get("target_2", None)
            sent_to(target_1,message)

        player_name = data["player"]
        if player_name not in quest.players:
            await websocket.send(json.dumps({"error": "Игрок не найден"}))
            continue

        if data["action_type"] != "connect":
            action_type = data["action_type"]
            target_1 = data.get("target_1", None)
            target_2 = data.get("target_2", None)

            # Выполнение действия и отправка результата
            response = quest.perform_actions(player_name, action_type, target_1, target_2)
            try:
                # Проверяем, выполнили ли все игроки условие (например, получили атрибут `is_end`)
                all_ready = all(
                    quest.objects[player].gattrs.get("is_end", False)  # Проверяем наличие атрибута в gattrs
                    for player in quest.players
                )

                if all_ready:
                    # Если все игроки готовы, перемещаем их в 4-ю комнату
                    for player in quest.players:
                        quest.move_player(player, "room_4")
                        await connected_clients[player].send(
                            json.dumps({"message": "Все игроки готовы. Вы переходите в 4-ю комнату!", "room": "room_4"})
                        )
                else:
                    # Если не все игроки готовы, отправляем экран ожидания
                    await websocket.send(json.dumps({"message": "Ждём остальных игроков, чтобы перейти в следующую комнату."}))
            except Exception as e:
                print(e)


            # Добавляем текущий контекст (инвентарь, окружение, изображение и т. д.)
            parent_objects = quest.objects[quest.objects[player_name].parent].objects.copy()
            parent_objects.remove(player_name)
            objects_dict = {"surroundings": get_id_name_image(parent_objects)}
            inventory_dict = {"inventory": get_id_name_image(quest.objects[player_name].objects)}
            current_image = {"image": quest.objects[quest.objects[player_name].parent].image}
            try:
                response |= current_image
                response |= inventory_dict
                response |= objects_dict
            except Exception as e:
                print(e)
            print(response)

            await websocket.send(json.dumps(response))

# async def handler(websocket):
#     global connected_clients
#     async for message in websocket:
#         try:
#             data = json.loads(message)
#         except Exception:
#             await websocket.send(json.dumps({"error": "Неверный ввод"}))
#             continue
#
#         if "player" not in data or "action_type" not in data:
#             await websocket.send(json.dumps({"error": "Неверный ввод (missing keys: 'player' or 'action_type')"}))
#             continue
#
#         if data["action_type"] == "connect":
#             player_name = data["player"]
#             connected_clients[player_name] = websocket
#             await websocket.send(json.dumps({"message": f"Добро пожаловать, {player_name}!"}))
#             if all_players_connected():
#                 for client in connected_clients.values():
#                     await client.send(json.dumps({"message": "Все игроки подключены. Пусть игра начнётся!"}))
#             continue
#
#         player_name = data["player"]
#         if player_name not in quest.players:
#             await websocket.send(json.dumps({"error": "Игрок не найден"}))
#             continue
#
#         if data["action_type"] != "connect":
#             action_type = data["action_type"]
#             target_1 = data.get("target_1", None)
#             target_2 = data.get("target_2", None)
#
#             # Выполнение действия и отправка результата
#             response = quest.perform_actions(player_name, action_type, target_1, target_2)
#             parent_objects = quest.objects[quest.objects[player_name].parent].objects.copy()
#             parent_objects.remove(player_name)
#             objects_dict = {"surroundings":get_id_name_image(parent_objects)}
#             inventory_dict = {"inventory":get_id_name_image(quest.objects[player_name].objects)}
#             current_image = {"image": quest.objects[quest.objects[player_name].parent].image}
#             response |= current_image
#             response |= inventory_dict
#             response |= objects_dict
#
#
#             await websocket.send(json.dumps(response))


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
