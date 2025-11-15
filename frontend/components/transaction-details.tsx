'use client'

import { ArrowLeft, Calendar, CreditCard, FileText, User, TrendingDown, TrendingUp } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

interface Transaction {
  transaction_id: number
  receiver_name: string
  receiver_bank_account: string
  amount: number
  transaction_date: string
  transaction_type: string
  transaction_text: string
  amount_before: number
  amount_after: number
}

interface TransactionDetailsProps {
  transaction: Transaction
  onBack: () => void
}

export default function TransactionDetails({ transaction, onBack }: TransactionDetailsProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('de-DE', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('de-DE', {
      style: 'currency',
      currency: 'EUR',
    }).format(amount)
  }

  const isPositive = transaction.amount > 0

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-4 py-4 sticky top-0 z-50">
        <div className="max-w-md mx-auto flex items-center gap-3">
          <button
            onClick={onBack}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-slate-700" />
          </button>
          <h1 className="text-lg font-semibold text-slate-900">Transaction Details</h1>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-md mx-auto px-4 py-6 space-y-6">
        {/* Amount Card */}
        <Card className={`border-0 shadow-sm ${isPositive ? 'bg-gradient-to-br from-green-50 to-white' : 'bg-gradient-to-br from-slate-50 to-white'}`}>
          <CardContent className="pt-6">
            <div className="flex items-center justify-center mb-2">
              {isPositive ? (
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center">
                  <TrendingUp className="w-8 h-8 text-green-600" />
                </div>
              ) : (
                <div className="w-16 h-16 rounded-full bg-slate-100 flex items-center justify-center">
                  <TrendingDown className="w-8 h-8 text-slate-600" />
                </div>
              )}
            </div>
            <div className="text-center">
              <p className="text-sm text-slate-600 mb-1">
                {isPositive ? 'Received' : 'Sent'}
              </p>
              <h2 className={`text-4xl font-bold ${isPositive ? 'text-green-600' : 'text-slate-900'}`}>
                {isPositive ? '+' : '-'}{formatCurrency(Math.abs(transaction.amount))}
              </h2>
            </div>
          </CardContent>
        </Card>

        {/* Transaction Info */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Transaction Information</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Recipient */}
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5 text-slate-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-500 mb-1">
                  {isPositive ? 'From' : 'To'}
                </p>
                <p className="font-medium text-slate-900">{transaction.receiver_name}</p>
              </div>
            </div>

            {/* Bank Account */}
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0">
                <CreditCard className="w-5 h-5 text-slate-600" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs text-slate-500 mb-1">Bank Account</p>
                <p className="font-mono text-sm text-slate-900 break-all">
                  {transaction.receiver_bank_account}
                </p>
              </div>
            </div>

            {/* Date & Time */}
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0">
                <Calendar className="w-5 h-5 text-slate-600" />
              </div>
              <div className="flex-1">
                <p className="text-xs text-slate-500 mb-1">Date & Time</p>
                <p className="font-medium text-slate-900">{formatDate(transaction.transaction_date)}</p>
              </div>
            </div>

            {/* Transaction Text */}
            {transaction.transaction_text && (
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center flex-shrink-0">
                  <FileText className="w-5 h-5 text-slate-600" />
                </div>
                <div className="flex-1">
                  <p className="text-xs text-slate-500 mb-1">Reference</p>
                  <p className="text-sm text-slate-900">{transaction.transaction_text}</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Balance Change */}
        <Card className="border-0 shadow-sm">
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Balance Change</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <span className="text-sm text-slate-600">Balance Before</span>
              <span className="font-semibold text-slate-900">{formatCurrency(transaction.amount_before)}</span>
            </div>
            <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
              <span className="text-sm text-slate-600">Balance After</span>
              <span className="font-semibold text-slate-900">{formatCurrency(transaction.amount_after)}</span>
            </div>
          </CardContent>
        </Card>

        {/* Transaction ID */}
        <div className="text-center py-4">
          <p className="text-xs text-slate-500">Transaction ID</p>
          <p className="text-sm font-mono text-slate-700 mt-1">#{transaction.transaction_id}</p>
        </div>

        {/* Action Buttons */}
        <div className="space-y-3 pb-6">
          <Button
            onClick={onBack}
            className="w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-semibold py-3 rounded-lg transition-colors"
          >
            Back to Dashboard
          </Button>
        </div>
      </div>
    </div>
  )
}
