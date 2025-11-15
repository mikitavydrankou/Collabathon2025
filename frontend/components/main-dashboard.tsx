"use client";

import { useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Eye,
  EyeOff,
  Send,
  Plus,
  MessageCircle,
  Phone,
  FileText,
  Home,
  Newspaper,
  ShoppingCart,
  BarChart3,
  MoreVertical,
  Bot,
} from "lucide-react";
import ChatbotScreen from "./chatbot-screen";
import { apiClient } from "@/lib/api";

interface MainDashboardProps {
  onLogout: () => void;
}

const portfolioData = [
  { name: "Accounts", value: 184587.65, color: "#1a1a2e" },
  { name: "Loans", value: 45000, color: "#0f3460" },
  { name: "Avails", value: 32000, color: "#e94560" },
  { name: "Credit cards", value: 18000, color: "#c0c0c0" },
  { name: "Investment products", value: 25000, color: "#4a90e2" },
];

const currencyData = [
  { currency: "EUR", balance: 2400, percentage: "2M10" },
  { currency: "USD", balance: 4600, percentage: "465K" },
  { currency: "CNH", balance: 2290, percentage: "32K" },
  { currency: "CND", balance: 2000, percentage: "278K" },
];

const accountsData = [
  {
    date: "07.02.2022",
    name: "Current account",
    iban: "DE57 3004 6098 0123 4567 90",
    balance: 269220.37,
    type: "Accounts",
  },
  {
    date: "21.09.2022",
    name: "Current account",
    iban: "DE57 7004 6048 0197 4567 20",
    balance: 38067.0,
    type: "Accounts",
  },
];

