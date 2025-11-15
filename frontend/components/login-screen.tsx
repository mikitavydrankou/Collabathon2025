"use client";

import { useState } from "react";
import { Eye, EyeOff, HelpCircle, Settings, Fingerprint } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";

interface LoginScreenProps {
  onLogin: (userData: any) => void;
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [showPassword, setShowPassword] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;

    setIsLoading(true);
    setError("");

    try {
      const data = await apiClient.login({ username, password });
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_data", JSON.stringify(data));
      onLogin(data);
    } catch (err: any) {
      setError(err.message || "An error occurred during login");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-slate-800 via-slate-700 to-slate-600">
      <div className="flex-1 flex flex-col items-center justify-center px-4 pt-20 pb-12">
        <div className="mb-12">
          <svg
            className="w-20 h-20"
            viewBox="0 0 100 100"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M50 10L80 30L80 70L50 90L20 70L20 30Z"
              fill="#FBBF24"
              stroke="#FBBF24"
              strokeWidth="2"
            />
            <path
              d="M50 35L65 45L65 65L50 75L35 65L35 45Z"
              fill="none"
              stroke="#1F2937"
              strokeWidth="2"
            />
          </svg>
        </div>

        <h1 className="text-white text-center">
          <p className="text-lg font-light tracking-wide mb-2">Welcome to</p>
          <p className="text-4xl font-bold">Commerzbank</p>
        </h1>
      </div>

      <div className="flex-1 bg-slate-50 rounded-t-3xl px-6 py-10 shadow-2xl flex flex-col justify-start">
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Username / Participant Number"
              className="w-full px-4 py-3 border-2 border-slate-300 rounded-xl focus:outline-none focus:border-slate-700 focus:ring-2 focus:ring-slate-200 transition-all text-slate-900 placeholder:text-slate-400 font-medium"
            />
          </div>

          <div>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password / PIN"
                className="w-full px-4 py-3 border-2 border-slate-300 rounded-xl focus:outline-none focus:border-slate-700 focus:ring-2 focus:ring-slate-200 transition-all text-slate-900 placeholder:text-slate-400 font-medium"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 transition-colors"
              >
                {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
              </button>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl text-sm">
              {error}
            </div>
          )}

          <div className="text-right">
            <button
              type="button"
              className="text-slate-600 hover:text-slate-800 text-sm font-medium transition-colors"
            >
              Forgot credentials
            </button>
          </div>

          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setRememberMe(!rememberMe)}
              className={`w-6 h-6 rounded-full border-2 transition-all flex items-center justify-center ${
                rememberMe
                  ? "bg-slate-300 border-slate-300"
                  : "border-slate-300 hover:border-slate-400"
              }`}
            >
              {rememberMe && (
                <div className="w-2 h-2 bg-slate-500 rounded-full" />
              )}
            </button>
            <label className="text-sm text-slate-600 cursor-pointer font-medium">
              Remember user data
            </label>
          </div>

          <Button
            type="submit"
            disabled={!username || !password || isLoading}
            className="w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-bold py-3 rounded-full transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md hover:shadow-lg"
          >
            {isLoading ? "Logging in..." : "Login"}
          </Button>
        </form>

        <div className="flex justify-center gap-8 mt-10 pt-8 border-t border-slate-200">
          <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors hover:bg-slate-100 rounded-lg">
            <HelpCircle size={24} />
          </button>
          <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors hover:bg-slate-100 rounded-lg">
            <Settings size={24} />
          </button>
          <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors hover:bg-slate-100 rounded-lg">
            <Fingerprint size={24} />
          </button>
        </div>
      </div>
    </div>
  );
}
