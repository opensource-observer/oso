"use client";

import React, { useEffect, useState } from "react";
import { useAuth } from "../../lib/hooks/useAuth";
import {
  CreditsService,
  CreditTransaction,
  UserCredits,
} from "../../lib/services/credits";
import { useRouter } from "next/navigation";
import { logger } from "../../lib/logger";

// TODO(jabolo): Migrate this to Plasmic
export default function BillingPage() {
  const { user, loading, isAuthenticated } = useAuth();
  const router = useRouter();
  const [credits, setCredits] = useState<UserCredits | null>(null);
  const [transactions, setTransactions] = useState<CreditTransaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push("/");
    }
  }, [loading, isAuthenticated, router]);

  useEffect(() => {
    const fetchData = async () => {
      if (isAuthenticated && user.role !== "anonymous") {
        setIsLoading(true);
        try {
          const [userCredits, creditTransactions] = await Promise.all([
            CreditsService.getUserCredits(user.userId),
            CreditsService.getCreditTransactions(user.userId),
          ]);

          setCredits(userCredits);
          setTransactions(creditTransactions);
        } catch (error) {
          logger.error("Error fetching billing data:", error);
        } finally {
          setIsLoading(false);
        }
      }
    };

    void fetchData();
  }, [isAuthenticated, user]);

  if (loading || isLoading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-8">Billing & Credits</h1>

      <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Credit Balance</h2>
        <div className="text-5xl font-bold text-blue-600 mb-4">
          {credits?.credits_balance || 0}
        </div>
        <p className="text-gray-600">
          Credits are used for API calls to our services
        </p>
      </div>

      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-xl font-semibold mb-4">Transaction History</h2>

        {transactions.length === 0 ? (
          <p className="text-gray-600">No transactions yet</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full bg-white">
              <thead>
                <tr className="bg-gray-100 text-gray-700 uppercase text-sm leading-normal">
                  <th className="py-3 px-6 text-left">Date</th>
                  <th className="py-3 px-6 text-left">Type</th>
                  <th className="py-3 px-6 text-right">Amount</th>
                  <th className="py-3 px-6 text-left">API Endpoint</th>
                </tr>
              </thead>
              <tbody className="text-gray-600 text-sm">
                {transactions.map((transaction) => (
                  <tr
                    key={transaction.id}
                    className="border-b border-gray-200 hover:bg-gray-50"
                  >
                    <td className="py-3 px-6 text-left whitespace-nowrap">
                      {new Date(transaction.created_at).toLocaleString()}
                    </td>
                    <td className="py-3 px-6 text-left">
                      {transaction.transaction_type.replace(/_/g, " ")}
                    </td>
                    <td
                      className={`py-3 px-6 text-right font-bold ${transaction.amount > 0 ? "text-green-600" : "text-red-600"}`}
                    >
                      {transaction.amount > 0 ? "+" : ""}
                      {transaction.amount}
                    </td>
                    <td className="py-3 px-6 text-left">
                      {transaction.api_endpoint || "-"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
