import { ChatInterface } from "@/components/chat-interface"
import { HeroButtons } from "@/components/hero-buttons";
import { ChatCard } from "@/components/chat-card";
import { CheckCircle2, Zap, Shield, Globe } from "lucide-react"

export default function Home() {
  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-indigo-500/30">
      {/* Hero Section */}
      <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 overflow-hidden">
        {/* Background Gradients */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-[500px] bg-gradient-to-b from-indigo-500/10 via-purple-500/5 to-transparent blur-3xl -z-10" />

        <div className="container px-4 md:px-6 mx-auto text-center relative z-10">
          <div className="inline-flex items-center rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm font-medium text-indigo-300 backdrop-blur-sm mb-6">
            <span className="flex h-2 w-2 rounded-full bg-indigo-500 mr-2 animate-pulse"></span>
            Iris: Your AI Vision Assistant
          </div>

          <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-white/60 mb-6">
            Your Vision, <br /> Enhanced by AI
          </h1>

          <p className="max-w-2xl mx-auto text-lg md:text-xl text-zinc-400 mb-10 leading-relaxed">
            Iris is an advanced AI assistant designed to be your eyes.
            Ask questions, describe images, and navigate the world with confidence.
          </p>

          <HeroButtons />

          {/* Chat Interface Container */}
          <ChatCard />
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-[#080808] border-t border-white/5">
        <div className="container px-4 md:px-6 mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Why Choose Iris?</h2>
            <p className="text-zinc-400 max-w-2xl mx-auto">
              Built with accessibility at its core to empower blind and visually impaired students.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                icon: Zap,
                title: "Instant Description",
                description: "Get real-time descriptions of images, documents, and your surroundings."
              },
              {
                icon: Shield,
                title: "Private & Secure",
                description: "Your conversations and data are encrypted and never shared."
              },
              {
                icon: Globe,
                title: "Always Available",
                description: "Access Iris anytime, anywhere, on any device."
              }
            ].map((feature, i) => (
              <div key={i} className="group p-8 rounded-3xl bg-white/5 border border-white/5 hover:border-white/10 transition-colors">
                <div className="h-12 w-12 rounded-2xl bg-indigo-500/10 flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300">
                  <feature.icon className="h-6 w-6 text-indigo-400" />
                </div>
                <h3 className="text-xl font-semibold mb-3">{feature.title}</h3>
                <p className="text-zinc-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer id="about" className="py-12 border-t border-white/5 bg-[#050505]">
        <div className="container px-4 md:px-6 mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
              <Zap className="h-4 w-4 text-indigo-400" />
            </div>
            <span className="font-bold text-lg">Iris</span>
          </div>

          <div className="flex gap-8 text-sm text-zinc-400">
            <a href="#" className="hover:text-white transition-colors">Privacy</a>
            <a href="#" className="hover:text-white transition-colors">Terms</a>
            <a href="#" className="hover:text-white transition-colors">Twitter</a>
            <a href="#" className="hover:text-white transition-colors">GitHub</a>
          </div>

          <div className="text-sm text-zinc-500">
            © 2024 Iris. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
