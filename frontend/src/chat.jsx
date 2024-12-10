import React, {useState} from 'react';
import SelectableList from "./SelectableList.jsx";

const Chat = () => {
    const [ip, setIp] = useState('localhost'); // IP-адрес сервера
    const [playerName, setPlayerName] = useState('player'); // IP-адрес сервера
    const [port, setPort] = useState('8765'); // Порт сервера

    const [action, setAction] = useState('view');
    const [selectedObject, setSelectedObject] = useState(null);
    const [selectedInventoryObject, setSelectedInventoryObject] = useState(null);

    const [inventory, setInventory] = useState([{"id":"storage", "name":"123", image:"123"}]);
    const [objects, setObjects] = useState([]);

    const [image, setImage] = useState("");

    const [message, setMessage] = useState("");
    const [errors, setErrors] = useState("");

    const [socket, setSocket] = useState(null); // Объект WebSocket
    const [isConnected, setIsConnected] = useState(false); // Состояние подключения (булевое)
    const [isConnecting, setIsConnecting] = useState(false);

    const toggleConnection = () => {
        if (isConnected) {
            if (socket) {
                socket.close(); // Закрываем соединение
            }
        } else {
            const ws = new WebSocket(`ws://${ip}:${port}`);
            setIsConnecting(true)
            setSocket(ws);


            ws.onopen = () => {
                ws.send(JSON.stringify({
                    "player": playerName,
                    "action_type": "connect"
                }));
                setIsConnected(true)
                setIsConnecting(false)
            };
            ws.onmessage = (event) => {
                let incoming_data = JSON.parse(event.data);

                console.log(incoming_data);

                setInventory(incoming_data["inventory"] ?? []);
                setObjects(incoming_data["surroundings"] ?? [])
                setSelectedInventoryObject(null);
                setSelectedObject(null);

                setImage(incoming_data["image"] ?? "");
                setMessage(incoming_data["message"] ?? "");
                setErrors(incoming_data["error"] ?? "");


            };
            ws.onclose = () => {
                setIsConnecting(false)
                setIsConnected(false)};
            ws.onerror = () => {
                alert('Ошибка подключения');
                setIsConnected(false);
                setIsConnecting(false);
            };
        }
    };

    const sendMessage = () => {
        if (socket && isConnected) {
            socket.send(JSON.stringify({
                "player": playerName,
                "action_type": action,
                "target_1": selectedObject,
                "target_2": selectedInventoryObject
            }));
        }
    };

    const handleChange = (event) => {
        setAction(event.target.value);
    };

    return (
        <div>
            <nav className="bg-gray-800 text-white p-4 mb-5">
                <div className="container mx-auto flex flex-col lg:flex-row items-center justify-between">
                    {/* Логотип */}
                    <div className="p-2 text-lg font-bold mb-4 md:mb-0 flex items-center">
                        <img src="/logo.png" alt="logo" className="w-10 h-10 mr-3"/>
                        <div>TextQuest</div>
                        </div>

                    {/* Форма подключения */}
                    <div className="flex flex-col md:flex-row items-center">
                        <input
                            type="text"
                            value={ip}
                            placeholder="IP сервера"
                            onChange={(e) => setIp(e.target.value)}
                            className="p-2 rounded border border-gray-400 text-black mb-2 md:mb-0 md:mr-2"
                        />
                        <input
                            type="text"
                            value={port}
                            placeholder="Порт"
                            onChange={(e) => setPort(e.target.value)}
                            className="p-2 rounded border border-gray-400 text-black mb-2 md:mb-0 md:mr-2"
                        />
                        <input
                            type="text"
                            value={playerName}
                            placeholder="Имя игрока в соответствии со сценарием"
                            onChange={(e) => setPlayerName(e.target.value)}
                            className="p-2 rounded border border-gray-400 text-black mb-2 md:mb-0 md:mr-2"
                        />
                        <button
                            onClick={toggleConnection}
                            className={`p-2 rounded text-white ${
                                isConnecting
                                    ? 'bg-gray-400 cursor-not-allowed'
                                    : isConnected
                                        ? 'bg-red-500 hover:bg-red-600'
                                        : 'bg-blue-600 hover:bg-blue-700'
                            }`}
                            disabled={isConnecting}
                        >
                            {isConnecting ? 'Подключение...' : isConnected ? 'Отключиться' : 'Подключиться'}
                        </button>
                    </div>
                </div>
            </nav>

            {isConnected ? <div className="container mx-auto">
                    <div className="flex justify-center mb-2">
                        <img className="md:w-screen lg:w-1/2 h-auto justify-center rounded-lg"
                             src={image}
                             alt="Изображение файла"/>

                    </div>

                    <div className="flex justify-center mb-2 flex-wrap">
                    <div className="flex">
                        <label className="cursor-pointer">
                            <input type="radio"
                                   name="radio-group"
                                   value="view"
                                   className="peer hidden"
                                   onChange={handleChange}
                                   defaultChecked/>
                            <div
                                className="peer-checked:bg-blue-600 peer-checked:text-white bg-gray-200 text-gray-700 px-5 py-2.5 rounded-l-lg">
                                Осмотреть
                            </div>
                        </label>

                        <label className="cursor-pointer">
                            <input type="radio" onChange={handleChange}
                                   name="radio-group" value="enter" className="peer hidden"/>
                            <div
                                className="peer-checked:bg-blue-600 peer-checked:text-white bg-gray-200 text-gray-700 px-5 py-2.5">
                                Войти
                            </div>
                        </label>

                        <label className="cursor-pointer">
                            <input type="radio" onChange={handleChange} name="radio-group" value="take"
                                   className="peer hidden"/>
                            <div
                                className="peer-checked:bg-blue-600 peer-checked:text-white bg-gray-200 text-gray-700 px-5 py-2.5">
                                Взять
                            </div>
                        </label>

                        <label className="cursor-pointer">
                            <input type="radio" onChange={handleChange} name="radio-group" value="put"
                                   className="peer hidden"/>
                            <div
                                className="peer-checked:bg-blue-600 peer-checked:text-white bg-gray-200 text-gray-700 px-5 py-2.5 rounded-r-lg">
                                Положить
                            </div>
                        </label>
                    </div>


                    <button onClick={sendMessage} disabled={!isConnected}
                            className="bg-blue-600 hover:bg-blue-700 rounded-lg text-white mt-2 md:mt-0 md:ml-3 px-4 py-2">
                        Выполнить действие
                    </button>
                </div>

                <div className="flex justify-center mb-2">
                    <div className="text-white">{message}</div>
                    <div className="text-red-700">{errors}</div>
                </div>

                <div className="flex flex-col md:flex-row gap-4">
                    <div className="md:w-1/2">
                        <h1 className="font-bold text-center text-white mb-2">Доступные объекты:</h1>
                        <SelectableList items={objects}
                                        selectedId={selectedObject}
                                        setSelectedId={setSelectedObject}/>
                    </div>
                    <div className="md:w-1/2">
                        <h1 className="font-bold text-center text-white mb-2">Инвентарь:</h1>
                        <SelectableList items={inventory}
                                        selectedId={selectedInventoryObject}
                                        setSelectedId={setSelectedInventoryObject}/>
                    </div>
                </div>
            </div> :
                <h1 className="text-white font-bold text-center p-5">
                    Введите данные игры, чтобы к ней подключиться!
                </h1>}


        </div>
    );
};

export default Chat;
