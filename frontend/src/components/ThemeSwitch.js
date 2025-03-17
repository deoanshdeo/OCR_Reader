import React from 'react';

function ThemeSwitch({ theme, toggleTheme }) {
    return (
        <div className="fixed top-4 right-4">
            <button
                onClick={toggleTheme}
                className="relative w-10 h-5 bg-gray-300 dark:bg-gray-700 rounded-full p-1 shadow-md transition duration-300"
            >
                <div
                    className={`w-3 h-3 rounded-full bg-gradient-to-r from-purple-500 to-yellow-500 flex items-center justify-center text-white shadow-inner transform transition duration-300 ${
                        theme === 'light' ? 'translate-x-1' : 'translate-x-5'
                    }`}
                >
                    {theme === 'light' ? '☀️' : '🌙'}
                </div>
            </button>
        </div>
    );
}

export default ThemeSwitch;