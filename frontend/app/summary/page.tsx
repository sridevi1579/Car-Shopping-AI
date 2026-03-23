"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import TradeInCard from "@/components/TradeInCard";
import { useAppContext } from "@/context/AppContext";

function calcMonthlyPayment(principal: number, aprPercent: number, months: number): number {
  const r = aprPercent / 100 / 12;
  if (r === 0) return principal / months;
  return principal * (r * Math.pow(1 + r, months)) / (Math.pow(1 + r, months) - 1);
}

export default function SummaryPage() {
  const { selectedCar, tradeInEstimate, resetAll } = useAppContext();
  const router = useRouter();

  const handleStartNew = () => {
    resetAll();
    router.push("/");
  };

  const carPrice = selectedCar?.price ?? null;
  const tradeInValue = tradeInEstimate?.trade_in_value ?? null;
  const amountFinanced =
    carPrice !== null && tradeInValue !== null ? Math.max(0, carPrice - tradeInValue) : null;
  const apr = 7.9;
  const monthly36 = amountFinanced !== null && amountFinanced > 0 ? calcMonthlyPayment(amountFinanced, apr, 36) : null;
  const monthly48 = amountFinanced !== null && amountFinanced > 0 ? calcMonthlyPayment(amountFinanced, apr, 48) : null;
  const monthly60 = amountFinanced !== null && amountFinanced > 0 ? calcMonthlyPayment(amountFinanced, apr, 60) : null;

  return (
    <div className="flex flex-col min-h-screen bg-[#f8fafc]">
      {/* Header */}
      <header className="shrink-0 bg-white border-b border-slate-200 shadow-sm z-10">
        <div className="flex items-center justify-between px-6 py-3">
          <span
            className="text-xl font-bold text-[#1e3a8a]"
            style={{ fontFamily: "'Syne', sans-serif" }}
          >
            AutoCar 🚗
          </span>
          <span className="text-xs text-[#64748b] hidden sm:block">
            Powered by Claude · NHTSA · fueleconomy.gov
          </span>
        </div>
        <div className="flex border-t border-slate-100">
          <Link href="/" className="px-6 py-2 text-sm font-medium text-slate-500 hover:text-[#1e3a8a] hover:bg-slate-50 transition-colors">
            🔍 Car Finder
          </Link>
          <Link href="/tradein" className="px-6 py-2 text-sm font-medium text-slate-500 hover:text-[#1e3a8a] hover:bg-slate-50 transition-colors">
            💰 Trade-In Estimator
          </Link>
          <span className="px-6 py-2 text-sm font-semibold text-[#1e3a8a] border-b-2 border-[#1e3a8a] bg-blue-50">
            📋 Summary
          </span>
        </div>
      </header>

      <main className="flex-1">
        <div className="max-w-[780px] mx-auto px-4 py-8 flex flex-col gap-6">

          {/* Title */}
          <div className="text-center">
            <div className="text-4xl mb-2">📋</div>
            <h1 className="text-2xl font-bold text-[#1e3a8a]" style={{ fontFamily: "'Syne', sans-serif" }}>
              Your Deal Summary
            </h1>
            <p className="text-sm text-slate-500 mt-1">Here&apos;s everything in one place.</p>
          </div>

          {/* No data fallback */}
          {!selectedCar && !tradeInEstimate && (
            <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-8 text-center">
              <p className="text-slate-500 mb-4">No data yet. Start by searching for a car.</p>
              <button
                onClick={() => router.push("/")}
                className="px-6 py-2 rounded-lg bg-[#1e3a8a] text-white text-sm font-semibold hover:bg-blue-800 transition-colors"
              >
                Go to Car Finder
              </button>
            </div>
          )}

          {/* Selected car card */}
          {selectedCar && (
            <div className="rounded-xl bg-white border border-slate-200 shadow-sm overflow-hidden">
              <div className="bg-[#1e3a8a] px-4 py-3">
                <p className="text-white font-semibold text-sm">🚗 Selected Vehicle</p>
              </div>
              <div className="px-4 py-4">
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-slate-800">
                      {selectedCar.year} {selectedCar.make} {selectedCar.model}
                    </h2>
                    <p className="text-sm text-slate-500">{selectedCar.trim} · {selectedCar.source}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xl font-bold text-[#1e3a8a]">${selectedCar.price.toLocaleString()}</p>
                    <p className="text-xs text-slate-400">{selectedCar.mileage.toLocaleString()} mi</p>
                  </div>
                </div>
                <table className="w-full text-sm">
                  <tbody>
                    {[
                      ["Condition",    selectedCar.condition],
                      ["Color",        selectedCar.color],
                      ["Drive Type",   selectedCar.drive_type],
                      ["Location",     selectedCar.location],
                      ["Fuel Economy", selectedCar.fuel_economy || "N/A"],
                      ["Safety Rating",selectedCar.safety_rating || "N/A"],
                      ["VIN",          selectedCar.vin],
                    ].map(([label, value]) => (
                      <tr key={label} className="even:bg-slate-50">
                        <td className="py-1.5 pr-4 font-medium text-blue-800 w-36">{label}</td>
                        <td className="py-1.5 text-slate-700">{value}</td>
                      </tr>
                    ))}
                    {selectedCar.recalls && selectedCar.recalls.length > 0 && (
                      <tr className="even:bg-slate-50">
                        <td className="py-1.5 pr-4 font-medium text-blue-800 align-top">Inspection Notes</td>
                        <td className="py-1.5 text-slate-700">
                          <ul className="list-disc list-inside space-y-0.5">
                            {selectedCar.recalls.map((note, idx) => (
                              <li key={idx} className="text-slate-600 text-xs">{note}</li>
                            ))}
                          </ul>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Trade-in card */}
          {tradeInEstimate && <TradeInCard estimate={tradeInEstimate} />}

          {/* Final numbers */}
          {selectedCar && tradeInEstimate && tradeInEstimate.trade_in_value !== null && (
            <div className="rounded-xl bg-white border border-slate-200 shadow-sm overflow-hidden">
              <div className="bg-green-700 px-4 py-3">
                <p className="text-white font-semibold text-sm">💡 Final Numbers</p>
              </div>
              <div className="px-4 py-4">
                <table className="w-full text-sm">
                  <tbody>
                    <tr>
                      <td className="py-2 text-slate-600">Vehicle Price</td>
                      <td className="py-2 text-right font-medium text-slate-800">${carPrice!.toLocaleString()}</td>
                    </tr>
                    <tr>
                      <td className="py-2 text-slate-600">− Trade-In Value</td>
                      <td className="py-2 text-right font-medium text-green-700">− ${tradeInValue!.toLocaleString()}</td>
                    </tr>
                    <tr>
                      <td colSpan={2} className="py-0">
                        <div className="border-t border-slate-200 my-1" />
                      </td>
                    </tr>
                    <tr>
                      <td className="py-2 font-bold text-slate-800 text-base">Amount Financed</td>
                      <td className="py-2 text-right font-bold text-[#1e3a8a] text-lg">${amountFinanced!.toLocaleString()}</td>
                    </tr>
                  </tbody>
                </table>

                {amountFinanced !== null && amountFinanced > 0 && (
                  <>
                    <div className="border-t border-slate-100 mt-3 pt-3">
                      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                        Monthly Payment Options ({apr}% APR)
                      </p>
                      <div className="grid grid-cols-3 gap-2">
                        {[
                          { months: 36, payment: monthly36 },
                          { months: 48, payment: monthly48 },
                          { months: 60, payment: monthly60 },
                        ].map(({ months, payment }) => (
                          <div key={months} className="text-center rounded-lg bg-blue-50 border border-blue-100 py-3">
                            <p className="text-lg font-bold text-[#1e3a8a]">
                              ${payment?.toFixed(0)}
                            </p>
                            <p className="text-xs text-slate-500">{months} months</p>
                          </div>
                        ))}
                      </div>
                    </div>
                    <p className="text-[11px] text-slate-400 italic mt-3">
                      ⚠️ These are estimates for demonstration purposes only. Actual rates depend on lender approval.
                    </p>
                  </>
                )}
              </div>
            </div>
          )}

          {/* CTA — visit Carvana to proceed */}
          {(selectedCar || tradeInEstimate) && (
            <div className="rounded-xl overflow-hidden border border-blue-200 shadow-sm">
              <div className="bg-gradient-to-r from-[#1e3a8a] to-blue-600 px-5 py-4 flex flex-col sm:flex-row items-center justify-between gap-3">
                <div>
                  <p className="text-white font-semibold text-sm">
                    Ready to make it official?
                  </p>
                  <p className="text-blue-100 text-xs mt-0.5">
                    Visit Carvana to complete your purchase, apply for financing, and get your car delivered to your door.
                  </p>
                </div>
                <a
                  href="https://www.carvana.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="shrink-0 inline-flex items-center gap-1.5 px-5 py-2 rounded-lg bg-white text-[#1e3a8a] text-sm font-bold hover:bg-blue-50 transition-colors shadow"
                >
                  Visit Carvana →
                </a>
              </div>
            </div>
          )}

          {/* Start new search */}
          <button
            onClick={handleStartNew}
            className="w-full py-3 rounded-xl bg-[#1e3a8a] hover:bg-blue-800 text-white text-sm font-semibold transition-colors"
          >
            🔍 Start New Search
          </button>

        </div>
      </main>
    </div>
  );
}
