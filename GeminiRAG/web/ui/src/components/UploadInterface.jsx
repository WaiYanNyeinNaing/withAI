import React, { useState } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, Plus } from 'lucide-react';
import { api } from '../lib/api';
import { clsx } from 'clsx';

export function UploadInterface({ onUploadComplete }) {
    const [dragActive, setDragActive] = useState(false);
    const [files, setFiles] = useState([]);
    const [textInput, setTextInput] = useState('');
    const [isUploading, setIsUploading] = useState(false);
    const [uploadResults, setUploadResults] = useState(null);

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFiles(Array.from(e.dataTransfer.files));
        }
    };

    const handleChange = (e) => {
        e.preventDefault();
        if (e.target.files && e.target.files[0]) {
            setFiles(Array.from(e.target.files));
        }
    };

    const handleUpload = async () => {
        if (files.length === 0 && !textInput.trim()) return;

        setIsUploading(true);
        setUploadResults(null);

        try {
            let results = [];

            if (files.length > 0) {
                const fileRes = await api.uploadFiles(files);
                if (fileRes.success) {
                    results = fileRes.results;
                } else {
                    throw new Error(fileRes.error);
                }
            }

            if (textInput.trim()) {
                const textRes = await api.addText(textInput);
                results.push({
                    filename: 'Text Input',
                    status: textRes.success ? 'success' : 'error',
                    chunks: textRes.chunks,
                    error: textRes.error
                });
            }

            setUploadResults(results);
            setFiles([]);
            setTextInput('');
            if (onUploadComplete) onUploadComplete();

        } catch (error) {
            setUploadResults([{ filename: 'Upload Failed', status: 'error', error: error.message }]);
        } finally {
            setIsUploading(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-gray-50 p-8 overflow-y-auto">
            <div className="max-w-3xl mx-auto w-full">
                <h1 className="text-3xl font-bold text-gray-800 mb-8">Add Knowledge</h1>

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
                    <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
                        <Upload size={20} />
                        Upload Documents
                    </h2>

                    <div
                        className={clsx(
                            "border-2 border-dashed rounded-lg p-10 text-center transition-colors cursor-pointer",
                            dragActive ? "border-green-500 bg-green-50" : "border-gray-300 hover:border-gray-400"
                        )}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                        onClick={() => document.getElementById('file-upload').click()}
                    >
                        <input
                            id="file-upload"
                            type="file"
                            multiple
                            className="hidden"
                            onChange={handleChange}
                            accept=".txt,.md,.pdf"
                        />
                        <div className="flex flex-col items-center gap-3">
                            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center text-gray-500">
                                <Upload size={24} />
                            </div>
                            <p className="text-lg font-medium text-gray-700">
                                Click to upload or drag and drop
                            </p>
                            <p className="text-sm text-gray-500">
                                PDF, TXT, MD files supported
                            </p>
                        </div>
                    </div>

                    {files.length > 0 && (
                        <div className="mt-4 space-y-2">
                            {files.map((file, idx) => (
                                <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-md">
                                    <FileText size={18} className="text-gray-500" />
                                    <span className="text-sm text-gray-700 flex-1 truncate">{file.name}</span>
                                    <span className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="flex items-center gap-4 mb-8">
                    <div className="h-px bg-gray-200 flex-1"></div>
                    <span className="text-gray-400 text-sm font-medium">OR</span>
                    <div className="h-px bg-gray-200 flex-1"></div>
                </div>

                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-8">
                    <h2 className="text-lg font-semibold text-gray-700 mb-4 flex items-center gap-2">
                        <FileText size={20} />
                        Paste Text
                    </h2>
                    <textarea
                        value={textInput}
                        onChange={(e) => setTextInput(e.target.value)}
                        placeholder="Paste any text content here to index it directly..."
                        className="w-full h-40 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none"
                    />
                </div>

                <div className="flex justify-end">
                    <button
                        onClick={handleUpload}
                        disabled={isUploading || (files.length === 0 && !textInput.trim())}
                        className="flex items-center gap-2 px-6 py-3 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
                    >
                        {isUploading ? (
                            <>
                                <Loader2 size={20} className="animate-spin" />
                                Processing...
                            </>
                        ) : (
                            <>
                                <Plus size={20} />
                                Add to Knowledge Base
                            </>
                        )}
                    </button>
                </div>

                {/* Results Section */}
                {uploadResults && (
                    <div className="mt-8 animate-in fade-in slide-in-from-bottom-4">
                        <h3 className="text-lg font-semibold text-gray-700 mb-4">Processing Results</h3>
                        <div className="space-y-3">
                            {uploadResults.map((result, idx) => (
                                <div
                                    key={idx}
                                    className={clsx(
                                        "p-4 rounded-lg border flex items-start gap-3",
                                        result.status === 'success' ? "bg-green-50 border-green-200" : "bg-red-50 border-red-200"
                                    )}
                                >
                                    {result.status === 'success' ? (
                                        <CheckCircle className="text-green-600 mt-0.5" size={20} />
                                    ) : (
                                        <AlertCircle className="text-red-600 mt-0.5" size={20} />
                                    )}
                                    <div>
                                        <p className={clsx("font-medium", result.status === 'success' ? "text-green-800" : "text-red-800")}>
                                            {result.filename}
                                        </p>
                                        <p className={clsx("text-sm mt-1", result.status === 'success' ? "text-green-600" : "text-red-600")}>
                                            {result.status === 'success'
                                                ? `Successfully indexed ${result.chunks} chunks.`
                                                : `Error: ${result.error || result.reason}`}
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
