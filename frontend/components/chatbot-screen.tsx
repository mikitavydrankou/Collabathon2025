"use client";

import { useState, useEffect, useRef } from "react";
import { ArrowLeft, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import { apiClient } from "@/lib/api";

interface ChatbotScreenProps {
  userId: number;
  onBack: () => void;
  onConfirmPayment?: (transactionData: any) => void;
}

interface ChatMessage {
  id: string;
  sender: "user" | "bot";
  message: string;
  buttons?: string[];
  suggestion?: any;
  showConfirmPayment?: boolean;
  validationProblems?: string[];
}

export default function ChatbotScreen({ userId, onBack, onConfirmPayment }: ChatbotScreenProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState<string>("initial");
  const [transactionData, setTransactionData] = useState<any>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageIdCounter = useRef(0);

  // Generate unique message ID
  const generateMessageId = () => {
    messageIdCounter.current += 1;
    return `${Date.now()}-${messageIdCounter.current}-${Math.random().toString(36).slice(2, 11)}`;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    startChat();
  }, []);

  const startChat = async () => {
    setIsLoading(true);
    try {
      const response = await apiClient.startChatbot(userId);
      setSessionId(response.session_id);
      addMessage({
        id: generateMessageId(),
        sender: "bot",
        message: response.message,
        buttons: response.buttons,
      });
    } catch (error: any) {
      addMessage({
        id: generateMessageId(),
        sender: "bot",
        message: `Error: ${error.message}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const addMessage = (message: ChatMessage) => {
    setMessages((prev) => [...prev, message]);
  };

  const handleButtonClick = async (action: string) => {
    if (!sessionId) return;

    addMessage({
      id: generateMessageId(),
      sender: "user",
      message: action.charAt(0).toUpperCase() + action.slice(1),
    });

    setIsLoading(true);
    try {
      const response = await apiClient.sendChatbotMessage({
        session_id: sessionId,
        user_id: userId,
        action,
      });

      handleBotResponse(response);
    } catch (error: any) {
      addMessage({
        id: generateMessageId(),
        sender: "bot",
        message: `Error: ${error.message}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim() || !sessionId) return;

    const userMessage = inputValue.trim();
    setInputValue("");

    addMessage({
      id: generateMessageId(),
      sender: "user",
      message: userMessage,
    });

    setIsLoading(true);
    try {
      const response = await apiClient.sendChatbotMessage({
        session_id: sessionId,
        user_id: userId,
        message: userMessage,
      });

      handleBotResponse(response);
    } catch (error: any) {
      addMessage({
        id: generateMessageId(),
        sender: "bot",
        message: `Error: ${error.message}`,
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleBotResponse = (response: any) => {
    setCurrentStage(response.stage);
    setTransactionData(response.transaction_data);

    addMessage({
      id: generateMessageId(),
      sender: "bot",
      message: response.message,
      buttons: response.buttons,
      suggestion: response.suggestion,
      showConfirmPayment: response.show_confirm_payment,
      validationProblems: response.validation_problems,
    });
  };

  const handleConfirmPayment = () => {
    if (onConfirmPayment && transactionData) {
      onConfirmPayment(transactionData);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-700 text-white px-4 py-4 shadow-lg">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
          >
            <ArrowLeft size={24} />
          </button>
          <div>
            <h1 className="text-xl font-bold">Payment Assistant</h1>
            <p className="text-sm text-slate-300">Here to help you</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
        {messages.map((msg) => (
          <div key={msg.id}>
            {/* Message bubble */}
            <div
              className={`flex ${msg.sender === "user" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                  msg.sender === "user"
                    ? "bg-yellow-400 text-slate-900"
                    : "bg-white text-slate-900 shadow-md border border-slate-200"
                }`}
              >
                <p className="text-sm whitespace-pre-line">{msg.message}</p>
              </div>
            </div>

            {/* Suggestion card */}
            {msg.suggestion && (
              <div className="mt-3 ml-2">
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 max-w-[80%]">
                  <div className="text-xs text-blue-600 font-semibold mb-2">
                    SUGGESTED PAYMENT
                  </div>
                  <div className="space-y-1 text-sm">
                    <p>
                      <span className="font-medium">To:</span>{" "}
                      {msg.suggestion.recipient_name}
                    </p>
                    <p>
                      <span className="font-medium">Account:</span>{" "}
                      {msg.suggestion.bank_account}
                    </p>
                    <p>
                      <span className="font-medium">Amount:</span> €
                      {msg.suggestion.amount.toFixed(2)}
                    </p>
                    <p>
                      <span className="font-medium">Description:</span>{" "}
                      {msg.suggestion.title}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* Validation problems */}
            {msg.validationProblems && msg.validationProblems.length > 0 && (
              <div className="mt-3 ml-2">
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 max-w-[80%]">
                  <div className="text-xs text-amber-600 font-semibold mb-2">
                    ISSUES FOUND
                  </div>
                  <ul className="space-y-1 text-sm text-amber-900">
                    {msg.validationProblems.map((problem, idx) => (
                      <li key={idx}>• {problem}</li>
                    ))}
                  </ul>
                </div>
              </div>
            )}

            {/* Button options */}
            {msg.buttons && msg.buttons.length > 0 && (
              <div className="mt-3 flex gap-2 flex-wrap ml-2">
                {msg.buttons.map((btn) => (
                  <Button
                    key={btn}
                    onClick={() => handleButtonClick(btn)}
                    disabled={isLoading}
                    className="bg-slate-700 hover:bg-slate-800 text-white rounded-full px-6 py-2 text-sm font-medium shadow-md"
                  >
                    {btn.charAt(0).toUpperCase() + btn.slice(1)}
                  </Button>
                ))}
              </div>
            )}

            {/* Confirm payment button */}
            {msg.showConfirmPayment && (
              <div className="mt-3 ml-2">
                <Button
                  onClick={handleConfirmPayment}
                  className="bg-green-600 hover:bg-green-700 text-white rounded-full px-8 py-3 text-base font-bold shadow-lg"
                >
                  Confirm Payment
                </Button>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-white rounded-2xl px-4 py-3 shadow-md border border-slate-200">
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></div>
                <div
                  className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.1s" }}
                ></div>
                <div
                  className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                ></div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="bg-white border-t border-slate-200 px-4 py-4">
        <div className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
            disabled={isLoading}
            className="flex-1 px-4 py-3 border-2 border-slate-300 rounded-full focus:outline-none focus:border-slate-700 focus:ring-2 focus:ring-slate-200 transition-all text-slate-900 placeholder:text-slate-400 disabled:bg-slate-100"
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputValue.trim() || isLoading}
            className="bg-yellow-400 hover:bg-yellow-500 text-slate-900 rounded-full p-3 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
          >
            <Send size={20} />
          </button>
        </div>
      </div>
    </div>
  );
}
