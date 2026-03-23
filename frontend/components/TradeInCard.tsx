"use client";

import { TradeInEstimate } from "@/types";

interface Props {
  estimate: TradeInEstimate;
}

const confidenceConfig = {
  high:   { label: "High Confidence",   color: "text-green-700 bg-green-50 border-green-200" },
  medium: { label: "Medium Confidence", color: "text-yellow-700 bg-yellow-50 border-yellow-200" },
  low:    { label: "Low Confidence",    color: "text-orange-700 bg-orange-50 border-orange-200" },
  none:   { label: "No Estimate",       color: "text-slate-600 bg-slate-50 border-slate-200" },
};

export default function TradeInCard({ estimate }: Props) {
  const conf = confidenceConfig[estimate.confidence] ?? confidenceConfig.none;

  if (estimate.trade_in_value === null) {
    return (
      <div className="mt-3 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <p className="text-sm text-slate-500">{estimate.reasoning}</p>
      </div>
    );
  }

  return (
    <div className="mt-3 rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
      {/* Value banner */}
      <div className="bg-[#1e3a8a] px-5 py-4">
        <p className="text-xs text-blue-300 uppercase tracking-widest mb-1">Estimated Trade-In Value</p>
        <p className="text-4xl font-bold text-white">
          ${estimate.trade_in_value.toLocaleString()}
        </p>
      </div>

      {/* Details */}
      <div className="px-5 py-4 flex flex-col gap-3">
        {/* Confidence badge */}
        <span className={`self-start text-xs font-semibold px-3 py-1 rounded-full border ${conf.color}`}>
          {conf.label}
        </span>

        {/* Reasoning */}
        <div>
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">How we calculated this</p>
          <p className="text-sm text-slate-700 leading-relaxed">{estimate.reasoning}</p>
        </div>

        {/* Financing impact */}
        <div className="rounded-xl bg-blue-50 border border-blue-100 px-4 py-3">
          <p className="text-xs font-semibold text-blue-600 uppercase tracking-wider mb-1">Financing Impact</p>
          <p className="text-sm text-blue-800 leading-relaxed">{estimate.financing_impact}</p>
        </div>

        {estimate.confidence === "low" && (
          <p className="text-xs text-orange-600 italic">
            * Limited market data for this vehicle. Estimate may vary.
          </p>
        )}

        {/* Disclaimer */}
        <div className="rounded-xl bg-slate-50 border border-slate-200 px-4 py-3 flex gap-2 items-start">
          <span className="text-slate-400 text-sm mt-0.5">⚠️</span>
          <p className="text-xs text-slate-500 leading-relaxed">
            <span className="font-semibold text-slate-600">Disclaimer:</span> This is an estimate only based on market data and self-reported condition. Actual trade-in value may vary and is subject to physical inspection by the dealer. For an accurate quote, visit a dealership in person.
          </p>
        </div>
      </div>
    </div>
  );
}
