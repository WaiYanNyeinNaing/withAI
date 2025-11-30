import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { ChatInterface } from './components/ChatInterface';
import { UploadInterface } from './components/UploadInterface';
import { api } from './lib/api';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [stats, setStats] = useState(null);
  const [chatKey, setChatKey] = useState(0);

  const fetchStats = async () => {
    try {
      const data = await api.getStats();
      if (!data.error) {
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleClearHistory = async () => {
    if (window.confirm('Are you sure you want to delete ALL documents from the database? This cannot be undone.')) {
      try {
        await api.clearAll();
        await fetchStats();
        alert('All documents cleared successfully.');
      } catch (error) {
        alert('Failed to clear documents: ' + error.message);
      }
    }
  };

  const handleNewChat = () => {
    setChatKey(prev => prev + 1);
    setActiveTab('chat');
  };

  return (
    <div className="flex h-screen w-full bg-white overflow-hidden font-sans text-gray-900">
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onClearHistory={handleClearHistory}
        onNewChat={handleNewChat}
        stats={stats}
      />

      <main className="flex-1 h-full relative">
        {activeTab === 'chat' ? (
          <ChatInterface key={chatKey} />
        ) : (
          <UploadInterface onUploadComplete={fetchStats} />
        )}
      </main>
    </div>
  );
}

export default App;
