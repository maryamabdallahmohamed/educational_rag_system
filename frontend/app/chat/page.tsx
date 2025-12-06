"use client";

import { ChatSidebar } from "@/components/chat-sidebar";
import { SimpleChatInterface } from "@/components/simple-chat-interface";
import { motion } from "framer-motion";

export default function ChatPage() {
    return (
        <div className="flex h-screen bg-[#050505] text-white">
            {/* Sidebar - Fixed Left */}
            <div className="hidden md:flex w-64 flex-col border-r border-white/10 bg-[#0A0A0A] z-20">
                <ChatSidebar className="h-full border-none" />
            </div>

            {/* Main Content - Right Side */}
            <main className="flex-1 flex flex-col relative w-full min-h-0">
                {/* Top padding for Navbar */}
                <div className="flex-1 flex flex-col pt-20 relative min-h-0">
                    <SimpleChatInterface />
                </div>
            </main>
        </div>
    );
}
