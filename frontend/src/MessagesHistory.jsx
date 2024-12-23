import React, { useState } from "react";

const MessagesHistory = ({messageHistory}) => {
    const [isOpen, setIsOpen] = useState(false);

    const toggleDropdown = () => {
        setIsOpen(!isOpen);
    };


    return (
        <div className="w-full max-w-md mx-auto my-1">
            <button
                onClick={toggleDropdown}
                className="w-full px-4 py-2 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 focus:outline-none"
            >
                {isOpen ? "Скрыть историю" : "Показать историю"}
            </button>

            {isOpen && (
          <textarea
              value={messageHistory}
              readOnly
              placeholder="Введите историю сообщений..."
              className="w-full h-40 my-1 p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
          />
            )}
        </div>
    );
};

export default MessagesHistory;