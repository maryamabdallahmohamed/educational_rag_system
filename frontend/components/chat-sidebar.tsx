"use client";

import * as React from "react";
import Link from "next/link";
import { MessageSquarePlus, Settings, User, Menu, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ChatSidebarProps {
    className?: string;
}

export function ChatSidebar({ className }: ChatSidebarProps) {
    const [isOpen, setIsOpen] = React.useState(false);

    const conversations = [
        { id: "1", title: "Image description help", date: "Today" },
        { id: "2", title: "Math homework assistance", date: "Yesterday" },
        { id: "3", title: "Reading article summary", date: "2 days ago" },
    ];

    const sidebarContent = (
        <div className="flex h-full flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/10">
                <Link href="/" className="flex items-center gap-2">
                    <div className="h-8 w-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                        <span className="text-indigo-400 font-bold">I</span>
                    </div>
                    <span className="font-bold text-white">Iris</span>
                </Link>
                <Button
                    variant="ghost"
                    size="icon"
                    className="md:hidden text-white"
                    onClick={() => setIsOpen(false)}
                >
                    <X className="h-5 w-5" />
                </Button>
            </div>

            {/* New Chat Button */}
            <div className="p-4">
                <Button className="w-full justify-start gap-2 bg-indigo-600 hover:bg-indigo-700 text-white">
                    <MessageSquarePlus className="h-4 w-4" />
                    New Chat
                </Button>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto px-2">
                <div className="space-y-1">
                    {conversations.map((conv) => (
                        <button
                            key={conv.id}
                            className="w-full text-left px-3 py-2 rounded-lg hover:bg-white/5 transition-colors group"
                        >
                            <div className="text-sm font-medium text-white truncate">
                                {conv.title}
                            </div>
                            <div className="text-xs text-zinc-500">{conv.date}</div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Bottom Actions */}
            <div className="border-t border-white/10 p-4 space-y-2">
                <Button
                    variant="ghost"
                    className="w-full justify-start gap-2 text-zinc-400 hover:text-white hover:bg-white/5"
                >
                    <Settings className="h-4 w-4" />
                    Settings
                </Button>
                <Button
                    variant="ghost"
                    className="w-full justify-start gap-2 text-zinc-400 hover:text-white hover:bg-white/5"
                >
                    <User className="h-4 w-4" />
                    Profile
                </Button>
            </div>
        </div>
    );

    return (
        <>
            {/* Mobile Toggle Button */}
            <Button
                variant="ghost"
                size="icon"
                className="fixed top-4 left-4 z-50 md:hidden text-white bg-black/50 backdrop-blur-sm"
                onClick={() => setIsOpen(true)}
            >
                <Menu className="h-5 w-5" />
            </Button>

            {/* Desktop Sidebar */}
            <aside
                className={cn(
                    "hidden md:flex w-64 bg-[#0A0A0A] border-r border-white/10",
                    className
                )}
            >
                {sidebarContent}
            </aside>

            {/* Mobile Sidebar (Overlay) */}
            {isOpen && (
                <>
                    <div
                        className="fixed inset-0 bg-black/50 z-40 md:hidden"
                        onClick={() => setIsOpen(false)}
                    />
                    <aside className="fixed left-0 top-0 bottom-0 w-64 bg-[#0A0A0A] border-r border-white/10 z-50 md:hidden">
                        {sidebarContent}
                    </aside>
                </>
            )}
        </>
    );
}
