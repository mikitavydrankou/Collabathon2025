"use client";

import { useState, useEffect } from "react";
import LoginScreen from "@/components/login-screen";
import MainDashboard from "@/components/main-dashboard";
import { apiClient } from "@/lib/api";

export default function Home() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [userData, setUserData] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState<"dashboard" | "transaction">(
    "dashboard",
  );

  useEffect(() => {
    const storedUserData = apiClient.getStoredUserData();
    if (storedUserData && apiClient.isAuthenticated()) {
      setUserData(storedUserData);
      setIsLoggedIn(true);
    }
    setIsLoading(false);
  }, []);

  const handleLogin = (data: any) => {
    setUserData(data);
    setIsLoggedIn(true);
  };

  const handleLogout = () => {
    apiClient.logout();
    setIsLoggedIn(false);
    setUserData(null);
    setCurrentPage("dashboard");
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-slate-800 via-slate-700 to-slate-600">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-400"></div>
      </div>
    );
  }

  if (!isLoggedIn) {
    return <LoginScreen onLogin={handleLogin} />;
  }

  return (
    <MainDashboard
      userData={userData}
      onLogout={handleLogout}
      onNavigateTransaction={() => setCurrentPage("transaction")}
    />
  );
}
