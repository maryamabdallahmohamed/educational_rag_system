"use client";

import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";

export function HeroButtons() {
    const scrollToChat = () => {
        const element = document.getElementById("chat");
        if (element) {
            element.scrollIntoView({ behavior: "smooth" });
        }
    };

    return (
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Button
                size="lg"
                className="rounded-full h-12 px-8 text-base bg-white text-black hover:bg-zinc-200"
                onClick={scrollToChat}
            >
                Start Chatting
                <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button
                size="lg"
                variant="outline"
                className="rounded-full h-12 px-8 text-base border-white/10 bg-white/5 hover:bg-white/10 text-white"
            >
                Learn More
            </Button>
        </div>
    );
}
