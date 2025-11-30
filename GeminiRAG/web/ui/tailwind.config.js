/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Custom colors to match ChatGPT/Premium look
                gray: {
                    50: '#f9fafb',
                    100: '#f3f4f6',
                    200: '#e5e7eb',
                    300: '#d1d5db',
                    400: '#9ca3af',
                    500: '#6b7280',
                    600: '#4b5563',
                    700: '#374151',
                    800: '#1f2937',
                    900: '#111827',
                    950: '#030712',
                },
                primary: {
                    50: '#f0fdf4',
                    100: '#dcfce7',
                    500: '#22c55e', // Green like ChatGPT
                    600: '#16a34a',
                    700: '#15803d',
                }
            }
        },
    },
    plugins: [],
}
