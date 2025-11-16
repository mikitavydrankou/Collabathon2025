"use client";

import { useState, useEffect } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
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
  ArrowUpRight,
  ArrowDownLeft,
  Clock,
} from "lucide-react";
import AIHelperPopup from "@/components/ai-helper-popup";
import SendMoneyPage from "@/components/send-money-page";
import ChatbotScreen from "@/components/chatbot-screen";
import QAChatbotScreen from "@/components/qa-chatbot-screen";
import TransactionDetails from "@/components/transaction-details";
import NoConnectionPage from "@/components/no-connection-page";

interface MainDashboardProps {
  userData: any;
  onLogout: () => void;
  onNavigateTransaction?: () => void;
}

interface Transaction {
  transaction_id: number;
  receiver_name: string;
  receiver_surname: string;
  receiver_bank_account: string;
  amount: number;
  transaction_date: string;
  transaction_type: string;
  transaction_text: string;
  amount_before: number;
  amount_after: number;
  is_sent: boolean;
  transaction_posted: boolean;
}

const portfolioData = [
  { name: "Accounts", value: 184587.65, color: "#1a1a2e" },
  { name: "Loans", value: 45000, color: "#0f3460" },
  { name: "Avails", value: 32000, color: "#e94560" },
  { name: "Credit Cards", value: 18000, color: "#c0c0c0" },
  { name: "Investment Products", value: 25000, color: "#4a90e2" },
];

const currencyData = [
  { currency: "PLN", balance: 2400, percentage: "2M10" },
  { currency: "USD", balance: 4600, percentage: "465K" },
  { currency: "CNH", balance: 2290, percentage: "32K" },
  { currency: "CAD", balance: 2000, percentage: "278K" },
];

