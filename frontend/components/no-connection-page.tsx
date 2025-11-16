"use client";

import { useState } from "react";
import { WifiOff, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

interface NoConnectionPageProps {
  onRefresh: () => void;
  hasDraft?: boolean;
}

export default function NoConnectionPage({
  onRefresh,
  hasDraft = false,
}: NoConnectionPageProps) {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => {
      setIsRefreshing(false);
      onRefresh();
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex items-center justify-center p-6">
      <div className="max-w-sm w-full text-center">
        {/* Offline Icon */}
        <div className="w-20 h-20 rounded-full bg-red-100 flex items-center justify-center mb-6 mx-auto">
          <WifiOff className="w-10 h-10 text-red-600" />
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-slate-900 mb-3">
          No Internet Connection
        </h1>

        {/* Description */}
        <p className="text-slate-600 mb-8">
          Please check your connection and try again.
        </p>

        {/* Refresh Button */}
        <Button
          onClick={handleRefresh}
          disabled={isRefreshing}
          className="max-w-xs mx-auto bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-semibold py-3 px-6 flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRefreshing ? (
            <>
              <RefreshCw className="w-5 h-5 animate-spin" />
              Checking...
            </>
          ) : (
            <>
              <RefreshCw className="w-5 h-5" />
              Retry Connection
            </>
          )}
        </Button>

        {/* Footer Text */}
        <p className="text-xs text-slate-400 mt-8">
          Your data is safe and secure
        </p>
      </div>
    </div>
  );
}
