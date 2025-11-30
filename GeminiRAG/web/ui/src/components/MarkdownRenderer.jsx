import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Check, Copy } from 'lucide-react';

export function MarkdownRenderer({ content }) {
    const [copiedCode, setCopiedCode] = useState(null);

    const copyToClipboard = (code, index) => {
        navigator.clipboard.writeText(code);
        setCopiedCode(index);
        setTimeout(() => setCopiedCode(null), 2000);
    };

    // Don't render if content is empty
    if (!content || content.trim() === '') {
        return null;
    }

    return (
        <div className="markdown-content">
            <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                    code({ node, inline, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || '');
                        const codeString = String(children).replace(/\n$/, '');
                        const codeIndex = `${match?.[1] || 'code'}-${codeString.slice(0, 20)}`;

                        return !inline && match ? (
                            <div className="relative group my-4">
                                <div className="flex items-center justify-between bg-gray-800 px-4 py-2 rounded-t-lg">
                                    <span className="text-xs font-mono text-gray-400">{match[1]}</span>
                                    <button
                                        onClick={() => copyToClipboard(codeString, codeIndex)}
                                        className="flex items-center gap-1 px-2 py-1 text-xs text-gray-300 hover:text-white hover:bg-gray-700 rounded transition-colors"
                                    >
                                        {copiedCode === codeIndex ? (
                                            <>
                                                <Check size={14} />
                                                <span>Copied!</span>
                                            </>
                                        ) : (
                                            <>
                                                <Copy size={14} />
                                                <span>Copy code</span>
                                            </>
                                        )}
                                    </button>
                                </div>
                                <SyntaxHighlighter
                                    style={oneDark}
                                    language={match[1]}
                                    PreTag="div"
                                    className="!mt-0 !rounded-t-none"
                                    {...props}
                                >
                                    {codeString}
                                </SyntaxHighlighter>
                            </div>
                        ) : (
                            <code className="bg-gray-100 text-red-600 px-1.5 py-0.5 rounded text-sm font-mono" {...props}>
                                {children}
                            </code>
                        );
                    },
                    table({ children }) {
                        return (
                            <div className="my-4 overflow-x-auto">
                                <table className="min-w-full border-collapse border border-gray-300">
                                    {children}
                                </table>
                            </div>
                        );
                    },
                    thead({ children }) {
                        return <thead className="bg-gray-100">{children}</thead>;
                    },
                    th({ children }) {
                        return (
                            <th className="border border-gray-300 px-4 py-2 text-left font-semibold text-gray-700">
                                {children}
                            </th>
                        );
                    },
                    td({ children }) {
                        return (
                            <td className="border border-gray-300 px-4 py-2 text-gray-600">
                                {children}
                            </td>
                        );
                    },
                    tr({ children }) {
                        return <tr className="hover:bg-gray-50">{children}</tr>;
                    },
                    h1({ children }) {
                        return <h1 className="text-3xl font-bold mt-6 mb-4 text-gray-900 border-b pb-2">{children}</h1>;
                    },
                    h2({ children }) {
                        return <h2 className="text-2xl font-bold mt-5 mb-3 text-gray-900 border-b pb-2">{children}</h2>;
                    },
                    h3({ children }) {
                        return <h3 className="text-xl font-bold mt-4 mb-2 text-gray-900">{children}</h3>;
                    },
                    h4({ children }) {
                        return <h4 className="text-lg font-semibold mt-3 mb-2 text-gray-800">{children}</h4>;
                    },
                    p({ children }) {
                        return <p className="my-3 leading-7 text-gray-700">{children}</p>;
                    },
                    ul({ children }) {
                        return <ul className="my-3 ml-6 list-disc space-y-2 text-gray-700">{children}</ul>;
                    },
                    ol({ children }) {
                        return <ol className="my-3 ml-6 list-decimal space-y-2 text-gray-700">{children}</ol>;
                    },
                    li({ children }) {
                        return <li className="leading-7">{children}</li>;
                    },
                    blockquote({ children }) {
                        return (
                            <blockquote className="my-4 border-l-4 border-gray-300 pl-4 italic text-gray-600">
                                {children}
                            </blockquote>
                        );
                    },
                    a({ href, children }) {
                        return (
                            <a href={href} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
                                {children}
                            </a>
                        );
                    },
                    strong({ children }) {
                        return <strong className="font-semibold text-gray-900">{children}</strong>;
                    },
                    em({ children }) {
                        return <em className="italic text-gray-700">{children}</em>;
                    },
                    hr() {
                        return <hr className="my-6 border-gray-300" />;
                    }
                }}
            >
                {content}
            </ReactMarkdown>
        </div>
    );
}
