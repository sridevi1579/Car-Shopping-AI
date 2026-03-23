"use client";

import { useState } from "react";
import { Car } from "@/types";
import { useAppContext } from "@/context/AppContext";

interface Props {
  cars: Car[];
  onSendMessage?: (text: string) => void;
}

const BADGES = ["🏆", "2", "3", "4"];

function formatPrice(p: number) {
  return "$" + p.toLocaleString();
}
function formatMileage(m: number) {
  return m.toLocaleString() + " mi";
}

const COMPARE_FIELDS: [string, (c: Car) => string][] = [
  ["Source",             c => c.source],
  ["Year",               c => String(c.year)],
  ["Make / Model",       c => `${c.make} ${c.model}`],
  ["Trim",               c => c.trim],
  ["Price",              c => formatPrice(c.price)],
  ["Mileage",            c => formatMileage(c.mileage)],
  ["Condition",          c => c.condition],
  ["Color",              c => c.color],
  ["Drive Type",         c => c.drive_type],
  ["Location",           c => c.location],
  ["Fuel Economy",       c => c.fuel_economy || "N/A"],
  ["Safety Rating",      c => c.safety_rating || "N/A"],
  ["Inspection Notes",   c => c.recalls && c.recalls.length > 0 ? c.recalls.join(" · ") : "—"],
  ["VIN",                c => c.vin],
];

