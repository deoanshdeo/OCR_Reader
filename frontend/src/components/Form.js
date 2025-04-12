// Welcome to the main form of my app! This is where users can type text, upload files and translate textx.

import React, { useState, useRef } from 'react';
import axios from 'axios';
import Popup from './Popup';
import { FaTrash } from 'react-icons/fa';

function Form() {
    const [text, setText] = useState('');
    const [file, setFile] = useState(null);
    const [pastedImage, setPastedImage] = useState(null);
    const [option, setOption] = useState('ocr');
    const [sourceLang, setSourceLang] = useState('auto');
    const [targetLang, setTargetLang] = useState('en');
    const [result, setResult] = useState('');
    const [showPopup, setShowPopup] = useState(false);
    const pasteAreaRef = useRef(null);

    const handleSubmit = async (e) => {
        e.preventDefault();
        if (!text && !file && !pastedImage) {
            alert('Please provide text, a file, or paste an image');
            return;
        }

        const formData = new FormData();
        formData.append('text', text);
        if (file) formData.append('file', file);
        if (pastedImage) {
            const blob = await fetch(pastedImage).then(res => res.blob());
            formData.append('file', blob, 'pasted-image.png');
        }
        formData.append('option', option);
        if (option === 'translate') {
            formData.append('source_lang', sourceLang);
            formData.append('target_lang', targetLang);
        }

        try {
            const response = await axios.post('http://localhost:5000/process', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setResult(response.data.result);
            setShowPopup(true);
        } catch (error) {
            console.error(error);
            setResult('An error occurred');
            setShowPopup(true);
        }
    };

    const clearPrompt = () => {
        setText('');
        setFile(null);
        setPastedImage(null);
        setSourceLang('auto');
        setTargetLang('en');
    };

    const handlePaste = (e) => {
        const items = (e.clipboardData || window.clipboardData).items;
        for (let i = 0; i < items.length; i++) {
            if (items[i].type.indexOf('image') === 0) {
                const blob = items[i].getAsFile();
                const url = URL.createObjectURL(blob);
                setPastedImage(url);
                e.preventDefault();
            }
        }
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        pasteAreaRef.current.classList.add('dragover');
    };

    const handleDragLeave = (e) => {
        e.preventDefault();
        pasteAreaRef.current.classList.remove('dragover');
    };

    const handleDrop = (e) => {
        e.preventDefault();
        pasteAreaRef.current.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].type.startsWith('image')) {
            const url = URL.createObjectURL(files[0]);
            setPastedImage(url);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="glass p-4 w-full max-w-md mx-auto">
            <div className="mb-3">
                <label className="block text-xs font-medium text-purple-400 dark:text-yellow-400 mb-1">
                    Text
                </label>
                <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="Enter your text..."
                    className="input-neon w-full p-2 border border-purple-400 dark:border-yellow-400 rounded-lg bg-gray-900 text-purple-400 dark:text-yellow-400 placeholder-gray-600 dark:placeholder-gray-400 focus:outline-none transition duration-300 resize-none font-medium italic"
                    rows="2"
                />
            </div>
            <div className="mb-3">
                <label className="block text-xs font-medium text-purple-400 dark:text-yellow-400 mb-1">
                    File
                </label>
                <input
                    type="file"
                    onChange={(e) => setFile(e.target.files[0])}
                    className="input-neon w-full p-2 border border-purple-400 dark:border-yellow-400 rounded-lg bg-gray-900 text-purple-400 dark:text-yellow-400 focus:outline-none transition duration-300"
                />
            </div>
            <div className="mb-3">
                <label className="block text-xs font-medium text-purple-400 dark:text-yellow-400 mb-1">
                    Paste Image
                </label>
                <div
                    ref={pasteAreaRef}
                    onPaste={handlePaste}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className="image-paste-area"
                >
                    <p className="text-purple-400 dark:text-yellow-400">
                        Paste an image here (Ctrl+V) or drop an image
                    </p>
                    {pastedImage && (
                        <img src={pastedImage} alt="Pasted Preview" className="image-preview" />
                    )}
                </div>
            </div>
            <div className="mb-3">
                <label className="block text-xs font-medium text-purple-400 dark:text-yellow-400 mb-1">
                    Action
                </label>
                <select
                    value={option}
                    onChange={(e) => setOption(e.target.value)}
                    className="input-neon w-full p-2 border border-purple-400 dark:border-yellow-400 rounded-lg bg-gray-900 text-purple-400 dark:text-yellow-400 focus:outline-none transition duration-300 font-medium italic"
                >
                    <option value="ocr">OCR Extract</option>
                    <option value="translate">Translate</option>
                </select>
            </div>
            {option === 'translate' && (
                <div className="mb-3">
                    <div className="flex space-x-2 mb-2">
                        <div className="w-1/2">
                            <label className="block text-xs font-medium text-purple-400 dark:text-yellow-400 mb-1">
                                Source Language
                            </label>
                            <select
                                value={sourceLang}
                                onChange={(e) => setSourceLang(e.target.value)}
                                className="input-neon w-full p-2 border border-purple-400 dark:border-yellow-400 rounded-lg bg-gray-900 text-purple-400 dark:text-yellow-400 focus:outline-none transition duration-300 font-medium italic"
                            >
                                <option value="auto">Auto-Detect</option>
                                <option value="en">English</option>
                                <option value="hi">Hindi</option>
                                <option value="fr">French</option>
                                <option value="es">Spanish</option>
                            </select>
                        </div>
                        <div className="w-1/2">
                            <label className="block text-xs font-medium text-purple-400 dark:text-yellow-400 mb-1">
                                Target Language
                            </label>
                            <select
                                value={targetLang}
                                onChange={(e) => setTargetLang(e.target.value)}
                                className="input-neon w-full p-2 border border-purple-400 dark:border-yellow-400 rounded-lg bg-gray-900 text-purple-400 dark:text-yellow-400 focus:outline-none transition duration-300 font-medium italic"
                            >
                                <option value="en">English</option>
                                <option value="hi">Hindi</option>
                                <option value="fr">French</option>
                                <option value="es">Spanish</option>
                            </select>
                        </div>
                    </div>
                </div>
            )}
            <div className="flex space-x-2">
                <button
                    type="submit"
                    className="ethereal-glow w-1/2 p-2 bg-gradient-to-r from-purple-500 to-yellow-500 text-white rounded-lg font-medium"
                >
                    Process
                </button>
                <button
                    type="button"
                    onClick={clearPrompt}
                    className="ethereal-glow w-1/2 p-2 bg-gray-900 text-white rounded-lg font-medium flex items-center justify-center transition duration-300 hover:bg-gradient-to-r hover:from-purple-600 hover:to-yellow-600 hover:shadow-neon"
                >
                    <FaTrash className="text-purple-400 dark:text-yellow-400 mr-2 hover:text-white transition duration-300" size={16} />
                    Clear
                </button>
            </div>
            {showPopup && <Popup result={result} onClose={() => setShowPopup(false)} />}
        </form>
    );
}

export default Form;