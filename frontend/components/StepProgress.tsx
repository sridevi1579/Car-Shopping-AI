"use client";

import { useAppContext } from "@/context/AppContext";

const STEPS = [
  { label: "Car Search", short: "Search" },
  { label: "Financing",  short: "Finance" },
  { label: "Trade-In",   short: "Trade-In" },
  { label: "Summary",    short: "Summary" },
];

export default function StepProgress() {
  const { currentStep } = useAppContext();

  return (
    <div className="bg-white border-t border-slate-100 px-4 py-2">
      <div className="max-w-[780px] mx-auto flex items-center justify-between gap-1">
        {STEPS.map((step, i) => {
          const num = i + 1;
          const isCompleted = num < currentStep;
          const isCurrent = num === currentStep;

          return (
            <div key={num} className="flex items-center flex-1 min-w-0">
              {/* Step circle + label */}
              <div className="flex flex-col items-center gap-0.5 flex-shrink-0">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold transition-colors ${
                    isCompleted
                      ? "bg-green-500 text-white"
                      : isCurrent
                      ? "bg-[#1e3a8a] text-white"
                      : "bg-slate-200 text-slate-400"
                  }`}
                >
                  {isCompleted ? (
                    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                      <path d="M2 6l3 3 5-5" stroke="white" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  ) : (
                    num
                  )}
                </div>
                <span
                  className={`text-[10px] font-medium hidden sm:block ${
                    isCurrent ? "text-[#1e3a8a]" : isCompleted ? "text-green-600" : "text-slate-400"
                  }`}
                >
                  {step.label}
                </span>
                <span
                  className={`text-[10px] font-medium sm:hidden ${
                    isCurrent ? "text-[#1e3a8a]" : isCompleted ? "text-green-600" : "text-slate-400"
                  }`}
                >
                  {step.short}
                </span>
              </div>

              {/* Connector line (skip after last step) */}
              {i < STEPS.length - 1 && (
                <div
                  className={`flex-1 h-0.5 mx-1 transition-colors ${
                    num < currentStep ? "bg-green-400" : "bg-slate-200"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
