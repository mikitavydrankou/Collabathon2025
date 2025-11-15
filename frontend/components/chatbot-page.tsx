"use client";

import { useState } from "react";
import { ArrowLeft, Send } from "lucide-react";
import { Button } from "@/components/ui/button";
import TransactionConfirmation from "./transaction-confirmation";

interface ChatbotPageProps {
  onBack: () => void;
}

interface Message {
  type: "bot" | "user";
  text: string;
}

export default function ChatbotPage({ onBack }: ChatbotPageProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      type: "bot",
      text: "Hello! I'm your Commerzbank AI assistant. I can help you send money. Would you like to make a transfer?",
    },
  ]);
  const [input, setInput] = useState("");
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [conversationStep, setConversationStep] = useState(0);

  // Transaction data
  const [accountNumber, setAccountNumber] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [amount, setAmount] = useState("");
  const [title, setTitle] = useState("");

  const handleSendMessage = () => {
    if (input.trim()) {
      const userMessage = input.trim();
      setMessages([...messages, { type: "user", text: userMessage }]);
      setInput("");

      // Process the conversation flow
      setTimeout(() => {
        processConversation(userMessage);
      }, 500);
    }
  };

  const processConversation = (userInput: string) => {
    let botResponse = "";

    switch (conversationStep) {
      case 0:
        // Initial step - ask for account number
        if (
          userInput.toLowerCase().includes("yes") ||
          userInput.toLowerCase().includes("transfer") ||
          userInput.toLowerCase().includes("send")
        ) {
          botResponse =
            "Great! Let's get started. What is the recipient's account number (IBAN)?";
          setConversationStep(1);
        } else {
          botResponse = "No problem! How else can I assist you today?";
        }
        break;

      case 1:
        // Received account number
        setAccountNumber(userInput);
        botResponse = "Perfect! What is the recipient's full name?";
        setConversationStep(2);
        break;

      case 2:
        // Received recipient name
        setRecipientName(userInput);
        botResponse =
          "Got it! How much would you like to send? (Please specify the amount in PLN)";
        setConversationStep(3);
        break;

      case 3:
        // Received amount
        const amountMatch = userInput.match(/\d+\.?\d*/);
        if (amountMatch) {
          setAmount(amountMatch[0]);
          botResponse =
            "Almost done! What would you like to use as the transfer title/description?";
          setConversationStep(4);
        } else {
          botResponse =
            "I couldn't understand the amount. Please provide a number (e.g., 100 or 250.50)";
        }
        break;

      case 4:
        // Received title
        setTitle(userInput);
        botResponse =
          "Excellent! I have all the information I need. Let me show you the confirmation page to review and complete your transfer.";
        setConversationStep(5);

        // Show confirmation after a short delay
        setTimeout(() => {
          setShowConfirmation(true);
        }, 1500);
        break;

      default:
        botResponse = "How else can I assist you with your banking needs?";
    }

    setMessages((prev) => [
      ...prev,
      {
        type: "bot",
        text: botResponse,
      },
    ]);
  };

  const handleConfirmTransaction = () => {
    // Reset everything and go back to dashboard
    setAccountNumber("");
    setRecipientName("");
    setAmount("");
    setTitle("");
    setShowConfirmation(false);
    setConversationStep(0);
    onBack();
  };

  const handleBackFromConfirmation = () => {
    setShowConfirmation(false);
    setMessages((prev) => [
      ...prev,
      {
        type: "bot",
        text: "No problem! Would you like to make any changes to your transaction? You can start over or I can help you with something else.",
      },
    ]);
    setConversationStep(0);
  };

  if (showConfirmation) {
    return (
      <TransactionConfirmation
        onBack={handleBackFromConfirmation}
        onConfirm={handleConfirmTransaction}
        accountNumber={accountNumber}
        recipientName={recipientName}
        amount={amount}
        title={title}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex flex-col">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-slate-200 px-4 py-4 z-10">
        <div className="flex items-center gap-3 max-w-md mx-auto">
          <button
            onClick={onBack}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-slate-900" />
          </button>
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-slate-900">AI Chatbot</h1>
            <p className="text-xs text-yellow-600">🤖 Full Support Mode</p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 max-w-md mx-auto w-full space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.type === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-xs p-4 rounded-2xl ${
                msg.type === "user"
                  ? "bg-yellow-400 text-slate-900"
                  : "bg-white border border-slate-200 text-slate-900 shadow-sm"
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="sticky bottom-0 bg-white border-t border-slate-200 p-4">
        <div className="max-w-md mx-auto flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === "Enter" && handleSendMessage()}
            placeholder="Type a message..."
            className="flex-1 p-3 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-yellow-400"
          />
          <Button
            onClick={handleSendMessage}
            className="bg-yellow-400 hover:bg-yellow-500 text-slate-900 p-3 flex items-center justify-center"
          >
            <Send className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
