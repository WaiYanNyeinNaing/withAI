import React from 'react';
import { MessageSquare, Upload, Trash2, Database, Plus } from 'lucide-react';
import { clsx } from 'clsx';

export function Sidebar({ activeTab, setActiveTab, onClearHistory, onNewChat, stats }) {
    return (
        <div className="flex flex-col h-full w-[260px] bg-gray-900 text-gray-100 p-2">
            <div className="mb-4 px-2">
                <button
                    onClick={onNewChat}
                    className="flex items-center gap-3 w-full px-3 py-3 rounded-md border border-gray-700 hover:bg-gray-800 transition-colors text-sm text-left"
                >
                    <Plus size={16} />
                    <span>New chat</span>
                </button>
            </div>

            <div className="flex-1 overflow-y-auto">
                <div className="px-3 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                    Menu
                </div>
                <nav className="space-y-1">
                    <button
                        onClick={() => setActiveTab('chat')}
                        className={clsx(
                            "flex items-center gap-3 w-full px-3 py-3 rounded-md text-sm transition-colors",
                            activeTab === 'chat' ? "bg-gray-800 text-white" : "text-gray-300 hover:bg-gray-800"
                        )}
                    >
                        <MessageSquare size={18} />
                        <span>Chat</span>
                    </button>

                    <button
                        onClick={() => setActiveTab('upload')}
                        className={clsx(
                            "flex items-center gap-3 w-full px-3 py-3 rounded-md text-sm transition-colors",
                            activeTab === 'upload' ? "bg-gray-800 text-white" : "text-gray-300 hover:bg-gray-800"
                        )}
                    >
                        <Upload size={18} />
                        <span>Upload & Index</span>
                    </button>
                </nav>
            </div>

            <div className="border-t border-gray-700 pt-4 px-2">
                {stats && (
                    <div className="mb-4 px-3 text-xs text-gray-400">
                        <div className="flex items-center gap-2 mb-2">
                            <Database size={14} />
                            <span className="font-semibold">Collection Stats</span>
                        </div>
                        <div className="flex justify-between">
                            <span>Documents:</span>
                            <span>{stats.points_count}</span>
                        </div>
                        <div className="flex justify-between">
                            <span>Vectors:</span>
                            <span>{stats.vector_size}</span>
                        </div>
                    </div>
                )}

                <button
                    onClick={onClearHistory}
                    className="flex items-center gap-3 w-full px-3 py-3 rounded-md text-sm text-gray-300 hover:bg-gray-800 hover:text-red-400 transition-colors"
                >
                    <Trash2 size={18} />
                    <span>Clear All Data</span>
                </button>
            </div>
        </div>
    );
}