function ComparisonTable({ cars, onClose }: { cars: Car[]; onClose: () => void }) {
  return (
    <div className="mt-4 rounded-xl border border-blue-200 shadow-md overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 bg-blue-700">
        <span className="text-white font-semibold text-sm">Side-by-Side Comparison</span>
        <button
          onClick={onClose}
          className="text-white/80 hover:text-white text-xs underline"
        >
          Close
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-blue-50">
              <th className="py-2 px-3 text-left text-blue-800 font-semibold w-32 border-b border-blue-100">
                Detail
              </th>
              {cars.map((car, i) => (
                <th key={car.vin} className="py-2 px-3 text-left border-b border-blue-100">
                  <div className="text-blue-700 font-bold">{i === 0 ? "🏆 " : ""}{car.source}</div>
                  <div className="text-slate-600 font-normal text-xs">
                    {car.year} {car.make} {car.model} {car.trim}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {COMPARE_FIELDS.map(([label, getValue]) => (
              <tr key={label} className="even:bg-slate-50">
                <td className="py-2 px-3 font-medium text-blue-800 whitespace-nowrap border-r border-slate-100">
                  {label}
                </td>
                {cars.map(car => (
                  <td key={car.vin} className="py-2 px-3 text-slate-700">
                    {getValue(car)}
                  </td>
                ))}
              </tr>
            ))}
            <tr className="even:bg-slate-50">
              <td className="py-2 px-3 font-medium text-blue-800 border-r border-slate-100">Link</td>
              {cars.map(car => (
                <td key={car.vin} className="py-2 px-3">
                  <a
                    href={car.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 underline hover:text-blue-800 text-xs"
                  >
                    View on {car.source}
                  </a>
                </td>
              ))}
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

function CarCard({
  car,
  rank,
  selected,
  onToggleSelect,
  onSelect,
}: {
  car: Car;
  rank: number;
  selected: boolean;
  onToggleSelect: () => void;
  onSelect?: () => void;
}) {
  const [open, setOpen] = useState(rank === 0);
  const isBest = rank === 0;

  return (
    <div
      className={`rounded-xl border transition-all duration-200 overflow-hidden ${
        selected
          ? "border-blue-500 shadow-md shadow-blue-100 ring-2 ring-blue-300"
          : isBest
          ? "border-blue-400 shadow-md shadow-blue-100"
          : "border-slate-200 shadow-sm"
      }`}
    >
      {/* Header row */}
      <div
        className={`flex items-center gap-2 px-3 py-3 ${
          isBest ? "bg-blue-50" : "bg-white"
        }`}
      >
        {/* Select circle */}
        <button
          onClick={onToggleSelect}
          title="Select to compare"
          className={`shrink-0 w-5 h-5 rounded-full border-2 flex items-center justify-center transition-colors ${
            selected
              ? "border-blue-600 bg-blue-600"
              : "border-slate-300 bg-white hover:border-blue-400"
          }`}
        >
          {selected && (
            <svg width="10" height="10" viewBox="0 0 10 10" fill="none">
              <path d="M2 5l2 2 4-4" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          )}
        </button>

        {/* Rank badge */}
        <div
          className={`shrink-0 w-7 h-7 rounded-full flex items-center justify-center font-bold text-sm ${
            isBest ? "bg-yellow-400 text-white" : "bg-slate-100 text-slate-500"
          }`}
        >
          {BADGES[rank]}
        </div>

        {/* Expand/collapse button */}
        <button
          onClick={() => setOpen(o => !o)}
          className="flex-1 min-w-0 flex items-center gap-2 text-left hover:opacity-80"
        >
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              {isBest && (
                <span className="text-[10px] font-bold uppercase tracking-wide text-yellow-600 bg-yellow-100 px-1.5 py-0.5 rounded">
                  Best Deal
                </span>
              )}
              <span className="text-xs font-semibold text-blue-700">{car.source}</span>
              <span className="text-xs text-slate-400">·</span>
              <span className="text-sm font-medium text-slate-800 truncate">
                {car.year} {car.make} {car.model} {car.trim}
              </span>
            </div>
          </div>

          {/* Price + mileage */}
          <div className="shrink-0 text-right">
            <div className="text-sm font-bold text-blue-700">{formatPrice(car.price)}</div>
            <div className="text-xs text-slate-400">{formatMileage(car.mileage)}</div>
          </div>

          {/* Chevron */}
          <div className={`shrink-0 text-slate-400 transition-transform duration-200 ${open ? "rotate-180" : ""}`}>
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M4 6l4 4 4-4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
        </button>
      </div>

      {/* Expanded details */}
      {open && (
        <div className="border-t border-slate-100 bg-white px-4 py-3">
          <table className="w-full text-sm">
            <tbody>
              {([
                ["Source",           car.source],
                ["Year / Make / Model", `${car.year} ${car.make} ${car.model}`],
                ["Trim",             car.trim],
                ["Price",            formatPrice(car.price)],
                ["Mileage",          formatMileage(car.mileage)],
                ["Condition",        car.condition],
                ["Color",            car.color],
                ["Drive Type",       car.drive_type],
                ["Location",         car.location],
                ["Fuel Economy",     car.fuel_economy || "N/A"],
                ["Safety Rating",    car.safety_rating || "N/A"],
                ["VIN",              car.vin],
              ] as [string, string][]).map(([label, value]) => (
                <tr key={label} className="even:bg-slate-50">
                  <td className="py-1.5 pr-4 font-medium text-blue-800 whitespace-nowrap w-36">{label}</td>
                  <td className="py-1.5 text-slate-700">{value}</td>
                </tr>
              ))}
              {car.recalls && car.recalls.length > 0 && (
                <tr className="even:bg-slate-50">
                  <td className="py-1.5 pr-4 font-medium text-blue-800 whitespace-nowrap w-36 align-top">Inspection Notes</td>
                  <td className="py-1.5 text-slate-700">
                    <ul className="list-disc list-inside space-y-0.5">
                      {car.recalls.map((note, idx) => (
                        <li key={idx} className="text-slate-600 text-xs">{note}</li>
                      ))}
                    </ul>
                  </td>
                </tr>
              )}
              <tr className="even:bg-slate-50">
                <td className="py-1.5 pr-4 font-medium text-blue-800">Link</td>
                <td className="py-1.5">
                  <a href={car.url} target="_blank" rel="noopener noreferrer"
                    className="text-blue-600 underline hover:text-blue-800">
                    View on {car.source}
                  </a>
                </td>
              </tr>
            </tbody>
          </table>
          {onSelect && (
            <button
              onClick={onSelect}
              className="mt-3 w-full py-2 rounded-lg bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold transition-colors"
            >
              Select this car
            </button>
          )}
        </div>
      )}
    </div>
  );
}

export default function CarResultCards({ cars, onSendMessage }: Props) {
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [showComparison, setShowComparison] = useState(false);
  const { setSelectedCar, setCurrentStep } = useAppContext();

  const toggleSelect = (vin: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(vin)) next.delete(vin);
      else next.add(vin);
      return next;
    });
    setShowComparison(false);
  };

  const selectedCars = cars.filter(c => selected.has(c.vin));

  return (
    <div className="mt-3 flex flex-col gap-2">
      {cars.map((car, i) => (
        <CarCard
          key={car.vin}
          car={car}
          rank={i}
          selected={selected.has(car.vin)}
          onToggleSelect={() => toggleSelect(car.vin)}
          onSelect={onSendMessage
            ? () => {
                setSelectedCar(car);
                setCurrentStep(2);
                onSendMessage(
                  `I'd like to go with the ${car.year} ${car.make} ${car.model} ${car.trim} from ${car.source} at ${formatPrice(car.price)} with ${formatMileage(car.mileage)}.`
                );
              }
            : undefined}
        />
      ))}

      {/* Compare prompt */}
      <div className="mt-1 px-1 flex items-center justify-between gap-3 flex-wrap">
        <span className="text-xs text-slate-500">
          {selected.size === 0
            ? "Would you like to compare cars? Click the circles on cards to select."
            : selected.size === 1
            ? "Select one more car to compare."
            : `${selected.size} cars selected.`}
        </span>
        {selected.size >= 2 && !showComparison && (
          <button
            onClick={() => setShowComparison(true)}
            className="text-xs font-semibold text-white bg-blue-700 hover:bg-blue-800 px-3 py-1.5 rounded-lg transition-colors"
          >
            Compare {selected.size} Cars
          </button>
        )}
        {selected.size >= 1 && (
          <button
            onClick={() => { setSelected(new Set()); setShowComparison(false); }}
            className="text-xs text-slate-400 hover:text-slate-600 underline"
          >
            Clear
          </button>
        )}
      </div>

      {/* Side-by-side comparison */}
      {showComparison && selectedCars.length >= 2 && (
        <ComparisonTable cars={selectedCars} onClose={() => setShowComparison(false)} />
      )}
    </div>
  );
}
