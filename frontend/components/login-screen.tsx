"use client";

import { useState } from "react";
import { HelpCircle, Settings, Fingerprint, Delete } from "lucide-react";
import { apiClient } from "@/lib/api";
import FaceIdButton from "@/components/face-id-button";

interface LoginScreenProps {
  onLogin: (userData: any) => void;
}

export default function LoginScreen({ onLogin }: LoginScreenProps) {
  const [pin, setPin] = useState("");
  const [error, setError] = useState("");
  const [showBiometricModal, setShowBiometricModal] = useState(false);

  const handlePinInput = (digit: string) => {
    if (pin.length < 6) {
      const newPin = pin + digit;
      setPin(newPin);

      // Auto-login when PIN reaches 6 digits
      if (newPin.length === 6) {
        setTimeout(() => {
          loginUser();
        }, 300); // Small delay for visual feedback
      }
    }
  };

  const handleDeletePin = () => {
    setPin(pin.slice(0, -1));
    setError(""); // Clear error when user starts correcting
  };

  const handleBiometricClick = () => {
    setShowBiometricModal(true);
  };

  const loginUser = async () => {
    setError("");

    try {
      // Always login as alex.brown with password123
      const credentials = { username: "alex.brown", password: "password123" };

      const data = await apiClient.login(credentials);
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("user_data", JSON.stringify(data));
      onLogin(data);
    } catch (err: any) {
      setError(err.message || "Authentication failed");
      setShowBiometricModal(false);
    }
  };

  const handleBiometricSuccess = async () => {
    await loginUser();
    setShowBiometricModal(false);
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <div className="px-4 pt-6 pb-6 bg-white shadow-md">
        <div className="flex justify-center mb-6">
          <img
            src="/Commerzbank-logo.png"
            alt="Commerzbank Logo"
            className="h-20 w-auto object-contain"
          />
        </div>

        {/* User and Welcome Message Side by Side */}
        <div className="flex items-center justify-between gap-4">
          {/* User Info on Left */}
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-yellow-400 to-yellow-500 rounded-full flex items-center justify-center shadow-lg flex-shrink-0">
              <span className="text-slate-900 text-base font-bold">AB</span>
            </div>
            <div className="text-left">
              <h2 className="text-slate-900 text-sm font-bold leading-tight">
                Alex Brown
              </h2>
              <p className="text-slate-600 text-xs font-medium">Welcome back</p>
            </div>
          </div>

          {/* Welcome Message on Right */}
          <div className="text-right">
            <p className="text-xs font-light tracking-wide text-slate-600 mb-0.5">
              Welcome to
            </p>
            <p className="text-lg font-bold tracking-tight text-slate-900">
              Commerzbank
            </p>
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 bg-slate-50 px-5 pb-3 flex flex-col">
        {/* Spacer to push content down */}
        <div className="flex-1" />

        {/* PIN Display */}
        <div className="mb-6">
          <p className="text-center text-slate-700 text-sm font-semibold mb-2">
            Enter your PIN
          </p>
          <div className="flex justify-center gap-2.5">
            {[0, 1, 2, 3, 4, 5].map((index) => (
              <div
                key={index}
                className={`w-3 h-3 rounded-full transition-all duration-300 ${
                  index < pin.length
                    ? "bg-slate-900 scale-125 shadow-md"
                    : "bg-slate-300"
                }`}
              />
            ))}
          </div>
        </div>

        {error && (
          <div className="bg-red-50 border-2 border-red-200 text-red-700 px-4 py-3 rounded-2xl text-sm mb-4 text-center font-medium">
            {error}
          </div>
        )}

        {/* PIN Pad */}
        <div className="grid grid-cols-3 gap-2.5 w-full max-w-[280px] mx-auto mb-6">
          {[1, 2, 3, 4, 5, 6, 7, 8, 9].map((digit) => (
            <button
              key={digit}
              onClick={() => handlePinInput(digit.toString())}
              className="aspect-square bg-white hover:bg-slate-50 active:bg-slate-100 border-2 border-slate-200 rounded-full text-slate-900 text-xl font-bold transition-all shadow-lg hover:shadow-xl active:scale-95 active:shadow-md"
              type="button"
            >
              {digit}
            </button>
          ))}
          <div className="aspect-square" />
          <button
            onClick={() => handlePinInput("0")}
            className="aspect-square bg-white hover:bg-slate-50 active:bg-slate-100 border-2 border-slate-200 rounded-full text-slate-900 text-xl font-bold transition-all shadow-lg hover:shadow-xl active:scale-95 active:shadow-md"
            type="button"
          >
            0
          </button>
          <button
            onClick={handleDeletePin}
            className="aspect-square bg-white hover:bg-slate-50 active:bg-slate-100 border-2 border-slate-200 rounded-full text-slate-600 transition-all shadow-lg hover:shadow-xl active:scale-95 active:shadow-md flex items-center justify-center"
            type="button"
          >
            <Delete size={22} strokeWidth={2.5} />
          </button>
        </div>

        {/* Spacer to push footer down */}
        <div className="flex-1" />

        {/* Quick Actions */}
        <div className="flex justify-center items-center gap-8 pt-3 border-t-2 border-slate-200">
          <button
            type="button"
            className="p-2 text-slate-400 hover:text-slate-600 transition-all hover:bg-slate-100 rounded-xl active:scale-95"
          >
            <HelpCircle size={26} strokeWidth={2} />
          </button>
          <button
            type="button"
            onClick={handleBiometricClick}
            className="p-4 bg-gradient-to-br from-yellow-400 to-yellow-500 hover:from-yellow-500 hover:to-yellow-600 text-white transition-all rounded-3xl border-2 border-yellow-300 shadow-2xl hover:shadow-3xl active:scale-95"
          >
            <Fingerprint size={38} strokeWidth={2.5} />
          </button>
          <button
            type="button"
            className="p-2 text-slate-400 hover:text-slate-600 transition-all hover:bg-slate-100 rounded-xl active:scale-95"
          >
            <Settings size={26} strokeWidth={2} />
          </button>
        </div>

        <p className="text-center text-slate-500 text-xs font-medium mt-2">
          Use Face ID for quick access
        </p>
      </div>

      {/* Biometric Modal Overlay */}
      {showBiometricModal && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 animate-in fade-in duration-300">
          <div
            className="absolute inset-0 bg-black/60 backdrop-blur-md"
            onClick={() => setShowBiometricModal(false)}
          />
          <div className="relative bg-slate-800 rounded-3xl p-8 mx-4 shadow-2xl animate-in slide-in-from-top duration-500 max-w-sm w-full">
            <div className="text-center mb-6">
              <h3 className="text-white text-xl font-semibold mb-2">Face ID</h3>
              <p className="text-slate-300 text-sm">
                Authenticating as Alex Brown...
              </p>
            </div>
            <div className="flex justify-center">
              <FaceIdButton
                onAuthSuccess={handleBiometricSuccess}
                autoStart={true}
              />
            </div>
            <button
              onClick={() => setShowBiometricModal(false)}
              className="mt-6 text-slate-400 hover:text-white text-sm transition-colors w-full"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
