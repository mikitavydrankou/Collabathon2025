"use client";

import { Home, Send, Wallet, User, Settings } from "lucide-react";

interface BottomNavigationProps {
  activeNav: string;
  setActiveNav: (nav: string) => void;
}

export default function BottomNavigation({
  activeNav,
  setActiveNav,
}: BottomNavigationProps) {
  const navItems = [
    { id: "overview", icon: Home, label: "Overview" },
    { id: "transfer", icon: Send, label: "Transfer" },
    { id: "accounts", icon: Wallet, label: "Accounts" },
    { id: "profile", icon: User, label: "Profile" },
    { id: "settings", icon: Settings, label: "Settings" },
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-2">
      <div className="flex items-center justify-around max-w-md mx-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeNav === item.id;

          return (
            <button
              key={item.id}
              onClick={() => setActiveNav(item.id)}
              className="flex flex-col items-center gap-1 px-3 py-2 text-xs font-medium transition-colors rounded-lg hover:bg-gray-50"
            >
              <Icon
                size={24}
                className={
                  isActive
                    ? "text-primary"
                    : "text-gray-400 hover:text-foreground"
                }
              />
              <span
                className={
                  isActive ? "text-primary text-xs" : "text-gray-500 text-xs"
                }
              >
                {item.label}
              </span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
