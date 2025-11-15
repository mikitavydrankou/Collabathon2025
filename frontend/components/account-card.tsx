"use client";

import { MoreVertical } from "lucide-react";

interface Account {
  id: number;
  name: string;
  balance: number;
  currency: string;
  icon: string;
  color: string;
}

interface AccountCardProps {
  account: Account;
  hideBalance: boolean;
}

export default function AccountCard({
  account,
  hideBalance,
}: AccountCardProps) {
  return (
    <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:shadow-md transition-shadow cursor-pointer">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-3">
          <div
            className={`${account.color} w-10 h-10 rounded-lg flex items-center justify-center text-lg`}
          >
            {account.icon}
          </div>
          <div>
            <p className="text-sm font-medium text-foreground">
              {account.name}
            </p>
            <p className="text-xs text-gray-500">Active</p>
          </div>
        </div>
        <button className="p-1 hover:bg-gray-100 rounded-lg transition-colors">
          <MoreVertical size={16} className="text-gray-400" />
        </button>
      </div>
      <div className="flex items-baseline justify-between">
        <span className="text-xl font-bold text-foreground">
          {hideBalance
            ? "•••"
            : `${account.balance.toLocaleString("pl-PL", { minimumFractionDigits: 2 })} zł`}
        </span>
        <span className="text-xs text-gray-500">{account.currency}</span>
      </div>
    </div>
  );
}
