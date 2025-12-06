"use client";

import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ChatInterface } from "@/components/chat-interface";

export function ChatCard() {
    const router = useRouter();

    return (
        <motion.div
            id="chat"
            className="relative mx-auto max-w-5xl cursor-pointer"
            onClick={() => router.push("/chat")}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    router.push("/chat");
                }
            }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ duration: 0.2 }}
        >
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-[2rem] opacity-20 blur-xl"></div>
            <div className="relative rounded-[2rem] border border-white/10 bg-[#0A0A0A]/80 backdrop-blur-xl shadow-2xl overflow-hidden hover:border-white/20 transition-colors">
                <div className="p-1 bg-white/5 border-b border-white/5 flex items-center gap-2 px-4 h-10">
                    <div className="flex gap-1.5">
                        <div className="w-3 h-3 rounded-full bg-red-500/20 border border-red-500/50"></div>
                        <div className="w-3 h-3 rounded-full bg-yellow-500/20 border border-yellow-500/50"></div>
                        <div className="w-3 h-3 rounded-full bg-green-500/20 border border-green-500/50"></div>
                    </div>
                </div>
                <div className="py-12 px-4 md:px-8 bg-gradient-to-b from-transparent to-black/50 pointer-events-none">
                    <ChatInterface />
                </div>
            </div>
        </motion.div>
    );
}
