'use client'

import { useState } from 'react'
import { ArrowLeft, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface ChatbotPageProps {
  onBack: () => void
}

export default function ChatbotPage({ onBack }: ChatbotPageProps) {
  const [messages, setMessages] = useState([
    { type: 'bot', text: 'Hello! I\'m your Commerzbank AI assistant. How can I help you today?' },
  ])
  const [input, setInput] = useState('')

  const handleSendMessage = () => {
    if (input.trim()) {
      setMessages([...messages, { type: 'user', text: input }])
      setInput('')

      setTimeout(() => {
        setMessages((prev) => [
          ...prev,
          {
            type: 'bot',
            text: 'I understand your question. How else can I assist you with your banking needs?',
          },
        ])
      }, 500)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex flex-col">
      {/* Header */}
      <div className="sticky top-0 bg-white border-b border-slate-200 px-4 py-4 z-10">
        <div className="flex items-center gap-3 max-w-md mx-auto">
          <button onClick={onBack} className="p-2 hover:bg-slate-100 rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5 text-slate-900" />
          </button>
          <h1 className="text-lg font-semibold text-slate-900">AI Chatbot</h1>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 max-w-md mx-auto w-full space-y-4">
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-xs p-4 rounded-2xl ${
                msg.type === 'user'
                  ? 'bg-yellow-400 text-slate-900'
                  : 'bg-white border border-slate-200 text-slate-900'
              }`}
            >
              <p className="text-sm">{msg.text}</p>
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
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
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
  )
}
