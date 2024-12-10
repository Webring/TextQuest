import React, { useState, useEffect } from 'react';

const Chat = () => {
    const [messages, setMessages] = useState([]); // Список сообщений
    const [input, setInput] = useState(''); // Текущий ввод пользователя
    const [ip, setIp] = useState('localhost'); // IP-адрес сервера
    const [port, setPort] = useState('8080'); // Порт сервера
    const [socket, setSocket] = useState(null); // Объект WebSocket
    const [connectionStatus, setConnectionStatus] = useState('Disconnected'); // Состояние подключения

    const connectToServer = () => {
        if (socket) socket.close(); // Закрываем текущее соединение, если есть

        const ws = new WebSocket(`ws://${ip}:${port}`);
        setSocket(ws);

        ws.onopen = () => setConnectionStatus('Connected');
        ws.onclose = () => setConnectionStatus('Disconnected');
        ws.onerror = () => setConnectionStatus('Error');
        ws.onmessage = (event) => {
            setMessages((prev) => [...prev, event.data]);
        };
    };

    const sendMessage = () => {
        if (socket && input && connectionStatus === 'Connected') {
            socket.send(input);
            setInput(''); // Очистить поле ввода
        }
    };

    return (
        <div style={{ padding: '20px' }}>
            <h1>WebSocket Chat</h1>

            {/* Подключение */}
            <div style={{ marginBottom: '20px' }}>
                <input
                    type="text"
                    value={ip}
                    placeholder="Server IP"
                    onChange={(e) => setIp(e.target.value)}
                    style={{ marginRight: '10px' }}
                />
                <input
                    type="text"
                    value={port}
                    placeholder="Port"
                    onChange={(e) => setPort(e.target.value)}
                    style={{ marginRight: '10px' }}
                />
                <button onClick={connectToServer}>Connect</button>
                <span style={{ marginLeft: '10px', color: connectionStatus === 'Connected' ? 'green' : 'red' }}>
          {connectionStatus}
        </span>
            </div>

            {/* Сообщения */}
            <div style={{ border: '1px solid #ccc', padding: '10px', height: '200px', overflowY: 'scroll' }}>
                {messages.map((msg, idx) => (
                    <div key={idx}>{msg}</div>
                ))}
            </div>

            {/* Отправка сообщений */}
            <div style={{ marginTop: '10px' }}>
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    style={{ width: '80%', marginRight: '10px' }}
                    placeholder="Type a message"
                />
                <button onClick={sendMessage} disabled={connectionStatus !== 'Connected'}>
                    Send
                </button>
            </div>
        </div>
    );
};

export default Chat;
