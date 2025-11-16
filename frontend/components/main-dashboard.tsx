"use client";

import { useState, useEffect } from "react";
import { PieChart, Pie, Cell, ResponsiveContainer } from "recharts";
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
  HelpCircle,
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
        `http://localhost:8000/auth/user/${userData.user_id}/balance`,
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
        `http://localhost:8000/transactions/${userData.user_id}?limit=10`,
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
            { icon: MoreVertical, label: "More" },
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
      <button
        onClick={() => setShowAIHelper(true)}
        className="fixed bottom-24 right-4 w-14 h-14 rounded-full bg-yellow-400 hover:bg-yellow-500 text-slate-900 flex items-center justify-center shadow-lg transition-all hover:scale-110 z-30"
        title="Get help from AI"
      >
        <HelpCircle className="w-6 h-6" />
      </button>
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
