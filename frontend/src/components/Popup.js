// This is the popup that shows up after processing the requests from the frontend form / catching up any error in the processing.

import React, { useState } from 'react';
import { CSSTransition } from 'react-transition-group';
import { FaCopy, FaTimes } from 'react-icons/fa';

function Popup({ result, onClose }) {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(result);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <CSSTransition in={true} timeout={300} classNames="popup" unmountOnExit>
            <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-60 p-4">
                <div className="glass p-4 rounded-lg max-w-md w-full relative">
                    <button
                        onClick={onClose}
                        className="absolute top-2 right-2 text-purple-400 dark:text-yellow-400 hover:text-white transition duration-300"
                    >
                        <FaTimes size={20} />
                    </button>
                    <h2 className="text-lg font-semibold mb-3 text-purple-400 dark:text-yellow-400">
                        Result
                    </h2>
                    <p className="mb-4 text-purple-400 dark:text-yellow-400 whitespace-pre-wrap popup-content">
                        {result}
                    </p>
                    <div className="flex space-x-2">
                        <button
                            onClick={handleCopy}
                            className="ethereal-glow w-1/2 p-2 bg-gray-900 text-purple-400 dark:text-yellow-400 rounded-lg font-medium flex items-center justify-center transition duration-300 hover:bg-gradient-to-r hover:from-purple-600 hover:to-yellow-600 hover:text-white hover:shadow-neon"
                        >
                            <FaCopy className="mr-2" size={16} />
                            {copied ? 'Copied!' : 'Copy'}
                        </button>
                        <button
                            onClick={onClose}
                            className="ethereal-glow w-1/2 p-2 bg-gradient-to-r from-purple-500 to-yellow-500 dark:from-purple-600 dark:to-yellow-600 text-white rounded-lg font-medium transition duration-300 hover:shadow-neon"
                        >
                            Close
                        </button>
                    </div>
                </div>
            </div>
        </CSSTransition>
    );
}

export default Popup;