import React, { useState, useRef, useEffect } from 'react';
import { Send, User, Bot, Loader2, FileText } from 'lucide-react';
import { MarkdownRenderer } from './MarkdownRenderer';
import { api } from '../lib/api';
import { clsx } from 'clsx';

export function ChatInterface() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I can help you answer questions based on your indexed documents. What would you like to know?' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState('pro'); // 'pro' or 'flash'
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    // Add a placeholder message for streaming
    const assistantMessageIndex = messages.length + 1;
    setMessages(prev => [...prev, { role: 'assistant', content: '', isStreaming: true }]);

    try {
      let fullContent = '';
      let stage1Thinking = '';
      let stage1Draft = '';
      let stage2Reflection = '';
      let stage3Thinking = '';
      let sources = [];

      await api.askQuestionStream(userMessage, 5, mode, (chunk) => {
        if (chunk.type === 'sources') {
          sources = chunk.sources;
        } else if (chunk.type === 'stage1_thinking') {
          stage1Thinking += chunk.content;
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: fullContent,
              stage1Thinking,
              stage1Draft,
              stage2Reflection,
              stage3Thinking,
              sources,
              isStreaming: true
            };
            return newMessages;
          });
        } else if (chunk.type === 'stage1_draft') {
          stage1Draft += chunk.content;
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: fullContent,
              stage1Thinking,
              stage1Draft,
              stage2Reflection,
              stage3Thinking,
              sources,
              isStreaming: true
            };
            return newMessages;
          });
        } else if (chunk.type === 'stage2_reflection') {
          stage2Reflection += chunk.content;
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: fullContent,
              stage1Thinking,
              stage1Draft,
              stage2Reflection,
              stage3Thinking,
              sources,
              isStreaming: true
            };
            return newMessages;
          });
        } else if (chunk.type === 'stage3_thinking') {
          stage3Thinking += chunk.content;
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: fullContent,
              stage1Thinking,
              stage1Draft,
              stage2Reflection,
              stage3Thinking,
              sources,
              isStreaming: true
            };
            return newMessages;
          });
        } else if (chunk.type === 'content') {
          fullContent += chunk.content;
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: fullContent,
              stage1Thinking,
              stage1Draft,
              stage2Reflection,
              stage3Thinking,
              sources,
              isStreaming: true
            };
            return newMessages;
          });
        } else if (chunk.type === 'done') {
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: fullContent,
              stage1Thinking,
              stage1Draft,
              stage2Reflection,
              stage3Thinking,
              sources,
              isStreaming: false
            };
            return newMessages;
          });
          setIsLoading(false);
        } else if (chunk.type === 'error') {
          setMessages(prev => {
            const newMessages = [...prev];
            newMessages[assistantMessageIndex] = {
              role: 'assistant',
              content: `Error: ${chunk.error}`,
              isError: true,
              isStreaming: false
            };
            return newMessages;
          });
          setIsLoading(false);
        }
      });

    } catch (error) {
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[assistantMessageIndex] = {
          role: 'assistant',
          content: `Error: ${error.message}`,
          isError: true,
          isStreaming: false
        };
        return newMessages;
      });
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-white relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto pb-32">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={clsx(
              "w-full border-b border-black/5 dark:border-white/5",
              msg.role === 'assistant' ? "bg-gray-50" : "bg-white"
            )}
          >
            <div className="max-w-3xl mx-auto px-4 py-8 flex gap-6">
              <div className="flex-shrink-0 flex flex-col relative items-end">
                <div className={clsx(
                  "w-8 h-8 rounded-sm flex items-center justify-center",
                  msg.role === 'assistant' ? "bg-green-500" : "bg-gray-800"
                )}>
                  {msg.role === 'assistant' ? <Bot size={20} className="text-white" /> : <User size={20} className="text-white" />}
                </div>
              </div>

              <div className="relative flex-1 overflow-hidden">
                {msg.isError ? (
                  <span className="text-red-500">{msg.content}</span>
                ) : (
                  <>
                    {/* Stage 1: Initial Thinking */}
                    {msg.stage1Thinking && (
                      <div className="mb-4">
                        <details className="group">
                          <summary className="flex items-center gap-2 cursor-pointer text-sm text-blue-600 hover:text-blue-800 select-none">
                            <span className="font-medium">🧠 Stage 1: Initial Thinking</span>
                            <span className="text-xs opacity-50 group-open:hidden">(Click to expand)</span>
                          </summary>
                          <div className="mt-2 pl-4 border-l-2 border-blue-200 text-sm bg-blue-50 p-3 rounded-r-md">
                            <MarkdownRenderer content={msg.stage1Thinking} />
                          </div>
                        </details>
                      </div>
                    )}

                    {/* Stage 1: Draft Answer */}
                    {msg.stage1Draft && (
                      <div className="mb-4">
                        <details className="group">
                          <summary className="flex items-center gap-2 cursor-pointer text-sm text-green-600 hover:text-green-800 select-none">
                            <span className="font-medium">📝 Stage 1: Draft Answer</span>
                            <span className="text-xs opacity-50 group-open:hidden">(Click to expand)</span>
                          </summary>
                          <div className="mt-2 pl-4 border-l-2 border-green-200 text-sm bg-green-50 p-3 rounded-r-md">
                            <MarkdownRenderer content={msg.stage1Draft} />
                          </div>
                        </details>
                      </div>
                    )}

                    {/* Stage 2: Reflection */}
                    {msg.stage2Reflection && (
                      <div className="mb-4">
                        <details className="group">
                          <summary className="flex items-center gap-2 cursor-pointer text-sm text-purple-600 hover:text-purple-800 select-none">
                            <span className="font-medium">🔍 Stage 2: Reflection</span>
                            <span className="text-xs opacity-50 group-open:hidden">(Click to expand)</span>
                          </summary>
                          <div className="mt-2 pl-4 border-l-2 border-purple-200 text-sm bg-purple-50 p-3 rounded-r-md">
                            <MarkdownRenderer content={msg.stage2Reflection} />
                          </div>
                        </details>
                      </div>
                    )}

                    {/* Stage 3: Final Thinking */}
                    {msg.stage3Thinking && (
                      <div className="mb-4">
                        <details className="group">
                          <summary className="flex items-center gap-2 cursor-pointer text-sm text-orange-600 hover:text-orange-800 select-none">
                            <span className="font-medium">💭 Stage 3: Final Thinking</span>
                            <span className="text-xs opacity-50 group-open:hidden">(Click to expand)</span>
                          </summary>
                          <div className="mt-2 pl-4 border-l-2 border-orange-200 text-sm bg-orange-50 p-3 rounded-r-md">
                            <MarkdownRenderer content={msg.stage3Thinking} />
                          </div>
                        </details>
                      </div>
                    )}

                    {/* Final Answer */}
                    <div className="mb-2">
                      {(msg.stage1Thinking || msg.stage1Draft || msg.stage2Reflection || msg.stage3Thinking) && (
                        <div className="text-sm font-semibold text-gray-700 mb-2">✨ Final Answer:</div>
                      )}
                      <MarkdownRenderer content={msg.content} />
                    </div>
                    {msg.isStreaming && (
                      <span className="inline-block w-2 h-5 bg-gray-400 animate-pulse ml-1"></span>
                    )}
                  </>
                )}

                {/* Sources Section */}
                {msg.sources && msg.sources.length > 0 && !msg.isStreaming && (
                  <div className="mt-6 pt-4 border-t border-gray-200">
                    <h4 className="text-sm font-semibold text-gray-600 mb-3 flex items-center gap-2">
                      <FileText size={16} />
                      References ({msg.sources.length})
                    </h4>
                    <div className="grid gap-2">
                      {msg.sources.map((source, sIdx) => {
                        const filename = source.metadata?.filename || source.metadata?.source || 'Unknown';
                        const page = source.metadata?.page;

                        return (
                          <div key={sIdx} className="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-sm transition-shadow">
                            <div className="flex items-center gap-3">
                              <span className="text-xs font-semibold text-gray-500 min-w-[24px]">[{sIdx + 1}]</span>
                              <div className="flex-1">
                                <div className="font-medium text-sm text-gray-700">
                                  📄 {filename}
                                </div>
                                {page !== undefined && (
                                  <div className="text-xs text-gray-500 mt-0.5">
                                    Page {page}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="absolute bottom-0 left-0 w-full bg-gradient-to-t from-white via-white to-transparent pt-10 pb-6 px-4">
        <div className="max-w-3xl mx-auto">
          {/* Mode Selector */}
          <div className="mb-3 flex items-center justify-center gap-2">
            <span className="text-xs text-gray-500">Mode:</span>
            <button
              onClick={() => setMode('pro')}
              className={clsx(
                "px-3 py-1.5 text-xs font-medium rounded-lg transition-all",
                mode === 'pro'
                  ? "bg-purple-600 text-white shadow-sm"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              🧠 Pro Mode
            </button>
            <button
              onClick={() => setMode('flash')}
              className={clsx(
                "px-3 py-1.5 text-xs font-medium rounded-lg transition-all",
                mode === 'flash'
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              )}
            >
              ⚡ Flash Mode
            </button>
            <span className="text-xs text-gray-400 ml-2">
              {mode === 'pro' ? '(3-stage reasoning)' : '(quick answer)'}
            </span>
          </div>

          <form onSubmit={handleSubmit} className="relative shadow-lg rounded-xl border border-gray-200 bg-white focus-within:ring-2 focus-within:ring-green-500/20 focus-within:border-green-500 transition-all">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Send a message..."
              className="w-full py-4 pl-4 pr-12 bg-transparent border-none focus:ring-0 resize-none max-h-[200px] overflow-y-auto"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="absolute right-2 bottom-2 p-2 rounded-md text-gray-400 hover:bg-gray-100 disabled:opacity-50 disabled:hover:bg-transparent transition-colors"
            >
              {isLoading ? <Loader2 size={20} className="animate-spin" /> : <Send size={20} />}
            </button>
          </form>
          <div className="text-center text-xs text-gray-400 mt-2">
            GeminiRAG can make mistakes. Consider checking important information.
          </div>
        </div>
      </div>
    </div>
  );
}
