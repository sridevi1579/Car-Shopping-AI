"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { v4 as uuidv4 } from "uuid";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Message, TradeInEstimate } from "@/types";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import TypingIndicator from "@/components/TypingIndicator";
import TradeInCard from "@/components/TradeInCard";
import { useAppContext } from "@/context/AppContext";

function calcMonthlyPayment(principal: number, aprPercent: number, months: number): number {
  const r = aprPercent / 100 / 12;
  if (r === 0) return principal / months;
  return principal * (r * Math.pow(1 + r, months)) / (Math.pow(1 + r, months) - 1);
}

export default function TradeInPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sessionId = useRef<string>(uuidv4());
  const bottomRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const { selectedCar, tradeInEstimate, setTradeInEstimate, setCurrentStep } = useAppContext();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;
      setError(null);

      const userMsg: Message = { id: uuidv4(), role: "user", content: text };
      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);

      try {
        const res = await fetch("/estimate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, session_id: sessionId.current }),
        });

        if (!res.ok) throw new Error("Server error");

        const data = await res.json();
        const estimate: TradeInEstimate | undefined =
          data.estimate && Object.keys(data.estimate).length > 0
            ? (data.estimate as TradeInEstimate)
            : undefined;

        if (estimate) {
          setTradeInEstimate(estimate);
          setCurrentStep(4);
        }

        const agentMsg: Message = {
          id: uuidv4(),
          role: "agent",
          content: data.response,
          estimate,
        };
        setMessages((prev) => [...prev, agentMsg]);
      } catch {
        setError("Connection error — make sure the Flask server is running on port 5000.");
      } finally {
        setLoading(false);
      }
    },
    [loading, setTradeInEstimate, setCurrentStep]
  );

  const handleReset = async () => {
    await fetch("/reset-tradein", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId.current }),
    });
    sessionId.current = uuidv4();
    setMessages([]);
    setError(null);
  };

  // Combined calculation
  const carPrice = selectedCar?.price ?? null;
  const tradeInValue = tradeInEstimate?.trade_in_value ?? null;
  const amountFinanced =
    carPrice !== null && tradeInValue !== null ? Math.max(0, carPrice - tradeInValue) : null;
  const apr = 7.9; // Good credit default (matches Financing.md)
  const monthly60 =
    amountFinanced !== null && amountFinanced > 0
      ? calcMonthlyPayment(amountFinanced, apr, 60)
      : amountFinanced === 0 ? 0 : null;

  return (
    <div className="flex flex-col h-screen bg-[#f8fafc]">
      {/* Header */}
      <header className="shrink-0 bg-white border-b border-slate-200 shadow-sm z-10">
        <div className="flex items-center justify-between px-6 py-3">
          <span
            className="text-xl font-bold text-[#1e3a8a]"
            style={{ fontFamily: "'Syne', sans-serif" }}
          >
            AutoCar 🚗
          </span>
          <button
            onClick={handleReset}
            className="text-xs text-slate-500 hover:text-red-500 transition-colors"
          >
            Reset session
          </button>
        </div>
        {/* Tab navigation */}
        <div className="flex border-t border-slate-100">
          <Link
            href="/"
            className="px-6 py-2 text-sm font-medium text-slate-500 hover:text-[#1e3a8a] hover:bg-slate-50 transition-colors"
          >
            🔍 Car Finder
          </Link>
          <span className="px-6 py-2 text-sm font-semibold text-[#1e3a8a] border-b-2 border-[#1e3a8a] bg-blue-50">
            💰 Trade-In Estimator
          </span>
        </div>
      </header>

      {/* Chat area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[780px] mx-auto px-4 py-6 flex flex-col gap-4">

          {/* Selected car context panel */}
          {selectedCar && (
            <div className="rounded-xl bg-blue-50 border border-blue-200 px-4 py-3 flex items-center gap-3">
              <span className="text-2xl">🚗</span>
              <div className="flex-1 min-w-0">
                <p className="text-[10px] font-bold uppercase tracking-wide text-blue-400 mb-0.5">
                  Car you want to buy
                </p>
                <p className="text-sm font-semibold text-[#1e3a8a] truncate">
                  {selectedCar.year} {selectedCar.make} {selectedCar.model} {selectedCar.trim}
                </p>
                <p className="text-xs text-slate-500">
                  ${selectedCar.price.toLocaleString()} · {selectedCar.mileage.toLocaleString()} mi · {selectedCar.source} · {selectedCar.location}
                </p>
              </div>
            </div>
          )}

          {/* Welcome card when chat is empty */}
          {messages.length === 0 && !loading && (
            <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6 text-center">
              <div className="text-4xl mb-3">💰</div>
              <h2 className="text-lg font-bold text-[#1e3a8a] mb-2">
                Car Trade-In Estimator
              </h2>
              <p className="text-sm text-slate-500 mb-4">
                Tell me about your car and I&apos;ll estimate how much a dealer
                would offer you for it as a trade-in.
              </p>
              <div className="flex flex-wrap gap-2 justify-center">
                {[
                  "I want to trade in my 2020 Honda Civic",
                  "How much is my Toyota Camry worth?",
                  "Estimate my Jeep Wrangler trade-in value",
                ].map((chip) => (
                  <button
                    key={chip}
                    onClick={() => sendMessage(chip)}
                    className="text-xs px-3 py-2 rounded-full bg-blue-50 text-[#1e3a8a] border border-blue-100 hover:bg-blue-100 transition-colors"
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Messages */}
          {messages.map((msg) => (
            <div key={msg.id}>
              <ChatMessage message={msg} onSendMessage={sendMessage} />
              {msg.estimate && <TradeInCard estimate={msg.estimate} />}
            </div>
          ))}

          {loading && <TypingIndicator />}

          {error && (
            <div className="text-center text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
              {error}
            </div>
          )}

          {/* Combined calculation panel */}
          {selectedCar && tradeInEstimate && tradeInEstimate.trade_in_value !== null && (
            <div className="rounded-xl border border-green-200 bg-green-50 overflow-hidden">
              <div className="bg-green-700 px-4 py-2">
                <p className="text-white font-semibold text-sm">💡 Updated Financing with Trade-In</p>
              </div>
              <div className="px-4 py-4">
                <table className="w-full text-sm">
                  <tbody>
                    <tr>
                      <td className="py-1.5 text-slate-600">Car Price</td>
                      <td className="py-1.5 text-right font-medium text-slate-800">
                        ${carPrice!.toLocaleString()}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-1.5 text-slate-600">− Trade-In Value</td>
                      <td className="py-1.5 text-right font-medium text-green-700">
                        − ${tradeInValue!.toLocaleString()}
                      </td>
                    </tr>
                    <tr>
                      <td className="py-0" colSpan={2}>
                        <div className="border-t border-green-300 my-1" />
                      </td>
                    </tr>
                    <tr>
                      <td className="py-1.5 font-semibold text-slate-800">Amount Financed</td>
                      <td className="py-1.5 text-right font-bold text-[#1e3a8a] text-base">
                        ${amountFinanced!.toLocaleString()}
                      </td>
                    </tr>
                    {monthly60 !== null && (
                      <tr>
                        <td className="py-1.5 text-slate-500 text-xs">
                          Est. Monthly (60 mo @ {apr}% APR)
                        </td>
                        <td className="py-1.5 text-right font-semibold text-slate-700">
                          ~${monthly60.toFixed(0)}/mo
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
                <button
                  onClick={() => router.push("/summary")}
                  className="mt-4 w-full py-2 rounded-lg bg-[#1e3a8a] hover:bg-blue-800 text-white text-sm font-semibold transition-colors"
                >
                  View Full Summary →
                </button>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </main>

      {/* Input bar */}
      <div className="shrink-0 border-t border-slate-200 bg-white px-4 py-3">
        <div className="max-w-[780px] mx-auto">
          <ChatInput onSend={sendMessage} disabled={loading} />
        </div>
      </div>
    </div>
  );
}
