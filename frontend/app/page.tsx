"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { v4 as uuidv4 } from "uuid"; // still used for message IDs
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Message } from "@/types";
import ChatMessage from "@/components/ChatMessage";
import ChatInput from "@/components/ChatInput";
import TypingIndicator from "@/components/TypingIndicator";
import SuggestionChips from "@/components/SuggestionChips";
import { useAppContext } from "@/context/AppContext";


// Detect when the agent has asked the trade-in question after financing
function isTradeInQuestion(text: string): boolean {
  return /trade[\s-]?in your current vehicle/i.test(text);
}

export default function Home() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  const {
    selectedCar, setCurrentStep, resetAll,
    chatMessages: messages, setChatMessages: setMessages,
    tradeInAsked, setTradeInAsked, chatSessionId,
  } = useAppContext();

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading, tradeInAsked]);

  // Reset trade-in prompt only when car is explicitly cleared (not on initial mount)
  const mounted = useRef(false);
  useEffect(() => {
    if (!mounted.current) { mounted.current = true; return; }
    if (!selectedCar) setTradeInAsked(false);
  }, [selectedCar]);

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim() || loading) return;
      setError(null);

      const userMsg: Message = { id: uuidv4(), role: "user", content: text };
      setMessages((prev) => [...prev, userMsg]);
      setLoading(true);

      try {
        const res = await fetch("/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: text, session_id: chatSessionId }),
        });

        if (!res.ok) throw new Error("Server error");

        const data = await res.json();
        const responseText: string = data.response ?? "";

        const agentMsg: Message = {
          id: uuidv4(),
          role: "agent",
          content: responseText,
          cars: data.cars?.length > 0 ? data.cars : undefined,
        };
        setMessages((prev) => [...prev, agentMsg]);

        // Show trade-in Yes/No buttons only after financing is done
        if (isTradeInQuestion(responseText)) {
          setTradeInAsked(true);
        }
      } catch {
        setError("Connection error — make sure the Flask server is running on port 5000.");
      } finally {
        setLoading(false);
      }
    },
    [loading]
  );

  const handleYesTradeIn = () => {
    setCurrentStep(3);
    router.push("/tradein");
  };

  const handleNoTradeIn = () => {
    setCurrentStep(4);
    router.push("/summary");
  };

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
          <div className="flex items-center gap-3">
            <span className="text-xs text-[#64748b] hidden sm:block">
              Powered by Claude · NHTSA · fueleconomy.gov
            </span>
            {messages.length > 0 && (
              <button
                onClick={resetAll}
                className="text-xs text-slate-500 hover:text-red-600 border border-slate-200 hover:border-red-300 px-2.5 py-1 rounded-lg transition-colors"
              >
                New Search
              </button>
            )}
          </div>
        </div>
        {/* Tab navigation */}
        <div className="flex border-t border-slate-100">
          <span className="px-6 py-2 text-sm font-semibold text-[#1e3a8a] border-b-2 border-[#1e3a8a] bg-blue-50">
            🔍 Car Finder
          </span>
          <Link
            href="/tradein"
            className="px-6 py-2 text-sm font-medium text-slate-500 hover:text-[#1e3a8a] hover:bg-slate-50 transition-colors"
          >
            💰 Trade-In Estimator
          </Link>
        </div>
      </header>

      {/* Chat area */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[780px] mx-auto px-4 py-6 flex flex-col gap-4">
          {messages.length === 0 && !loading && (
            <SuggestionChips onSelect={sendMessage} />
          )}

          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} onSendMessage={sendMessage} />
          ))}

          {loading && <TypingIndicator />}

          {error && (
            <div className="text-center text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl px-4 py-3">
              {error}
            </div>
          )}

          {/* Trade-in Yes / No prompt — appears inline after financing is done */}
          {tradeInAsked && !loading && (
            <div className="rounded-xl border border-blue-200 bg-blue-50 px-4 py-4 flex flex-col gap-3">
              <p className="text-sm font-semibold text-[#1e3a8a]">
                Would you like to trade in your current vehicle?
              </p>
              <p className="text-xs text-slate-500">
                Applying a trade-in value as a down payment can reduce your monthly payment.
              </p>
              <div className="flex gap-3">
                <button
                  onClick={handleYesTradeIn}
                  className="flex-1 py-2 rounded-lg bg-[#1e3a8a] hover:bg-blue-800 text-white text-sm font-semibold transition-colors"
                >
                  Yes, Trade In My Car →
                </button>
                <button
                  onClick={handleNoTradeIn}
                  className="flex-1 py-2 rounded-lg bg-white hover:bg-slate-50 text-slate-700 text-sm font-semibold border border-slate-300 transition-colors"
                >
                  No, Skip to Summary →
                </button>
              </div>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      </main>

      {/* Selected car banner — just shows car info, no nav button until financing done */}
      {selectedCar && (
        <div className="shrink-0 bg-[#1e3a8a] text-white px-4 py-2.5 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2 min-w-0">
            <span className="text-green-300 text-base">✅</span>
            <span className="text-sm font-semibold truncate">
              {selectedCar.year} {selectedCar.make} {selectedCar.model} {selectedCar.trim}
              {" · "}
              <span className="text-blue-200">${selectedCar.price.toLocaleString()}</span>
            </span>
          </div>
          <button
            onClick={resetAll}
            className="text-xs text-blue-300 hover:text-white underline transition-colors shrink-0"
          >
            Clear
          </button>
        </div>
      )}

      {/* Input bar */}
      <div className="shrink-0 border-t border-slate-200 bg-white px-4 py-3">
        <div className="max-w-[780px] mx-auto">
          <ChatInput onSend={sendMessage} disabled={loading} />
        </div>
      </div>
    </div>
  );
}
