import axios from 'axios';

export const api = {
    getStats: async () => {
        const response = await axios.get('/stats');
        return response.data;
    },

    clearAll: async () => {
        const response = await axios.post('/clear');
        return response.data;
    },

    uploadFiles: async (files) => {
        const formData = new FormData();
        files.forEach(file => {
            formData.append('files', file);
        });
        const response = await axios.post('/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },

    addText: async (text) => {
        const response = await axios.post('/add', { text });
        return response.data;
    },

    askQuestion: async (query, topK = 5) => {
        const response = await axios.post('/ask', { query, top_k: topK });
        return response.data;
    },

    askQuestionStream: async (query, topK = 5, onChunk) => {
        const response = await fetch('/ask_stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query, top_k: topK }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');

            // Keep the last line in the buffer as it might be incomplete
            buffer = lines.pop() || '';

            for (const line of lines) {
                if (line.trim().startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.trim().slice(6));
                        onChunk(data);
                    } catch (e) {
                        console.error('Error parsing JSON chunk:', e, line);
                    }
                }
            }
        }
    },

    search: async (query, topK = 5) => {
        const response = await axios.post('/search', { query, top_k: topK });
        return response.data;
    }
};
