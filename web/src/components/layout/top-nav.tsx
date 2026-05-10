"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Sparkles,
  FileText,
  PenLine,
  Users,
  Search,
  Bell,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";

export function TopNav() {
  const pathname = usePathname();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  const navItems = [
    { label: "Dashboard", href: "/", icon: LayoutDashboard },
    { label: "KOL", href: "/kol", icon: Users },
    { label: "AI Discovery", href: "/ai-discovery", icon: Sparkles },
    { label: "Outlines", href: "/outlines", icon: FileText },
    { label: "Workbench", href: "/workbench", icon: PenLine },
  ];

  return (
    <header className="sticky top-0 z-50 bg-card/95 backdrop-blur-sm border-b border-outline-variant/30">
      <div className="max-w-[1400px] mx-auto px-lg flex items-center justify-between h-14">
        {/* Brand */}
        <Link href="/" className="flex items-center gap-2 shrink-0">
          <span className="font-serif text-xl font-bold text-brand tracking-tight">
            NewsRadar
          </span>
          <span className="text-xs text-muted-foreground font-sans hidden sm:inline">
            NEWSROOM INTEL
          </span>
        </Link>

        {/* Navigation */}
        <nav className="flex items-center gap-1">
          {navItems.map((item) => {
            const isActive = mounted && (
              item.href === "/"
                ? pathname === "/"
                : pathname.startsWith(item.href)
            );
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  isActive
                    ? "bg-brand/10 text-brand"
                    : "text-muted-foreground hover:text-foreground hover:bg-accent"
                )}
              >
                <Icon className="h-4 w-4" />
                <span className="hidden md:inline">{item.label}</span>
              </Link>
            );
          })}
        </nav>

        {/* Right side */}
        <div className="flex items-center gap-2">
          <button className="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
            <Search className="h-4 w-4" />
          </button>
          <button className="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
            <Bell className="h-4 w-4" />
          </button>
          <button className="p-2 rounded-md text-muted-foreground hover:text-foreground hover:bg-accent transition-colors">
            <Settings className="h-4 w-4" />
          </button>
          <div className="ml-2 flex items-center gap-2 pl-2 border-l border-outline-variant/30">
            <div className="h-8 w-8 rounded-full bg-brand/20 flex items-center justify-center text-brand text-xs font-bold">
              CE
            </div>
            <div className="hidden lg:block">
              <p className="text-sm font-medium leading-tight">Chief Editor</p>
              <p className="text-xs text-muted-foreground">Admin</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