export default function MainDashboard({
  userData,
  onLogout,
  onNavigateTransaction,
}: MainDashboardProps) {
  const [showBalance, setShowBalance] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [showAIHelper, setShowAIHelper] = useState(false);
  const [currentPage, setCurrentPage] = useState<
    | "dashboard"
    | "send-money"
    | "chatbot"
    | "qa-chatbot"
    | "transaction-details"
  >("dashboard");
  const [supportLevel, setSupportLevel] = useState<"full" | "partial" | "none">(
    "none",
  );
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [selectedTransaction, setSelectedTransaction] =
    useState<Transaction | null>(null);
  const [loadingTransactions, setLoadingTransactions] = useState(false);
  const [totalBalance, setTotalBalance] = useState<number>(0);
  const [loadingBalance, setLoadingBalance] = useState(false);
  const [showNoConnection, setShowNoConnection] = useState(false);
  const [showConnectionRestored, setShowConnectionRestored] = useState(false);
  const [hasDraft, setHasDraft] = useState(false);
  const [qaInitialMessage, setQaInitialMessage] = useState<string | undefined>(
    undefined,
  );
  const [showMoreMenu, setShowMoreMenu] = useState(false);
  const [showAccessibilityPanel, setShowAccessibilityPanel] = useState(false);

  // Check for offline mode on mount
  useEffect(() => {
    const offlineMode = localStorage.getItem("offlineMode");
    const draft = localStorage.getItem("transferDraft");

    if (offlineMode === "true") {
      setShowNoConnection(true);
      setHasDraft(!!draft);
    }
  }, []);

  // Check for offline mode when returning to dashboard
  useEffect(() => {
    if (currentPage === "dashboard") {
      const offlineMode = localStorage.getItem("offlineMode");
      const draft = localStorage.getItem("transferDraft");

      console.log("🔍 Dashboard Check:", {
        offlineMode,
        hasDraft: !!draft,
      });

      if (offlineMode === "true") {
        console.log("🔴 Showing No Connection Page");
        setShowNoConnection(true);
        setHasDraft(!!draft);
      }
    }
  }, [currentPage]);

  useEffect(() => {
    if (userData?.user_id) {
      fetchTransactions();
      fetchBalance();
    }
  }, [userData]);

  const fetchBalance = async () => {
    setLoadingBalance(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/auth/user/${userData.user_id}/balance`,
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setTotalBalance(data.balance || 0);
    } catch (error) {
      console.error("Error fetching balance:", error);
      setTotalBalance(0); // Set default balance on error
    } finally {
      setLoadingBalance(false);
    }
  };

  const fetchTransactions = async () => {
    setLoadingTransactions(true);
    try {
      const response = await fetch(
        `${API_BASE_URL}/transactions/${userData.user_id}?limit=10`,
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setTransactions(data.transactions || []);
    } catch (error) {
      console.error("Error fetching transactions:", error);
      setTransactions([]); // Set empty array on error
    } finally {
      setLoadingTransactions(false);
    }
  };

  const handleAIOption = (option: string) => {
    setShowAIHelper(false);

    if (option === "qa_chatbot") {
      setCurrentPage("qa-chatbot");
    } else if (option === "chatbot") {
      setCurrentPage("chatbot");
    } else if (option === "full_support") {
      setSupportLevel("full");
      setCurrentPage("send-money");
    } else if (option === "partial_support") {
      setSupportLevel("partial");
      setCurrentPage("send-money");
    } else if (option === "no_support") {
      setSupportLevel("none");
      setCurrentPage("send-money");
    }
  };

  const handleRefreshConnection = () => {
    // User clicked refresh button on no-connection page
    console.log("🔄 Refresh clicked - starting 3s timer");
    setShowNoConnection(false);
    localStorage.removeItem("offlineMode");

    const draft = localStorage.getItem("transferDraft");
    console.log("📝 Draft exists:", !!draft);

    // Update hasDraft state
    setHasDraft(!!draft);

    // Start 3-second timer to show connection restored popup
    setTimeout(() => {
      console.log("✅ Timer complete - showing popup");
      console.log("📋 hasDraft state before showing popup:", !!draft);
      setShowConnectionRestored(true);
    }, 3000);
  };

  const handleReturnToDraft = () => {
    console.log("📄 Continuing with draft");
    setShowConnectionRestored(false);

    // Read draft to get support level
    const draftStr = localStorage.getItem("transferDraft");
    if (draftStr) {
      try {
        const draft = JSON.parse(draftStr);
        // Set support level from draft (default to "none" if not specified)
        const savedSupportLevel = draft.supportLevel || "none";
        console.log("📋 Restoring support level:", savedSupportLevel);
        setSupportLevel(savedSupportLevel);
      } catch (e) {
        console.error("Failed to parse draft:", e);
        setSupportLevel("none");
      }
    } else {
      setSupportLevel("none");
    }

    setCurrentPage("send-money");
  };

  const handleDiscardDraft = () => {
    setShowConnectionRestored(false);
    localStorage.removeItem("transferDraft");
    setHasDraft(false);
  };

  const handleTransactionClick = (transaction: Transaction) => {
    setSelectedTransaction(transaction);
    setCurrentPage("transaction-details");
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - date.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays} days ago`;

    return new Intl.DateTimeFormat("en-GB", {
      day: "2-digit",
      month: "short",
    }).format(date);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat("pl-PL", {
      style: "currency",
      currency: "PLN",
      minimumFractionDigits: 2,
    }).format(amount);
  };

  // Show No Connection page if offline mode is active
  if (showNoConnection) {
    return (
      <NoConnectionPage
        onRefresh={handleRefreshConnection}
        hasDraft={hasDraft}
      />
    );
  }

  if (currentPage === "send-money") {
    return (
      <SendMoneyPage
        onBack={() => {
          setCurrentPage("dashboard");
          fetchTransactions(); // Refresh transactions after sending money
          fetchBalance(); // Refresh balance after sending money
        }}
        supportLevel={supportLevel}
        userData={userData}
      />
    );
  }

  if (currentPage === "chatbot") {
    return (
      <ChatbotScreen
        userId={userData?.user_id || 1}
        onBack={() => setCurrentPage("dashboard")}
      />
    );
  }

  if (currentPage === "qa-chatbot") {
    return (
      <QAChatbotScreen
        onBack={() => {
          setCurrentPage("dashboard");
          setQaInitialMessage(undefined); // Clear message when going back
        }}
        onSelectTransferOption={(option) => {
          if (option === "chatbot") {
            setCurrentPage("chatbot");
          } else if (option === "full_support") {
            setSupportLevel("full");
            setCurrentPage("send-money");
          } else if (option === "partial_support") {
            setSupportLevel("partial");
            setCurrentPage("send-money");
          } else if (option === "no_support") {
            setSupportLevel("none");
            setCurrentPage("send-money");
          }
        }}
        initialMessage={qaInitialMessage}
      />
    );
  }

  if (currentPage === "transaction-details" && selectedTransaction) {
    return (
      <TransactionDetails
        transaction={selectedTransaction}
        onBack={() => setCurrentPage("dashboard")}
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
                  ? `${totalBalance.toLocaleString("pl-PL", {
                      style: "currency",
                      currency: "PLN",
                    })}`
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
              +5,345.25 zł since last login
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
              Financial Overview
            </TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Portfolio Pie Chart */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <button
                  onClick={() => setShowAIHelper(true)}
                  className="text-left w-full hover:opacity-70 transition-opacity"
                >
                  <CardTitle className="text-lg">Your Portfolio</CardTitle>
                </button>
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
                        style={{
                          backgroundColor: item.color,
                        }}
                      />
                      <span className="text-xs text-slate-600">
                        {item.name}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Recent Transactions */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    Recent Transactions
                  </CardTitle>
                  <button className="text-xs text-yellow-600 hover:text-yellow-700 font-medium">
                    View All
                  </button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {loadingTransactions ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
                  </div>
                ) : transactions.length > 0 ? (
                  transactions.slice(0, 5).map((transaction, index) => (
                    <button
                      key={`${transaction.transaction_id}-${index}`}
                      onClick={() => handleTransactionClick(transaction)}
                      className="w-full flex items-center gap-3 p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-all group"
                    >
                      <div
                        className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                          transaction.is_sent ? "bg-slate-200" : "bg-green-100"
                        }`}
                      >
                        {transaction.is_sent ? (
                          <ArrowUpRight className="w-5 h-5 text-slate-600" />
                        ) : (
                          <ArrowDownLeft className="w-5 h-5 text-green-600" />
                        )}
                      </div>
                      <div className="text-left flex-1 min-w-0">
                        <p className="font-medium text-sm text-slate-900 truncate">
                          {transaction.is_sent
                            ? transaction.receiver_name
                            : `${transaction.receiver_name} ${transaction.receiver_surname}`}
                        </p>
                        <p className="text-xs text-slate-500">
                          {formatDate(transaction.transaction_date)}
                        </p>
                        {transaction.transaction_text && (
                          <p className="text-xs text-slate-400 truncate mt-0.5">
                            {transaction.transaction_text}
                          </p>
                        )}
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p
                          className={`font-semibold text-sm ${
                            transaction.is_sent
                              ? "text-slate-900"
                              : "text-green-600"
                          }`}
                        >
                          {transaction.is_sent ? "-" : "+"}
                          {formatCurrency(Math.abs(transaction.amount))}
                        </p>
                      </div>
                    </button>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <Clock className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">
                      No transactions yet
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Company Accounts */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Quick Actions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {[
                  {
                    name: "Commerzbank",
                    number: "329 1234567",
                  },
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
            {/* All Transactions */}
            <Card className="border-0 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-base">Recent Transactions</CardTitle>
                <CardDescription className="text-xs">
                  Last 10 transactions
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {loadingTransactions ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-400"></div>
                  </div>
                ) : transactions.length > 0 ? (
                  transactions.slice(0, 10).map((transaction, index) => (
                    <button
                      key={`${transaction.transaction_id}-${index}`}
                      onClick={() => handleTransactionClick(transaction)}
                      className="w-full p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-all"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <div
                            className={`w-8 h-8 rounded-full flex items-center justify-center ${
                              transaction.is_sent
                                ? "bg-slate-200"
                                : "bg-green-100"
                            }`}
                          >
                            {transaction.is_sent ? (
                              <ArrowUpRight className="w-4 h-4 text-slate-600" />
                            ) : (
                              <ArrowDownLeft className="w-4 h-4 text-green-600" />
                            )}
                          </div>
                          <div className="text-left">
                            <p className="font-medium text-sm text-slate-900">
                              {transaction.is_sent
                                ? transaction.receiver_name
                                : `${transaction.receiver_name} ${transaction.receiver_surname}`}
                            </p>
                            <p className="text-xs text-slate-500">
                              {formatDate(transaction.transaction_date)}
                            </p>
                          </div>
                        </div>
                        <p
                          className={`font-bold text-sm ${
                            transaction.is_sent
                              ? "text-slate-900"
                              : "text-green-600"
                          }`}
                        >
                          {transaction.is_sent ? "-" : "+"}
                          {formatCurrency(Math.abs(transaction.amount))}
                        </p>
                      </div>
                      {transaction.transaction_text && (
                        <p className="text-xs text-slate-500 text-left truncate">
                          {transaction.transaction_text}
                        </p>
                      )}
                    </button>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <Clock className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                    <p className="text-sm text-slate-500">
                      No transactions yet
                    </p>
                  </div>
                )}
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
                        style={{
                          width: `${(item.balance / 5000) * 100}%`,
                        }}
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
              { icon: FileText, label: "Personal Loan" },
              { icon: MessageCircle, label: "Chat" },
              { icon: Phone, label: "Call" },
              { icon: MoreVertical, label: "More" },
            ].map((action, idx) => (
              <button
                key={idx}
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
            {
              icon: Send,
              label: "Send Money",
              action: () => {
                setSupportLevel("none");
                setCurrentPage("send-money");
              },
            },
            {
              icon: ShoppingCart,
              label: "Orders",
              action: onNavigateTransaction,
            },
            { icon: BarChart3, label: "Exchange" },
            {
              icon: MoreVertical,
              label: "More",
              action: () => setShowMoreMenu(true),
            },
          ].map((item, idx) => (
            <button
              key={idx}
              onClick={item.action}
              className={`flex flex-col items-center gap-1 py-2 px-3 transition-colors ${
                item.active
                  ? "text-yellow-400"
                  : "text-slate-400 hover:text-slate-300"
              }`}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-xs">{item.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* More Menu */}
      {showMoreMenu && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowMoreMenu(false)}
          />
          <div className="fixed bottom-20 right-4 z-50 w-64 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden animate-scale-up">
            <div className="p-3 space-y-1">
              <button
                onClick={() => {
                  setShowMoreMenu(false);
                  setShowAccessibilityPanel(true);
                }}
                className="w-full flex items-center gap-3 p-3 hover:bg-slate-50 rounded-lg transition-colors text-left group"
              >
                <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center group-hover:bg-yellow-200 transition-colors">
                  <svg
                    className="w-4 h-4 text-yellow-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                    />
                  </svg>
                </div>
                <span className="text-slate-900 font-medium text-sm">
                  Accessibility
                </span>
              </button>

              <button className="w-full flex items-center gap-3 p-3 hover:bg-slate-50 rounded-lg transition-colors text-left group">
                <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center group-hover:bg-slate-200 transition-colors">
                  <svg
                    className="w-4 h-4 text-slate-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                </div>
                <span className="text-slate-900 font-medium text-sm">
                  Settings
                </span>
              </button>

              <button className="w-full flex items-center gap-3 p-3 hover:bg-slate-50 rounded-lg transition-colors text-left group">
                <div className="w-8 h-8 rounded-full bg-slate-100 flex items-center justify-center group-hover:bg-slate-200 transition-colors">
                  <svg
                    className="w-4 h-4 text-slate-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <span className="text-slate-900 font-medium text-sm">
                  Help & Support
                </span>
              </button>
            </div>
          </div>
        </>
      )}

      {/* Accessibility Panel */}
      {showAccessibilityPanel && (
        <>
          <div
            className="fixed inset-0 z-40"
            onClick={() => setShowAccessibilityPanel(false)}
          />
          <div className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-50 w-96 max-h-[85vh] bg-white rounded-2xl shadow-2xl overflow-hidden animate-scale-up">
            <div className="sticky top-0 bg-white border-b border-slate-200 px-5 py-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-slate-900">
                Accessibility
              </h2>
              <button
                onClick={() => setShowAccessibilityPanel(false)}
                className="text-slate-400 hover:text-slate-600 transition-colors"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>

            <div className="overflow-y-auto max-h-[calc(85vh-120px)] p-5 space-y-5">
              {/* Contrast */}
              <div>
                <h3 className="text-sm font-medium text-slate-700 mb-2">
                  Contrast
                </h3>
                <div className="flex gap-2">
                  <button className="flex-1 px-3 py-2 bg-yellow-50 border-2 border-yellow-400 rounded-lg text-xs font-medium text-slate-900 transition-colors">
                    Normal
                  </button>
                  <button className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 hover:border-slate-300 rounded-lg text-xs font-medium text-slate-700 transition-colors">
                    High
                  </button>
                  <button className="flex-1 px-3 py-2 bg-slate-50 border border-slate-200 hover:border-slate-300 rounded-lg text-xs font-medium text-slate-700 transition-colors">
                    Extra
                  </button>
                </div>
              </div>

              {/* Font Size */}
              <div>
                <h3 className="text-sm font-medium text-slate-700 mb-2">
                  Font Size
                </h3>
                <div className="grid grid-cols-4 gap-2">
                  <button className="px-3 py-2 bg-slate-50 border border-slate-200 hover:border-slate-300 rounded-lg text-xs font-medium text-slate-700 transition-colors">
                    S
                  </button>
                  <button className="px-3 py-2 bg-yellow-50 border-2 border-yellow-400 rounded-lg text-sm font-medium text-slate-900 transition-colors">
                    M
                  </button>
                  <button className="px-3 py-2 bg-slate-50 border border-slate-200 hover:border-slate-300 rounded-lg text-base font-medium text-slate-700 transition-colors">
                    L
                  </button>
                  <button className="px-3 py-2 bg-slate-50 border border-slate-200 hover:border-slate-300 rounded-lg text-lg font-medium text-slate-700 transition-colors">
                    XL
                  </button>
                </div>
              </div>

              {/* Toggles */}
              <div className="space-y-3">
                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-700">Text Spacing</span>
                  <button className="w-11 h-6 bg-slate-200 rounded-full relative transition-colors">
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform"></div>
                  </button>
                </div>

                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-700">Bold Text</span>
                  <button className="w-11 h-6 bg-slate-200 rounded-full relative transition-colors">
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform"></div>
                  </button>
                </div>

                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-700">Screen Reader</span>
                  <button className="w-11 h-6 bg-slate-200 rounded-full relative transition-colors">
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform"></div>
                  </button>
                </div>

                <div className="flex items-center justify-between py-2">
                  <span className="text-sm text-slate-700">Reduce Motion</span>
                  <button className="w-11 h-6 bg-slate-200 rounded-full relative transition-colors">
                    <div className="absolute left-1 top-1 w-4 h-4 bg-white rounded-full shadow transition-transform"></div>
                  </button>
                </div>
              </div>

              {/* Color Blind Mode */}
              <div>
                <h3 className="text-sm font-medium text-slate-700 mb-2">
                  Color Blind Mode
                </h3>
                <div className="space-y-2">
                  <button className="w-full px-3 py-2 bg-yellow-50 border-2 border-yellow-400 rounded-lg text-left text-sm text-slate-900 transition-colors">
                    Off
                  </button>
                  <button className="w-full px-3 py-2 bg-slate-50 border border-slate-200 hover:border-slate-300 rounded-lg text-left text-sm text-slate-700 transition-colors">
                    Protanopia
                  </button>
                  <button className="w-full px-3 py-2 bg-slate-50 border border-slate-200 hover:border-slate-300 rounded-lg text-left text-sm text-slate-700 transition-colors">
                    Deuteranopia
                  </button>
                  <button className="w-full px-3 py-2 bg-slate-50 border border-slate-200 hover:border-slate-300 rounded-lg text-left text-sm text-slate-700 transition-colors">
                    Tritanopia
                  </button>
                </div>
              </div>
            </div>

            <div className="sticky bottom-0 bg-white border-t border-slate-200 p-4">
              <button
                onClick={() => setShowAccessibilityPanel(false)}
                className="w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-medium py-2.5 rounded-lg transition-colors text-sm"
              >
                Done
              </button>
            </div>
          </div>
        </>
      )}

      {/* AI Helper Popup */}
      {showAIHelper && (
        <AIHelperPopup
          onClose={() => setShowAIHelper(false)}
          onSelectOption={handleAIOption}
          onSendToQA={(message) => {
            setQaInitialMessage(message);
            setCurrentPage("qa-chatbot");
          }}
        />
      )}

      {/* Connection Restored Popup */}
      {showConnectionRestored && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/60 z-40"
            onClick={() => setShowConnectionRestored(false)}
          />

          {/* Popup Container */}
          <div className="fixed inset-x-0 top-20 max-w-md mx-auto z-50">
            <div className="mx-4 bg-white rounded-2xl shadow-2xl p-6 animate-in fade-in slide-in-from-top-2">
              <div className="flex flex-col items-center text-center mb-4">
                <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-4 animate-pulse">
                  <svg
                    className="w-8 h-8 text-green-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <h3 className="font-semibold text-slate-900 text-xl mb-2">
                  Connection Restored
                </h3>
                <p className="text-sm text-slate-500">You're back online!</p>
              </div>
              <p className="text-sm text-slate-600 mb-6 text-center">
                Your internet connection has been restored.
                {hasDraft && " You have a saved draft waiting to be completed."}
              </p>
              <div className="flex flex-col gap-3">
                {hasDraft && (
                  <Button
                    onClick={handleReturnToDraft}
                    className="w-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 font-semibold"
                  >
                    Continue with Draft
                  </Button>
                )}
                <Button
                  onClick={handleDiscardDraft}
                  variant="outline"
                  className="w-full border-slate-300 text-slate-700 hover:bg-slate-50"
                >
                  {hasDraft ? "Discard Draft" : "Close"}
                </Button>
              </div>
            </div>
          </div>
        </>
      )}
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
