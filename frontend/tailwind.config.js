// Configuration file for Tailwind CSS implementation. Establishes consistent styling architecture with integrated dark mode functionality to enhance UI adaptability and user experience.

/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/**/*.{js,jsx,ts,tsx}",
    ],
    theme: {
        extend: {},
    },
    plugins: [],
    darkMode: 'class', // Enables class-based dark mode
}