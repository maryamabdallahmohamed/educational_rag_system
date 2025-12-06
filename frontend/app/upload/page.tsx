"use client";

import { useState, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Upload, FileText, CheckCircle2, AlertCircle, ArrowLeft } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useRAGApi } from "@/hooks/use-rag-api";
import Link from "next/link";

export default function UploadPage() {
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle");
    const [message, setMessage] = useState("");
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { uploadDocument, isLoading } = useRAGApi();

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setSelectedFile(file);
            setUploadStatus("idle");
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files?.[0];
        if (file) {
            setSelectedFile(file);
            setUploadStatus("idle");
        }
    };

    const handleUpload = async () => {
        if (!selectedFile) return;

        const result = await uploadDocument(selectedFile);

        if (result.success) {
            setUploadStatus("success");
            setMessage(result.message);
        } else {
            setUploadStatus("error");
            setMessage(result.message);
        }
    };

    const resetUpload = () => {
        setSelectedFile(null);
        setUploadStatus("idle");
        setMessage("");
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    return (
        <div className="min-h-screen bg-[#050505] text-white">
            {/* Background Gradient */}
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-gradient-to-b from-indigo-500/10 via-purple-500/5 to-transparent blur-3xl -z-10" />

            <div className="container px-4 md:px-6 mx-auto py-12">
                {/* Header */}
                <div className="mb-8">
                    <Link href="/chat">
                        <Button variant="ghost" className="mb-4 text-zinc-400 hover:text-white">
                            <ArrowLeft className="h-4 w-4 mr-2" />
                            Back to Chat
                        </Button>
                    </Link>
                    <h1 className="text-4xl md:text-5xl font-bold mb-4">Upload Document</h1>
                    <p className="text-zinc-400 text-lg">
                        Upload a document to ask questions, get summaries, or process with AI agents.
                    </p>
                </div>

                {/* Upload Card */}
                <div className="max-w-2xl mx-auto">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="bg-white/5 border border-white/10 rounded-3xl p-8"
                    >
                        {/* Drag and Drop Area */}
                        <div
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onDrop={handleDrop}
                            onClick={() => fileInputRef.current?.click()}
                            className={`
                                border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
                                transition-all duration-300
                                ${isDragging
                                    ? "border-indigo-500 bg-indigo-500/10"
                                    : "border-white/20 hover:border-white/40 hover:bg-white/5"
                                }
                            `}
                        >
                            <input
                                ref={fileInputRef}
                                type="file"
                                onChange={handleFileSelect}
                                className="hidden"
                                accept=".pdf,.txt,.doc,.docx,.md,.json"
                            />

                            <div className="flex flex-col items-center gap-4">
                                <div className="h-16 w-16 rounded-full bg-indigo-500/20 flex items-center justify-center">
                                    <Upload className="h-8 w-8 text-indigo-400" />
                                </div>

                                {selectedFile ? (
                                    <div className="flex items-center gap-2 text-white">
                                        <FileText className="h-5 w-5 text-indigo-400" />
                                        <span className="font-medium">{selectedFile.name}</span>
                                        <span className="text-zinc-500 text-sm">
                                            ({(selectedFile.size / 1024).toFixed(2)} KB)
                                        </span>
                                    </div>
                                ) : (
                                    <>
                                        <div>
                                            <p className="text-lg font-medium text-white mb-1">
                                                Drop your file here or click to browse
                                            </p>
                                            <p className="text-sm text-zinc-500">
                                                Supports PDF, TXT, DOC, DOCX, MD, JSON
                                            </p>
                                        </div>
                                    </>
                                )}
                            </div>
                        </div>

                        {/* Action Buttons */}
                        <div className="flex gap-3 mt-6">
                            <Button
                                onClick={handleUpload}
                                disabled={!selectedFile || isLoading}
                                className="flex-1 bg-indigo-600 hover:bg-indigo-700 text-white h-12 text-base font-medium"
                            >
                                {isLoading ? (
                                    <>
                                        <div className="h-4 w-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2" />
                                        Uploading...
                                    </>
                                ) : (
                                    <>
                                        <Upload className="h-4 w-4 mr-2" />
                                        Upload Document
                                    </>
                                )}
                            </Button>

                            {selectedFile && (
                                <Button
                                    onClick={resetUpload}
                                    variant="outline"
                                    className="border-white/20 hover:bg-white/5 text-white h-12"
                                >
                                    Clear
                                </Button>
                            )}
                        </div>

                        {/* Status Messages */}
                        <AnimatePresence>
                            {uploadStatus !== "idle" && (
                                <motion.div
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -10 }}
                                    className={`
                                        mt-6 p-4 rounded-xl flex items-start gap-3
                                        ${uploadStatus === "success"
                                            ? "bg-green-500/10 border border-green-500/20"
                                            : "bg-red-500/10 border border-red-500/20"
                                        }
                                    `}
                                >
                                    {uploadStatus === "success" ? (
                                        <CheckCircle2 className="h-5 w-5 text-green-400 flex-shrink-0 mt-0.5" />
                                    ) : (
                                        <AlertCircle className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                                    )}
                                    <div className="flex-1">
                                        <p className={uploadStatus === "success" ? "text-green-300" : "text-red-300"}>
                                            {message}
                                        </p>
                                        {uploadStatus === "success" && (
                                            <Link href="/chat">
                                                <Button
                                                    variant="link"
                                                    className="text-green-400 hover:text-green-300 p-0 h-auto mt-2"
                                                >
                                                    Go to Chat →
                                                </Button>
                                            </Link>
                                        )}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>

                    {/* Info Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                        {[
                            { title: "Ask Questions", desc: "Query your documents with natural language" },
                            { title: "Get Summaries", desc: "Quickly understand document content" },
                            { title: "AI Processing", desc: "Advanced content analysis with CPA Agent" },
                        ].map((item, i) => (
                            <div key={i} className="bg-white/5 border border-white/10 rounded-xl p-4">
                                <h3 className="font-semibold mb-1">{item.title}</h3>
                                <p className="text-sm text-zinc-400">{item.desc}</p>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
