"use client";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { FileText, Sparkles, Send, Zap } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { useState, useRef, useEffect } from "react";
import { useRAGApi } from "@/hooks/use-rag-api";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface Message {
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
}

export function SimpleChatInterface() {
    const [message, setMessage] = useState("");
    const [messages, setMessages] = useState<Message[]>([]);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const { askQuestion, summarizeDocument, runCPAAgent, isLoading } = useRAGApi();

    const handleFileUpload = () => {
        fileInputRef.current?.click();
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // TODO: Implement file upload to backend
            console.log("File selected:", file.name);
            // You can add your upload logic here
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSubmit = async () => {
        if (message.trim() && !isLoading) {
            const userMessage: Message = {
                role: "user",
                content: message.trim(),
                timestamp: new Date(),
            };

            setMessages((prev) => [...prev, userMessage]);
            setMessage("");

            try {
                const response = await askQuestion(userMessage.content);
                const assistantMessage: Message = {
                    role: "assistant",
                    content: response.result,
                    timestamp: new Date(),
                };
                setMessages((prev) => [...prev, assistantMessage]);
            } catch (error) {
                const errorMessage: Message = {
                    role: "assistant",
                    content: "Sorry, I encountered an error processing your question. Please make sure you've uploaded a document and the backend is running.",
                    timestamp: new Date(),
                };
                setMessages((prev) => [...prev, errorMessage]);
            }
        }
    };

    const handleSummarize = async () => {
        if (isLoading) return;

        const userMessage: Message = {
            role: "user",
            content: "📄 Summarize the document",
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);

        try {
            const response = await summarizeDocument();
            const assistantMessage: Message = {
                role: "assistant",
                content: response.result,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            const errorMessage: Message = {
                role: "assistant",
                content: "Failed to summarize the document. Please ensure a document is uploaded.",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        }
    };

    const handleCPAAgent = async () => {
        if (isLoading) return;

        const userMessage: Message = {
            role: "user",
            content: "🤖 Run CPA Agent",
            timestamp: new Date(),
        };
        setMessages((prev) => [...prev, userMessage]);

        try {
            const response = await runCPAAgent();
            const assistantMessage: Message = {
                role: "assistant",
                content: response.result,
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, assistantMessage]);
        } catch (error) {
            const errorMessage: Message = {
                role: "assistant",
                content: "Failed to run CPA Agent. Please ensure a document is uploaded.",
                timestamp: new Date(),
            };
            setMessages((prev) => [...prev, errorMessage]);
        }
    };

    const handleLuAction = () => {
        console.log("Lu action triggered");
        // TODO: Implement Lu action
    };

    const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    return (
        <div className="flex flex-col h-full w-full">
            {/* Messages Area - Scrollable */}
            <div className="flex-1 min-h-0 overflow-y-auto p-3 md:p-4">
                <div className="max-w-4xl mx-auto w-full space-y-4 pb-4">
                    {/* Greeting - only show when no messages */}
                    {messages.length === 0 && (
                        <div className="flex flex-col items-center justify-center h-[35vh] text-center opacity-50 mt-10">
                            <div className="h-12 w-12 rounded-xl bg-indigo-500/20 flex items-center justify-center mb-4">
                                <Sparkles className="h-6 w-6 text-indigo-400" />
                            </div>
                            <h2 className="text-xl font-bold mb-1">Welcome to Iris</h2>
                            <p className="text-zinc-400 max-w-md text-sm">
                                Upload a document and ask questions, or use the quick actions below to analyze your content.
                            </p>
                        </div>
                    )}



                    {/* Messages List */}
                    <AnimatePresence mode="popLayout">
                        {messages.map((msg, idx) => {
                            const isUser = msg.role === "user";
                            const prevSame = messages[idx - 1]?.role === msg.role;
                            const nextSame = messages[idx + 1]?.role === msg.role;

                            // Default rounded-2xl
                            let borderRadius = "rounded-2xl";

                            if (isUser) {
                                if (prevSame && nextSame) {
                                    // Middle: Small curves on right
                                    borderRadius = "rounded-[24px] rounded-r-[4px]";
                                } else if (prevSame && !nextSame) {
                                    // Bottom (End of group): Sharp tail on bottom-right
                                    borderRadius = "rounded-[24px] rounded-tr-[4px] rounded-br-none";
                                } else if (!prevSame && nextSame) {
                                    // Top (Start of group): Small curve on bottom-right
                                    borderRadius = "rounded-[24px] rounded-br-[4px]";
                                } else {
                                    // Single: Sharp tail on bottom-right
                                    borderRadius = "rounded-[24px] rounded-br-none";
                                }
                            } else {
                                // Assistant logic (mirror of user)
                                if (prevSame && nextSame) {
                                    borderRadius = "rounded-[24px] rounded-l-[4px]";
                                } else if (prevSame && !nextSame) {
                                    borderRadius = "rounded-[24px] rounded-tl-[4px] rounded-bl-none";
                                } else if (!prevSame && nextSame) {
                                    borderRadius = "rounded-[24px] rounded-bl-[4px]";
                                } else {
                                    borderRadius = "rounded-[24px] rounded-bl-none";
                                }
                            }

                            return (
                                <motion.div
                                    key={idx}
                                    initial={{ opacity: 0, y: 10, scale: 0.98 }}
                                    animate={{ opacity: 1, y: 0, scale: 1 }}
                                    exit={{ opacity: 0, scale: 0.9 }}
                                    transition={{ duration: 0.2 }}
                                    className={`flex w-full ${isUser ? "justify-end" : "justify-start"} ${nextSame ? "mb-0.5" : "mb-6"}`}
                                >
                                    <div className={`flex max-w-[80%] md:max-w-[70%] gap-3 items-end ${isUser ? "flex-row-reverse" : "flex-row"}`}>
                                        {/* Avatar - Only show for last message in group or single message */}
                                        <div className={`flex-shrink-0 w-8 ${!nextSame ? "opacity-100" : "opacity-0"}`}>
                                            {!nextSame && (
                                                <Avatar className="h-8 w-8 shadow-sm">
                                                    {isUser ? (
                                                        <>
                                                            <AvatarImage src="/placeholder-user.jpg" />
                                                            <AvatarFallback className="bg-indigo-600 text-white text-xs">U</AvatarFallback>
                                                        </>
                                                    ) : (
                                                        <>
                                                            <AvatarImage src="/placeholder-iris.jpg" />
                                                            <AvatarFallback className="bg-zinc-800 text-indigo-400 text-xs">
                                                                <Sparkles className="h-4 w-4" />
                                                            </AvatarFallback>
                                                        </>
                                                    )}
                                                </Avatar>
                                            )}
                                        </div>

                                        <div
                                            className={`
                                                relative px-5 py-3 shadow-md ${borderRadius}
                                                ${isUser
                                                    ? "bg-[#0084FF] text-white"
                                                    : "bg-[#1A1A1A] border border-white/5 text-zinc-100"
                                                }
                                            `}
                                        >
                                            <p className="text-sm leading-relaxed whitespace-pre-wrap">
                                                {msg.content}
                                            </p>
                                            <div className={`text-[10px] mt-1.5 opacity-60 font-medium ${isUser ? "text-blue-100" : "text-zinc-500"} ${nextSame ? "hidden" : "block text-right"}`}>
                                                {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </div>
                                        </div>
                                    </div>
                                </motion.div>
                            );
                        })}
                    </AnimatePresence>

                    {/* Loading Indicator */}
                    {isLoading && (
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="flex justify-start"
                        >
                            <div className="bg-[#1A1A1A] border border-white/5 rounded-2xl rounded-bl-none px-4 py-3">
                                <div className="flex items-center gap-1.5">
                                    <div className="h-1.5 w-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                                    <div className="h-1.5 w-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                                    <div className="h-1.5 w-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                                </div>
                            </div>
                        </motion.div>
                    )}

                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Input Area - Fixed at Bottom */}
            <div className="flex-shrink-0 border-t border-white/5 bg-[#050505] p-3 md:p-4">
                <div className="max-w-4xl mx-auto w-full">
                    {/* Action Bar */}
                    <div className="flex items-center gap-1.5 mb-2 flex-wrap pb-1">
                        <Button
                            onClick={handleSummarize}
                            disabled={isLoading}
                            variant="outline"
                            size="sm"
                            className="h-7 rounded-full border-white/10 bg-[#1A1A1A]/80 hover:bg-white/10 text-zinc-300 hover:text-white text-xs backdrop-blur-md transition-all"
                        >
                            <FileText className="h-3 w-3 mr-1.5 text-indigo-400" />
                            Summarize Document
                        </Button>
                        <Button
                            onClick={handleCPAAgent}
                            disabled={isLoading}
                            variant="outline"
                            size="sm"
                            className="h-7 rounded-full border-white/10 bg-[#1A1A1A]/80 hover:bg-white/10 text-zinc-300 hover:text-white text-xs backdrop-blur-md transition-all"
                        >
                            <Sparkles className="h-3 w-3 mr-1.5 text-purple-400" />
                            Run CPA Agent
                        </Button>
                        <Button
                            onClick={handleLuAction}
                            disabled={isLoading}
                            variant="outline"
                            size="sm"
                            className="h-7 rounded-full border-white/10 bg-[#1A1A1A]/80 hover:bg-white/10 text-zinc-300 hover:text-white text-xs backdrop-blur-md transition-all"
                        >
                            <Zap className="h-3 w-3 mr-1.5 text-yellow-400" />
                            lu
                        </Button>
                    </div>

                    {/* Input Box */}
                    <div className="relative group">
                        <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-3xl blur opacity-0 group-hover:opacity-100 transition duration-500" />
                        <div className="relative bg-[#0A0A0A] border border-white/10 rounded-3xl shadow-xl overflow-hidden focus-within:border-indigo-500/50 focus-within:ring-1 focus-within:ring-indigo-500/20 transition-all">
                            <Textarea
                                placeholder="Ask a question about your document..."
                                value={message}
                                onChange={(e) => setMessage(e.target.value)}
                                onKeyDown={handleKeyDown}
                                disabled={isLoading}
                                className="min-h-[44px] max-h-[200px] w-full resize-none bg-transparent border-none text-white text-base placeholder:text-zinc-600 focus:ring-0 focus:outline-none py-3 pl-4 pr-24"
                                rows={1}
                            />
                            <input
                                type="file"
                                ref={fileInputRef}
                                onChange={handleFileChange}
                                accept=".pdf,.doc,.docx,.txt"
                                className="hidden"
                            />
                            <div className="absolute bottom-1.5 right-1.5 flex items-center gap-2">
                                <Button
                                    variant="ghost"
                                    size="icon"
                                    onClick={handleFileUpload}
                                    disabled={isLoading}
                                    className="h-9 w-9 rounded-full bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white disabled:opacity-50 p-0"
                                >
                                    <FileText className="h-4 w-4" />
                                </Button>
                                <Button
                                    size="icon"
                                    onClick={handleSubmit}
                                    disabled={!message.trim() || isLoading}
                                    className="h-9 w-9 rounded-full bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed transition-all p-0"
                                >
                                    <Send className="h-4 w-4" />
                                    <span className="sr-only">Send message</span>
                                </Button>
                            </div>
                        </div>
                    </div>
                    <p className="text-center text-[10px] text-zinc-600 mt-3">
                        Iris can make mistakes. Please verify important information.
                    </p>
                </div>
            </div>
        </div>
    );
}