export default function MainDashboard({ onLogout }: MainDashboardProps) {
  const [showBalance, setShowBalance] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [showChatbot, setShowChatbot] = useState(false);

  const totalBalance = 184587.65;
  const userData = apiClient.getStoredUserData();

  if (showChatbot && userData) {
    return (
      <ChatbotScreen
        userId={userData.user_id}
        onBack={() => setShowChatbot(false)}
        onConfirmPayment={(transactionData) => {
          console.log("Payment confirmed:", transactionData);
          alert("Payment confirmed! (In production, this would redirect to payment page)");
          setShowChatbot(false);
        }}
      />
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100">
      {/* Main Content */}
      <div className="max-w-md mx-auto px-4 py-6 space-y-6 pb-32">
        {/* Greeting & Balance Card */}
        <Card className="bg-gradient-to-br from-white to-slate-50 border-0 shadow-sm">
          <CardContent className="pt-6">
            <p className="text-sm text-slate-600 mb-2">
              Total balance of all accounts:
            </p>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-3xl font-bold text-slate-900">
                {showBalance
                  ? `${totalBalance.toLocaleString("de-DE", { style: "currency", currency: "EUR" })}`
                  : "••••••"}
              </h2>
              <button
                onClick={() => setShowBalance(!showBalance)}
                className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
              >
                {showBalance ? (
                  <Eye className="w-5 h-5 text-slate-600" />
                ) : (
                  <EyeOff className="w-5 h-5 text-slate-600" />
                )}
              </button>
            </div>
            <p className="text-xs text-green-600 font-medium">
              +5.345,25 EUR since last login
            </p>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-slate-100 p-1 rounded-lg">
            <TabsTrigger
              value="overview"
              className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
            >
              GPP Dashboard
            </TabsTrigger>
            <TabsTrigger
              value="financial"
              className="data-[state=active]:bg-white data-[state=active]:shadow-sm"
            >
              Financial overview
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Portfolio Pie Chart */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg">Your Portfolio</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-64 flex items-center justify-center">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={portfolioData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {portfolioData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="grid grid-cols-2 gap-3 mt-4">
                  {portfolioData.map((item, idx) => (
                    <div key={idx} className="flex items-center gap-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-xs text-slate-600">
                        {item.name}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Company Accounts */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Companies</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  { name: "Commerzbank", number: "329 1234567" },
                  { name: "GmbH", number: "329 0987654" },
                ].map((company, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                  >
                    <div>
                      <p className="font-medium text-sm text-slate-900">
                        {company.name}
                      </p>
                      <p className="text-xs text-slate-500">
                        Customer number {company.number}
                      </p>
                    </div>
                    <ChevronRightIcon className="w-4 h-4 text-slate-400" />
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Financial Tab */}
          <TabsContent value="financial" className="space-y-6">
            {/* Accounts Section */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Your Accounts</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {accountsData.map((account, idx) => (
                  <div key={idx} className="p-3 bg-slate-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs text-slate-500">
                        {account.date}
                      </span>
                      <span className="text-xs font-medium text-slate-600 bg-white px-2 py-1 rounded">
                        {account.type}
                      </span>
                    </div>
                    <p className="font-medium text-sm text-slate-900 mb-1">
                      {account.name}
                    </p>
                    <p className="text-xs text-slate-500 mb-2">
                      {account.iban}
                    </p>
                    <p className="text-lg font-bold text-slate-900">
                      {account.balance.toLocaleString("de-DE", {
                        style: "currency",
                        currency: "EUR",
                      })}
                    </p>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Currency Distribution */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">
                  Currency Distribution
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {currencyData.map((item, idx) => (
                  <div key={idx} className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-slate-900">
                        {item.currency}
                      </span>
                      <span className="text-sm text-slate-500">
                        {item.percentage}
                      </span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div
                        className="bg-yellow-400 h-2 rounded-full"
                        style={{ width: `${(item.balance / 5000) * 100}%` }}
                      />
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Quick Actions */}
        <div>
          <p className="text-sm font-semibold text-slate-900 mb-4">
            What do you need?
          </p>
          <div className="grid grid-cols-4 gap-3">
            {[
              { icon: FileText, label: "Personal Loan", onClick: () => {} },
              { icon: Bot, label: "Payment Helper", onClick: () => setShowChatbot(true) },
              { icon: Phone, label: "Call", onClick: () => {} },
              { icon: MoreVertical, label: "More", onClick: () => {} },
            ].map((action, idx) => (
              <button
                key={idx}
                onClick={action.onClick}
                className="flex flex-col items-center gap-2 p-3 rounded-lg hover:bg-slate-100 transition-colors group"
              >
                <div className="w-12 h-12 rounded-full border-2 border-slate-300 flex items-center justify-center group-hover:border-yellow-400 transition-colors">
                  <action.icon className="w-5 h-5 text-slate-600 group-hover:text-yellow-400 transition-colors" />
                </div>
                <span className="text-xs text-center text-slate-600">
                  {action.label}
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Farewell */}
        <p className="text-center text-slate-600 text-sm py-4">
          Everything done? Then we wish you a nice day.
        </p>

        {/* Logout Button */}
        <Button
          onClick={onLogout}
          className="w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-semibold py-3 rounded-lg transition-colors"
        >
          Log Out
        </Button>
      </div>

      {/* Bottom Navigation */}
      <div className="fixed bottom-0 left-0 right-0 bg-slate-900 border-t border-slate-800">
        <div className="max-w-md mx-auto px-4 py-3 flex items-center justify-around">
          {[
            { icon: Home, label: "Overview", active: true },
            { icon: Newspaper, label: "News" },
            { icon: ShoppingCart, label: "Orders" },
            { icon: BarChart3, label: "Exchange" },
            { icon: MoreVertical, label: "More" },
          ].map((item, idx) => (
            <button
              key={idx}
              className={`flex flex-col items-center gap-1 py-2 px-3 transition-colors ${item.active ? "text-yellow-400" : "text-slate-400 hover:text-slate-300"}`}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-xs">{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

function ChevronRightIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      {...props}
      xmlns="http://www.w3.org/2000/svg"
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="9 18 15 12 9 6"></polyline>
    </svg>
  );
}
