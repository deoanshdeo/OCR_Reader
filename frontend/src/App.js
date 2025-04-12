/*
* This is the core component of the frontend.
* It integrates the form, theme switcher, and dynamic background effects to deliver a user-friendly and visually polished Text & File Processor.
*/

import React, { useState } from 'react';
import Form from './components/Form';
import ThemeSwitch from './components/ThemeSwitch';
import './index.css';

function App() {
    const [theme, setTheme] = useState('light');

    const toggleTheme = () => {
        setTheme(theme === 'light' ? 'dark' : 'light');
    };

    return (
        <div className={`min-h-screen ${theme} relative flex items-center justify-center p-4`}>
            <div className="bg-particles absolute top-0 left-0 w-full h-full z-0"></div>
            <div className="relative w-full max-w-xl z-10">
                <ThemeSwitch theme={theme} toggleTheme={toggleTheme} />
                <h1 className="text-2xl font-bold text-center mb-4 text-transparent bg-clip-text bg-gradient-to-r from-purple-500 to-yellow-500 p-2 rounded-lg shadow-lg">
                    Text & File Processor
                </h1>
                <Form />
            </div>
        </div>
    );
}

export default App;