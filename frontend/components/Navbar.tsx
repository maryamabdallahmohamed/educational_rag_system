"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Menu, Zap } from "lucide-react";
import { motion } from "framer-motion";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";

const navItems = [
  { label: "Home", href: "/" },
  { label: "Features", href: "/#features" },
  { label: "Chat", href: "/#chat" },
  { label: "About", href: "/#about" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = React.useState(false);
  const [hoveredPath, setHoveredPath] = React.useState<string | null>(null);

  const handleScroll = (e: React.MouseEvent<HTMLAnchorElement, MouseEvent>, href: string) => {
    if (href.startsWith("/#")) {
      e.preventDefault();
      const id = href.replace("/#", "");
      const element = document.getElementById(id);
      if (element) {
        element.scrollIntoView({ behavior: "smooth" });
      }
    }
  };

  return (
    <motion.header
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="fixed top-4 left-1/2 -translate-x-1/2 z-50 w-[95%] max-w-4xl"
    >
      <div className="relative flex h-14 items-center justify-between rounded-full border border-white/10 bg-black/60 px-4 shadow-lg backdrop-blur-md supports-[backdrop-filter]:bg-black/30 md:px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-tr from-indigo-500 to-purple-500 text-white shadow-md">
            <Zap className="h-4 w-4 fill-current" />
          </div>
          <span className="hidden text-sm font-bold tracking-tight text-white sm:inline-block">
            Iris
          </span>
        </Link>

        {/* Desktop Navigation */}
        <nav className="hidden md:flex md:items-center md:gap-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={(e) => handleScroll(e, item.href)}
                className={cn(
                  "relative px-4 py-2 text-sm font-medium transition-colors hover:text-white",
                  isActive ? "text-white" : "text-zinc-400"
                )}
                onMouseEnter={() => setHoveredPath(item.href)}
                onMouseLeave={() => setHoveredPath(null)}
              >
                {/* Hover Background */}
                {hoveredPath === item.href && (
                  <motion.div
                    layoutId="navbar-hover"
                    className="absolute inset-0 -z-10 rounded-full bg-white/10"
                    transition={{
                      type: "spring",
                      bounce: 0.2,
                      duration: 0.6,
                    }}
                  />
                )}
                {/* Active Indicator */}
                {isActive && (
                  <motion.div
                    layoutId="navbar-active"
                    className="absolute bottom-1.5 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-indigo-500"
                  />
                )}
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Actions */}
        <div className="hidden items-center gap-2 md:flex">
          <Link href="/login">
            <Button
              variant="ghost"
              size="sm"
              className="h-8 rounded-full text-zinc-400 hover:bg-white/10 hover:text-white"
            >
              Log in
            </Button>
          </Link>
          <Button
            size="sm"
            className="h-8 rounded-full bg-white text-black hover:bg-zinc-200"
            onClick={() => {
              const element = document.getElementById("chat");
              if (element) {
                element.scrollIntoView({ behavior: "smooth" });
              }
            }}
          >
            Start Chat
          </Button>
        </div>

        {/* Mobile Navigation */}
        <div className="md:hidden">
          <Sheet open={isOpen} onOpenChange={setIsOpen}>
            <SheetTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-9 w-9 rounded-full text-white hover:bg-white/10"
              >
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent
              side="top"
              className="w-full rounded-b-3xl border-b border-white/10 bg-black/90 backdrop-blur-xl"
            >
              <SheetHeader>
                <SheetTitle className="text-left text-white">Menu</SheetTitle>
              </SheetHeader>
              <div className="flex flex-col gap-4 py-8">
                {navItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsOpen(false)}
                    className={cn(
                      "text-lg font-medium transition-colors hover:text-indigo-400",
                      pathname === item.href ? "text-white" : "text-zinc-400"
                    )}
                  >
                    {item.label}
                  </Link>
                ))}
                <div className="mt-4 flex flex-col gap-3">
                  <Button
                    variant="outline"
                    className="w-full justify-center rounded-full border-white/20 bg-transparent text-white hover:bg-white/10"
                  >
                    Log in
                  </Button>
                  <Button className="w-full justify-center rounded-full bg-indigo-600 text-white hover:bg-indigo-700">
                    Get Started
                  </Button>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </motion.header>
  );
}
