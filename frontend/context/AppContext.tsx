"use client";

import { createContext, useContext, useState, useEffect, useCallback, useRef } from "react";
import { Car, TradeInEstimate, Message } from "@/types";
import { v4 as uuidv4 } from "uuid";

interface AppState {
  selectedCar: Car | null;
  tradeInEstimate: TradeInEstimate | null;
  currentStep: number;
  chatMessages: Message[];
  tradeInAsked: boolean;
  chatSessionId: string;
  setSelectedCar: (car: Car) => void;
  setTradeInEstimate: (estimate: TradeInEstimate) => void;
  setCurrentStep: (step: number) => void;
  setChatMessages: (msgs: Message[] | ((prev: Message[]) => Message[])) => void;
  setTradeInAsked: (v: boolean) => void;
  resetAll: () => void;
}

const AppContext = createContext<AppState | null>(null);

// Bump this string any time you want all users' localStorage wiped on next load.
const LS_VERSION = "v3";
const LS_KEYS = ["aa_selectedCar", "aa_tradeInEstimate", "aa_currentStep", "aa_chatMessages", "aa_tradeInAsked"];

function clearAllStorage() {
  LS_KEYS.forEach(k => localStorage.removeItem(k));
}

export function AppProvider({ children }: { children: React.ReactNode }) {
  const [selectedCar, setSelectedCarState] = useState<Car | null>(null);
  const [tradeInEstimate, setTradeInEstimateState] = useState<TradeInEstimate | null>(null);
  const [currentStep, setCurrentStepState] = useState<number>(1);
  const [chatMessages, setChatMessagesState] = useState<Message[]>([]);
  const [tradeInAsked, setTradeInAskedState] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const chatSessionId = useRef<string>(uuidv4()).current;

  // Load from localStorage on mount — wipe if version mismatch
  useEffect(() => {
    const storedVersion = localStorage.getItem("aa_version");
    if (storedVersion !== LS_VERSION) {
      clearAllStorage();
      localStorage.setItem("aa_version", LS_VERSION);
      setHydrated(true);
      return;
    }
    try {
      const car = localStorage.getItem("aa_selectedCar");
      const est = localStorage.getItem("aa_tradeInEstimate");
      const step = localStorage.getItem("aa_currentStep");
      const msgs = localStorage.getItem("aa_chatMessages");
      const asked = localStorage.getItem("aa_tradeInAsked");
      if (car) setSelectedCarState(JSON.parse(car));
      if (est) setTradeInEstimateState(JSON.parse(est));
      if (step) setCurrentStepState(Number(step));
      if (msgs) setChatMessagesState(JSON.parse(msgs));
      if (asked) setTradeInAskedState(true);
    } catch {}
    setHydrated(true);
  }, []);

  const setSelectedCar = useCallback((car: Car) => {
    setSelectedCarState(car);
    localStorage.setItem("aa_selectedCar", JSON.stringify(car));
  }, []);

  const setTradeInEstimate = useCallback((estimate: TradeInEstimate) => {
    setTradeInEstimateState(estimate);
    localStorage.setItem("aa_tradeInEstimate", JSON.stringify(estimate));
  }, []);

  const setCurrentStep = useCallback((step: number) => {
    setCurrentStepState(step);
    localStorage.setItem("aa_currentStep", String(step));
  }, []);

  const setChatMessages = useCallback((msgs: Message[] | ((prev: Message[]) => Message[])) => {
    setChatMessagesState((prev) => {
      const next = typeof msgs === "function" ? msgs(prev) : msgs;
      localStorage.setItem("aa_chatMessages", JSON.stringify(next));
      return next;
    });
  }, []);

  const setTradeInAsked = useCallback((v: boolean) => {
    setTradeInAskedState(v);
    if (v) localStorage.setItem("aa_tradeInAsked", "true");
    else   localStorage.removeItem("aa_tradeInAsked");
  }, []);

  const resetAll = useCallback(() => {
    setSelectedCarState(null);
    setTradeInEstimateState(null);
    setCurrentStepState(1);
    setChatMessagesState([]);
    setTradeInAsked(false);
    clearAllStorage();
    // Clear backend sessions so Claude doesn't answer from stale history
    const body = JSON.stringify({ session_id: chatSessionId });
    const opts = { method: "POST", headers: { "Content-Type": "application/json" }, body };
    fetch("/reset",         opts);
    fetch("/reset-tradein", opts);
  }, [chatSessionId]);

  if (!hydrated) return null;

  return (
    <AppContext.Provider
      value={{
        selectedCar, tradeInEstimate, currentStep,
        chatMessages, tradeInAsked, chatSessionId,
        setSelectedCar, setTradeInEstimate, setCurrentStep,
        setChatMessages, setTradeInAsked, resetAll,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useAppContext(): AppState {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useAppContext must be used within AppProvider");
  return ctx;
}
