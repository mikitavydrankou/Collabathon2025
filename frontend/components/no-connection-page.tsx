"use client";

import { useState } from "react";
import { WifiOff, RefreshCw, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

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
    // Simulate checking connection
    setTimeout(() => {
      setIsRefreshing(false);
      onRefresh();
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-100 to-slate-200 flex items-center justify-center p-4">
      <div className="max-w-md w-full">
        {/* Main Card */}
        <Card className="bg-white border-0 shadow-2xl p-8">
          <div className="flex flex-col items-center text-center">
            {/* Offline Icon */}
            <div className="w-24 h-24 rounded-full bg-red-100 flex items-center justify-center mb-6 relative">
              <WifiOff className="w-12 h-12 text-red-600" />
              <div className="absolute -top-1 -right-1 w-6 h-6 rounded-full bg-red-600 flex items-center justify-center">
                <AlertCircle className="w-4 h-4 text-white" />
              </div>
            </div>

            {/* Title */}
            <h1 className="text-2xl font-bold text-slate-900 mb-3">
              No Internet Connection
            </h1>

            {/* Description */}
            <p className="text-sm text-slate-600 mb-6">
              Oops! It looks like you're not connected to the internet. Please
              check your connection and try again.
            </p>

            {/* Draft Notification */}
            {hasDraft && (
              <div className="w-full bg-yellow-50 rounded-lg p-4 mb-6 border-2 border-yellow-200">
                <div className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-full bg-yellow-400 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-lg">📝</span>
                  </div>
                  <div className="text-left">
                    <p className="text-sm font-semibold text-slate-900 mb-1">
                      Draft Saved
                    </p>
                    <p className="text-xs text-slate-600">
                      You have an incomplete transfer saved. It will be
                      available when you reconnect.
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Connection Tips */}
            <div className="w-full bg-slate-50 rounded-lg p-4 mb-6 space-y-2">
              <p className="text-xs font-semibold text-slate-700 mb-2">
                Connection Tips:
              </p>
              <div className="space-y-2">
                <div className="flex items-start gap-2 text-xs text-slate-600">
                  <div className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 flex-shrink-0" />
                  <span>Check your WiFi or mobile data</span>
                </div>
                <div className="flex items-start gap-2 text-xs text-slate-600">
                  <div className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 flex-shrink-0" />
                  <span>Make sure airplane mode is off</span>
                </div>
                <div className="flex items-start gap-2 text-xs text-slate-600">
                  <div className="w-1.5 h-1.5 rounded-full bg-slate-400 mt-1.5 flex-shrink-0" />
                  <span>Try moving to a different location</span>
                </div>
              </div>
            </div>

            {/* Refresh Button */}
            <Button
              onClick={handleRefresh}
              disabled={isRefreshing}
              className="w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-semibold py-3 flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isRefreshing ? (
                <>
                  <RefreshCw className="w-5 h-5 animate-spin" />
                  Checking Connection...
                </>
              ) : (
                <>
                  <RefreshCw className="w-5 h-5" />
                  Refresh
                </>
              )}
            </Button>

            {/* Footer Text */}
            <p className="text-xs text-slate-400 mt-6">
              Your data is safe and will be available when you reconnect
            </p>
          </div>
        </Card>

        {/* Additional Info */}
        <div className="mt-6 text-center">
          <p className="text-xs text-slate-500">
            Having trouble? Contact support for assistance
          </p>
        </div>
      </div>
    </div>
  );
}
