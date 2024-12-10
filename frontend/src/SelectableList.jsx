import React, {useState} from 'react';



const SelectableList = ({items, selectedId, setSelectedId}) => {

    const handleSelect = (id) => {
        setSelectedId((prevSelectedId) => (prevSelectedId === id ? null : id));
    };
    return (
        <div className="flex flex-col rounded-lg overflow-hidden">
            {items.length === 0 ? <h2 className="text-white text-center">Пусто</h2>:
                items.map((item, index) => (
                <div
                    key={index}
                    onClick={() => handleSelect(item.id)}
                    className={`flex items-center p-3 cursor-pointer ${
                        selectedId === item.id ? "bg-blue-500 text-white" : "bg-white text-black"
                    } ${
                        index < items.length - 1 ? "border-b" : ""
                    }`} // Граница между элементами
                >
                    <img
                        src={item.image}
                        alt={item.name}
                        className="w-8 h-8 rounded-full mr-4"
                    />
                    <span>{item.name}</span>
                </div>
            ))}

        </div>
    );
};

export default SelectableList;