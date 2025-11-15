'use client'

import { useState } from 'react'
import { X, Send, Loader, MessageSquare, HelpCircle, ZapOff, Check, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface TransactionFormData {
  accountNumber: string
  recipientName: string
  amount: string
  title: string
}

type SupportLevel = 'none' | 'full' | 'partial' | null
type FormStep = 'account' | 'name' | 'amount' | 'title'

export default function UnifiedTransactionFlow() {
  const [showHelp, setShowHelp] = useState(true)
  const [helpStep, setHelpStep] = useState<'popup' | 'input' | 'loading' | 'options'>('popup')
  const [supportLevel, setSupportLevel] = useState<SupportLevel>(null)
  const [formData, setFormData] = useState<TransactionFormData>({
    accountNumber: '',
    recipientName: '',
    amount: '',
    title: '',
  })
  const [activeField, setActiveField] = useState<FormStep | null>(null)
  const [completedFields, setCompletedFields] = useState<Set<FormStep>>(new Set())
  const [message, setMessage] = useState('')
  const [showCelebration, setShowCelebration] = useState(false)

  const fieldConfigs: Record<FormStep, { label: string; placeholder: string; hint: string; fullHint: string }> = {
    account: {
      label: 'Account Number',
      placeholder: 'DE89 3704 0044 0532 0130 00',
      hint: 'Enter the recipient account number (IBAN)',
      fullHint: 'Enter the recipient account number (IBAN)',
    },
    name: {
      label: 'Recipient Name',
      placeholder: 'John Doe',
      hint: 'Who are you sending money to?',
      fullHint: 'Who are you sending money to?',
    },
    amount: {
      label: 'Amount',
      placeholder: '100.00',
      hint: 'How much do you want to send?',
      fullHint: 'How much do you want to send?',
    },
    title: {
      label: 'Transfer Title',
      placeholder: 'Monthly Payment',
      hint: 'What is this transfer for?',
      fullHint: 'What is this transfer for?',
    },
  }

  const handleAcceptHelp = () => {
    setHelpStep('input')
  }

  const handleSendMessage = () => {
    if (message.trim()) {
      setHelpStep('loading')
      setTimeout(() => {
        setHelpStep('options')
      }, 2000)
    }
  }

  const handleSelectSupport = (level: 'chatbot' | 'full_support' | 'partial_support' | 'no_support') => {
    setShowHelp(false)
    if (level === 'chatbot') {
      alert('Открыть страницу чата')
    } else if (level === 'full_support') {
      setSupportLevel('full')
      setActiveField('account')
    } else if (level === 'partial_support') {
      setSupportLevel('partial')
    } else if (level === 'no_support') {
      setSupportLevel('none')
    }
  }

  const handleFieldChange = (field: FormStep, value: string) => {
    setFormData({ ...formData, [field]: value })

    if (value.trim()) {
      const newCompleted = new Set(completedFields)
      newCompleted.add(field)
      setCompletedFields(newCompleted)
    }
  }

  const handleFieldFocus = (field: FormStep) => {
    if (supportLevel === 'full') {
      setActiveField(field)
    }
  }

  const handleFieldBlur = () => {
    if (supportLevel === 'full') {
      setActiveField(null)
    }
  }

  const handleSubmit = () => {
    setShowCelebration(true)
    setTimeout(() => {
      alert(`Отправка: ${JSON.stringify(formData)}`)
    }, 1500)
  }

  const isFormValid = Object.values(formData).every(val => val.trim() !== '')

  // Helper popup
  if (showHelp) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 flex items-center justify-center p-4">
        <div className="fixed inset-0 bg-black/40 z-40" />

        <div className="relative z-50 w-full max-w-sm">
          {helpStep === 'popup' && (
            <div className="bg-white rounded-3xl shadow-2xl p-8 animate-in fade-in slide-in-from-top-4 space-y-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-yellow-300 to-yellow-500 flex items-center justify-center shadow-lg animate-pulse">
                    <MessageSquare className="w-7 h-7 text-slate-900" />
                  </div>
                  <div>
                    <h3 className="font-bold text-xl text-slate-900">Do you need help?</h3>
                    <p className="text-xs text-slate-500 font-medium">AI Assistant</p>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setShowHelp(false)
                    setSupportLevel('none')
                  }}
                  className="p-2 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
              </div>
              <p className="text-sm text-slate-600">
                I can guide you through the transfer process. Choose how much help you need!
              </p>
              <div className="flex gap-3">
                <Button
                  onClick={() => {
                    setShowHelp(false)
                    setSupportLevel('none')
                  }}
                  variant="outline"
                  className="flex-1 border-2 border-slate-300 text-slate-700 hover:bg-slate-50 font-semibold"
                >
                  Skip
                </Button>
                <Button
                  onClick={handleAcceptHelp}
                  className="flex-1 bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-bold shadow-lg"
                >
                  Help me
                </Button>
              </div>
            </div>
          )}

          {helpStep === 'input' && (
            <div className="bg-white rounded-3xl shadow-2xl p-8 animate-in fade-in slide-in-from-top-4 space-y-4">
              <div className="flex items-center gap-3 mb-4">
                <button
                  onClick={() => setHelpStep('popup')}
                  className="p-2 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400" />
                </button>
                <h3 className="font-bold text-slate-900 flex-1">Tell me what you need</h3>
              </div>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask me anything about transfers..."
                className="w-full p-4 border-2 border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent bg-white text-slate-900 placeholder-slate-400 resize-none"
                rows={3}
              />
              <Button
                onClick={handleSendMessage}
                disabled={!message.trim()}
                className="w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-bold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send className="w-4 h-4" />
                Send
              </Button>
            </div>
          )}

          {helpStep === 'loading' && (
            <div className="bg-white rounded-3xl shadow-2xl p-8 animate-in fade-in slide-in-from-top-4">
              <div className="flex flex-col items-center justify-center py-8 gap-4">
                <Loader className="w-8 h-8 text-yellow-400 animate-spin" />
                <p className="text-sm text-slate-600 font-medium">Analyzing your request...</p>
              </div>
            </div>
          )}

          {helpStep === 'options' && (
            <div className="bg-white rounded-3xl shadow-2xl p-8 animate-in fade-in slide-in-from-top-4 space-y-3">
              <h3 className="font-bold text-slate-900 mb-2 text-lg">Choose your support level:</h3>
              <p className="text-sm text-slate-600 mb-4">How would you like to proceed?</p>

              {[
                {
                  label: 'Chatbot',
                  action: 'chatbot',
                  icon: MessageSquare,
                  desc: 'Chat with AI',
                  color: 'from-blue-50 to-blue-100 border-blue-200 hover:from-blue-100 hover:to-blue-150',
                },
                {
                  label: 'Full Support',
                  action: 'full_support',
                  icon: HelpCircle,
                  desc: 'Step-by-step with arrows',
                  color: 'from-yellow-50 to-amber-100 border-yellow-200 hover:from-yellow-100 hover:to-amber-150',
                },
                {
                  label: 'Partial Support',
                  action: 'partial_support',
                  icon: HelpCircle,
                  desc: 'Light tips as you fill',
                  color: 'from-green-50 to-emerald-100 border-green-200 hover:from-green-100 hover:to-emerald-150',
                },
                {
                  label: 'No Support',
                  action: 'no_support',
                  icon: ZapOff,
                  desc: 'Just let me send',
                  color: 'from-slate-50 to-slate-100 border-slate-200 hover:from-slate-100 hover:to-slate-150',
                },
              ].map((option) => {
                const Icon = option.icon
                return (
                  <button
                    key={option.action}
                    onClick={() =>
                      handleSelectSupport(
                        option.action as 'chatbot' | 'full_support' | 'partial_support' | 'no_support'
                      )
                    }
                    className={`w-full p-4 text-left rounded-2xl transition-all border-2 flex items-center gap-4 bg-gradient-to-br ${option.color} font-medium`}
                  >
                    <Icon className="w-6 h-6 text-yellow-500 flex-shrink-0" />
                    <div className="flex-1">
                      <p className="text-sm font-bold text-slate-900">{option.label}</p>
                      <p className="text-xs text-slate-600">{option.desc}</p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-slate-400 flex-shrink-0" />
                  </button>
                )
              })}

              <Button
                onClick={() => {
                  setShowHelp(false)
                  setSupportLevel('none')
                }}
                variant="outline"
                className="w-full mt-6 border-2 border-slate-300 text-slate-700 font-semibold"
              >
                Close
              </Button>
            </div>
          )}
        </div>
      </div>
    )
  }

  // Main transaction form
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 pb-24">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-5 sticky top-0 z-10 shadow-sm">
        <h1 className="text-2xl font-bold text-slate-900">Send Money</h1>
        <div className="flex items-center gap-2 mt-2">
          <div className="w-2 h-2 rounded-full bg-yellow-400" />
          <p className="text-sm text-slate-600 font-medium">
            {supportLevel === 'full' && '🎯 Full guided experience'}
            {supportLevel === 'partial' && '💡 Tips enabled'}
            {supportLevel === 'none' && 'Fill in the details below'}
          </p>
        </div>
      </div>

      {/* Form */}
      <div className="px-4 py-6 space-y-5 max-w-2xl mx-auto">
        {/* Account Number Field */}
        <div className="relative">
          {supportLevel === 'full' && activeField === 'account' && (
            <div className="absolute -top-20 left-1/2 transform -translate-x-1/2 z-20 animate-in fade-in slide-in-from-top-2">
              <svg className="w-12 h-20 text-yellow-400 drop-shadow-lg" viewBox="0 0 24 80" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 0 L12 60 M8 50 L12 60 L16 50" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="bg-yellow-400 text-slate-900 font-bold px-4 py-2 rounded-lg text-sm whitespace-nowrap shadow-xl text-center">
                Enter account number ↓
              </div>
            </div>
          )}

          <div className={`guided-field ${supportLevel === 'full' && activeField === 'account' ? 'active' : ''} ${supportLevel === 'full' && completedFields.has('account') ? 'ring-4 ring-green-300 ring-offset-2' : ''}`}>
            <label className="block text-sm font-bold text-slate-900 mb-2 flex items-center gap-2">
              {fieldConfigs.account.label}
              {completedFields.has('account') && (
                <Check className="w-5 h-5 text-green-500 bg-green-100 rounded-full p-0.5" />
              )}
            </label>
            <input
              type="text"
              value={formData.accountNumber}
              onChange={(e) => handleFieldChange('account', e.target.value)}
              onFocus={() => handleFieldFocus('account')}
              onBlur={handleFieldBlur}
              placeholder={fieldConfigs.account.placeholder}
              className="w-full p-4 border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent bg-white text-slate-900 placeholder-slate-400 transition-all text-base"
            />
            {supportLevel === 'partial' && !completedFields.has('account') && (
              <p className="text-xs text-yellow-600 mt-2 font-medium">💡 {fieldConfigs.account.hint}</p>
            )}
          </div>
        </div>

        {/* Recipient Name Field */}
        <div className="relative">
          {supportLevel === 'full' && activeField === 'name' && (
            <div className="absolute -top-20 left-1/2 transform -translate-x-1/2 z-20 animate-in fade-in slide-in-from-top-2">
              <svg className="w-12 h-20 text-yellow-400 drop-shadow-lg" viewBox="0 0 24 80" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 0 L12 60 M8 50 L12 60 L16 50" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="bg-yellow-400 text-slate-900 font-bold px-4 py-2 rounded-lg text-sm whitespace-nowrap shadow-xl text-center">
                Who receives it? ↓
              </div>
            </div>
          )}

          <div className={`guided-field ${supportLevel === 'full' && activeField === 'name' ? 'active' : ''} ${supportLevel === 'full' && completedFields.has('name') ? 'ring-4 ring-green-300 ring-offset-2' : ''}`}>
            <label className="block text-sm font-bold text-slate-900 mb-2 flex items-center gap-2">
              {fieldConfigs.name.label}
              {completedFields.has('name') && (
                <Check className="w-5 h-5 text-green-500 bg-green-100 rounded-full p-0.5" />
              )}
            </label>
            <input
              type="text"
              value={formData.recipientName}
              onChange={(e) => handleFieldChange('name', e.target.value)}
              onFocus={() => handleFieldFocus('name')}
              onBlur={handleFieldBlur}
              placeholder={fieldConfigs.name.placeholder}
              className="w-full p-4 border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent bg-white text-slate-900 placeholder-slate-400 transition-all text-base"
            />
            {supportLevel === 'partial' && !completedFields.has('name') && (
              <p className="text-xs text-yellow-600 mt-2 font-medium">💡 {fieldConfigs.name.hint}</p>
            )}
          </div>
        </div>

        {/* Amount Field */}
        <div className="relative">
          {supportLevel === 'full' && activeField === 'amount' && (
            <div className="absolute -top-20 left-1/2 transform -translate-x-1/2 z-20 animate-in fade-in slide-in-from-top-2">
              <svg className="w-12 h-20 text-yellow-400 drop-shadow-lg" viewBox="0 0 24 80" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 0 L12 60 M8 50 L12 60 L16 50" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="bg-yellow-400 text-slate-900 font-bold px-4 py-2 rounded-lg text-sm whitespace-nowrap shadow-xl text-center">
                How much money? ↓
              </div>
            </div>
          )}

          <div className={`guided-field ${supportLevel === 'full' && activeField === 'amount' ? 'active' : ''} ${supportLevel === 'full' && completedFields.has('amount') ? 'ring-4 ring-green-300 ring-offset-2' : ''}`}>
            <label className="block text-sm font-bold text-slate-900 mb-2 flex items-center gap-2">
              {fieldConfigs.amount.label}
              {completedFields.has('amount') && (
                <Check className="w-5 h-5 text-green-500 bg-green-100 rounded-full p-0.5" />
              )}
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.amount}
              onChange={(e) => handleFieldChange('amount', e.target.value)}
              onFocus={() => handleFieldFocus('amount')}
              onBlur={handleFieldBlur}
              placeholder={fieldConfigs.amount.placeholder}
              className="w-full p-4 border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent bg-white text-slate-900 placeholder-slate-400 transition-all text-base"
            />
            {supportLevel === 'partial' && !completedFields.has('amount') && (
              <p className="text-xs text-yellow-600 mt-2 font-medium">💡 {fieldConfigs.amount.hint}</p>
            )}
          </div>
        </div>

        {/* Transfer Title Field */}
        <div className="relative">
          {supportLevel === 'full' && activeField === 'title' && (
            <div className="absolute -top-20 left-1/2 transform -translate-x-1/2 z-20 animate-in fade-in slide-in-from-top-2">
              <svg className="w-12 h-20 text-yellow-400 drop-shadow-lg" viewBox="0 0 24 80" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 0 L12 60 M8 50 L12 60 L16 50" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
              <div className="bg-yellow-400 text-slate-900 font-bold px-4 py-2 rounded-lg text-sm whitespace-nowrap shadow-xl text-center">
                What's this for? ↓
              </div>
            </div>
          )}

          <div className={`guided-field ${supportLevel === 'full' && activeField === 'title' ? 'active' : ''} ${supportLevel === 'full' && completedFields.has('title') ? 'ring-4 ring-green-300 ring-offset-2' : ''}`}>
            <label className="block text-sm font-bold text-slate-900 mb-2 flex items-center gap-2">
              {fieldConfigs.title.label}
              {completedFields.has('title') && (
                <Check className="w-5 h-5 text-green-500 bg-green-100 rounded-full p-0.5" />
              )}
            </label>
            <input
              type="text"
              value={formData.title}
              onChange={(e) => handleFieldChange('title', e.target.value)}
              onFocus={() => handleFieldFocus('title')}
              onBlur={handleFieldBlur}
              placeholder={fieldConfigs.title.placeholder}
              className="w-full p-4 border-2 border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-yellow-400 focus:border-transparent bg-white text-slate-900 placeholder-slate-400 transition-all text-base"
            />
            {supportLevel === 'partial' && !completedFields.has('title') && (
              <p className="text-xs text-yellow-600 mt-2 font-medium">💡 {fieldConfigs.title.hint}</p>
            )}
          </div>
        </div>

        {/* Completion Message for Full Support */}
        {supportLevel === 'full' && completedFields.size === 4 && !showCelebration && (
          <div className="bg-gradient-to-r from-green-50 to-emerald-50 border-2 border-green-200 rounded-2xl p-6 text-center animate-in fade-in slide-in-from-bottom-2 space-y-2">
            <p className="text-4xl">🎉</p>
            <p className="text-sm font-bold text-green-900">Perfect! All fields completed!</p>
            <p className="text-xs text-green-700">Ready to send your transfer</p>
          </div>
        )}

        {/* Celebration Animation */}
        {showCelebration && (
          <div className="fixed inset-0 z-50 flex items-center justify-center pointer-events-none">
            <div className="text-7xl animate-bounce">🎉</div>
            <div className="absolute text-6xl animate-bounce" style={{ left: '20%', top: '30%', animationDelay: '0.1s' }}>✨</div>
            <div className="absolute text-6xl animate-bounce" style={{ right: '20%', top: '30%', animationDelay: '0.2s' }}>🎊</div>
          </div>
        )}

        {/* Submit Button */}
        <div className="pt-4 space-y-3">
          <Button
            onClick={handleSubmit}
            disabled={!isFormValid}
            className="w-full bg-gradient-to-r from-yellow-400 to-yellow-500 hover:from-yellow-500 hover:to-yellow-600 disabled:from-slate-300 disabled:to-slate-300 text-slate-900 font-bold py-5 text-lg rounded-2xl disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
          >
            Send Money
          </Button>
          <Button
            onClick={() => {
              setSupportLevel(null)
              setShowHelp(true)
              setHelpStep('popup')
              setFormData({ accountNumber: '', recipientName: '', amount: '', title: '' })
              setCompletedFields(new Set())
            }}
            variant="outline"
            className="w-full border-2 border-slate-300 text-slate-700 font-semibold py-5 rounded-2xl hover:bg-slate-100"
          >
            Back to Help
          </Button>
        </div>
      </div>
    </div>
  )
}
