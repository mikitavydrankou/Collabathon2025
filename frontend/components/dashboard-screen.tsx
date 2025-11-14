'use client'

import { useState } from 'react'
import { Menu, LogOut, Send, Eye, EyeOff, MoreVertical } from 'lucide-react'
import { Button } from '@/components/ui/button'
import AccountCard from '@/components/account-card'
import BottomNavigation from '@/components/bottom-navigation'

interface DashboardScreenProps {
  onLogout: () => void
}

const ACCOUNTS = [
  {
    id: 1,
    name: 'Girokonto Mein',
    balance: 2768.50,
    currency: 'EUR',
    icon: '💳',
    color: 'bg-yellow-400',
  },
  {
    id: 2,
    name: 'Sparkonto',
    balance: 12450.75,
    currency: 'EUR',
    icon: '🏦',
    color: 'bg-blue-500',
  },
  {
    id: 3,
    name: 'Geschäftskonto',
    balance: -340.20,
    currency: 'EUR',
    icon: '📊',
    color: 'bg-green-500',
  },
]

const TRANSACTIONS = [
  {
    id: 1,
    description: 'Supermarkt Müller',
    amount: -45.99,
    date: 'Heute',
    type: 'shopping',
  },
  {
    id: 2,
    description: 'Gehalt November',
    amount: 3200.00,
    date: 'Gestern',
    type: 'income',
  },
  {
    id: 3,
    description: 'Mietzahlung',
    amount: -1200.00,
    date: '12. Nov',
    type: 'transfer',
  },
]

export default function DashboardScreen({ onLogout }: DashboardScreenProps) {
  const [hideBalance, setHideBalance] = useState(false)
  const [activeNav, setActiveNav] = useState('overview')

  const totalBalance = ACCOUNTS.reduce((sum, acc) => sum + acc.balance, 0)

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-4 py-4 sticky top-0 z-50">
        <div className="flex items-center justify-between mb-4">
          <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <Menu size={24} className="text-foreground" />
          </button>
          <div className="text-center flex-1">
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center mx-auto">
              <span className="text-accent font-bold text-sm">C</span>
            </div>
          </div>
          <button onClick={onLogout} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
            <LogOut size={20} className="text-foreground" />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto pb-24 px-4 py-4">
        {/* Total Balance Card */}
        <div className="bg-gradient-to-br from-accent to-accent/80 text-white rounded-2xl p-6 mb-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium opacity-90">Gesamtsaldo aller Konten</h2>
            <button
              onClick={() => setHideBalance(!hideBalance)}
              className="p-1 hover:bg-white/20 rounded-lg transition-colors"
            >
              {hideBalance ? <EyeOff size={20} /> : <Eye size={20} />}
            </button>
          </div>
          <div className="flex items-baseline gap-2 mb-6">
            <span className="text-4xl font-bold">
              {hideBalance ? '•••' : `€ ${totalBalance.toLocaleString('de-DE', { minimumFractionDigits: 2 })}`}
            </span>
          </div>
          <div className="flex gap-3">
            <Button className="flex-1 bg-white text-accent hover:bg-gray-100 font-semibold py-2 rounded-full">
              <Send size={18} className="mr-2" />
              Überweisen
            </Button>
            <Button className="flex-1 bg-white/20 text-white hover:bg-white/30 font-semibold py-2 rounded-full border border-white/30">
              Mehr
            </Button>
          </div>
        </div>

        {/* Accounts Section */}
        <div className="mb-6">
          <h3 className="text-sm font-semibold text-gray-600 mb-3 px-1">Meine Konten</h3>
          <div className="space-y-3">
            {ACCOUNTS.map((account) => (
              <AccountCard key={account.id} account={account} hideBalance={hideBalance} />
            ))}
          </div>
        </div>

        {/* Transactions Section */}
        <div>
          <h3 className="text-sm font-semibold text-gray-600 mb-3 px-1">Transaktionen</h3>
          <div className="space-y-2 bg-white rounded-xl overflow-hidden">
            {TRANSACTIONS.map((transaction, index) => (
              <div
                key={transaction.id}
                className={`flex items-center justify-between p-4 ${
                  index !== TRANSACTIONS.length - 1 ? 'border-b border-gray-100' : ''
                }`}
              >
                <div className="flex-1">
                  <p className="text-sm font-medium text-foreground">{transaction.description}</p>
                  <p className="text-xs text-gray-500">{transaction.date}</p>
                </div>
                <span
                  className={`text-sm font-semibold ${
                    transaction.amount > 0 ? 'text-green-600' : 'text-foreground'
                  }`}
                >
                  {transaction.amount > 0 ? '+' : ''}€ {Math.abs(transaction.amount).toLocaleString('de-DE', {
                    minimumFractionDigits: 2,
                  })}
                </span>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Bottom Navigation */}
      <BottomNavigation activeNav={activeNav} setActiveNav={setActiveNav} />
    </div>
  )
}
