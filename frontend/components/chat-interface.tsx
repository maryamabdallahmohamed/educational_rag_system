"use client"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Brain, Link, Folder, Mic } from "lucide-react"
import { LiquidMetal, PulsingBorder } from "@paper-design/shaders-react"
import { motion } from "framer-motion"
import { useState, useRef } from "react"

interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
}

export function ChatInterface() {
  const [isFocused, setIsFocused] = useState(false)
  const [message, setMessage] = useState("")
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleSubmit = () => {
    if (message.trim()) {
      // TODO: Send message to backend/API
      console.log("Sending message:", message)
      setMessage("") // Clear input after sending
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleFileUpload = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      console.log("File selected:", file.name)
      // TODO: Implement file upload to backend
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto relative mt-8">
      <div className="flex flex-row items-center mb-2">
        {/* Shader Circle */}
        <motion.div
          id="circle-ball"
          className="relative flex items-center justify-center z-10"
          animate={{
            y: isFocused ? 50 : 0,
            opacity: isFocused ? 0 : 100,
            filter: isFocused ? "blur(4px)" : "blur(0px)",
            rotate: isFocused ? 180 : 0,
          }}
          transition={{
            duration: 0.5,
            type: "spring",
            stiffness: 200,
            damping: 20,
          }}
        >
          <div className="z-10 absolute bg-white/5 h-11 w-11 rounded-full backdrop-blur-[3px]">
            <div className="h-[2px] w-[2px] bg-white rounded-full absolute top-4 left-4  blur-[1px]" />
            <div className="h-[2px] w-[2px] bg-white rounded-full absolute top-3 left-7  blur-[0.8px]" />
            <div className="h-[2px] w-[2px] bg-white rounded-full absolute top-8 left-2  blur-[1px]" />
            <div className="h-[2px] w-[2px] bg-white rounded-full absolute top-5 left-9 blur-[0.8px]" />
            <div className="h-[2px] w-[2px] bg-white rounded-full absolute top-7 left-7  blur-[1px]" />
          </div>
          <LiquidMetal
            style={{ height: 80, width: 80, filter: "blur(14px)", position: "absolute" }}
            colorBack="hsl(0, 0%, 0%, 0)"
            colorTint="hsl(29, 77%, 49%)"
            repetition={4}
            softness={0.5}
            shiftRed={0.3}
            shiftBlue={0.3}
            distortion={0.1}
            contour={1}
            shape="circle"
            offsetX={0}
            offsetY={0}
            scale={0.58}
            rotation={50}
            speed={5}
          />
          <LiquidMetal
            style={{ height: 80, width: 80 }}
            colorBack="hsl(0, 0%, 0%, 0)"
            colorTint="hsl(29, 77%, 49%)"
            repetition={4}
            softness={0.5}
            shiftRed={0.3}
            shiftBlue={0.3}
            distortion={0.1}
            contour={1}
            shape="circle"
            offsetX={0}
            offsetY={0}
            scale={0.58}
            rotation={50}
            speed={5}
          />
        </motion.div>

        {/* Greeting Text */}
        <motion.p
          className="text-white/40 text-sm font-light z-10"
          animate={{
            y: isFocused ? 50 : 0,
            opacity: isFocused ? 0 : 100,
            filter: isFocused ? "blur(4px)" : "blur(0px)",
          }}
          transition={{
            duration: 0.5,
            type: "spring",
            stiffness: 200,
            damping: 20,
          }}
        >
          Hello, I am Iris. I am here to be your eyes and assist you with anything you need.
        </motion.p>
      </div>

      <div className="relative">
        <motion.div
          className="absolute w-full h-full z-0 flex items-center justify-center"
          initial={{ opacity: 0 }}
          animate={{ opacity: isFocused ? 1 : 0 }}
          transition={{
            duration: 0.8,
          }}
        >
          <PulsingBorder
            style={{ height: "146.5%", minWidth: "143%" }}
            colorBack="hsl(0, 0%, 0%)"
            roundness={0.18}
            thickness={0}
            softness={0}
            intensity={0.3}
            bloom={2}
            spots={2}
            spotSize={0.25}
            pulse={0}
            smoke={0.35}
            smokeSize={0.4}
            scale={0.7}
            rotation={0}
            offsetX={0}
            offsetY={0}
            speed={1}
            colors={[
              "hsl(29, 70%, 37%)",
              "hsl(32, 100%, 83%)",
              "hsl(4, 32%, 30%)",
              "hsl(25, 60%, 50%)",
              "hsl(0, 100%, 10%)",
            ]}
          />
        </motion.div>

        <motion.div
          className="relative bg-[#040404] rounded-2xl p-4 z-10"
          animate={{
            borderColor: isFocused ? "#BA9465" : "#3D3D3D",
          }}
          transition={{
            duration: 0.6,
            delay: 0.1,
          }}
          style={{
            borderWidth: "1px",
            borderStyle: "solid",
          }}
        >
          {/* Message Input */}
          <div className="relative mb-6">
            <Textarea
              placeholder="Type your message here..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              className="min-h-[80px] resize-none bg-transparent border-none text-white text-base placeholder:text-zinc-500 focus:ring-0 focus:outline-none focus-visible:ring-0 focus-visible:outline-none [&:focus]:ring-0 [&:focus]:outline-none [&:focus-visible]:ring-0 [&:focus-visible]:outline-none pr-24"
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
            />
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".pdf,.doc,.docx,.txt"
              className="hidden"
            />
            <div className="absolute bottom-2 right-2 flex items-center gap-2">
              <Button
                variant="ghost"
                size="icon"
                onClick={handleFileUpload}
                className="h-9 w-9 rounded-full bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white p-0"
              >
                <Folder className="h-4 w-4" />
              </Button>
              <Button
                size="icon"
                onClick={handleSubmit}
                className="h-9 w-9 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white p-0"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m22 2-7 20-4-9-9-4Z" />
                  <path d="M22 2 11 13" />
                </svg>
                <span className="sr-only">Send message</span>
              </Button>
            </div>
          </div>
        </motion.div>
      </div>
    </div >
  )
}
