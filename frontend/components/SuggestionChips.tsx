interface Props {
  onSelect: (text: string) => void;
}

const SUGGESTIONS = [
  "Used Honda Civic under $20k Phoenix AZ",
  "Toyota RAV4 under $25k Scottsdale",
  "What cars do you have?",
  "Subaru Outback AWD under $22k",
];

export default function SuggestionChips({ onSelect }: Props) {
  return (
    <div className="flex flex-col items-center gap-6 py-10 animate-fadeSlideUp">
      <div className="text-center">
        <h1
          className="text-3xl font-bold text-[#1e3a8a] mb-2"
          style={{ fontFamily: "'Syne', sans-serif" }}
        >
          AutoCar 🚗
        </h1>
        <p className="text-[#64748b] text-sm">
          Find your perfect car — I&apos;ll search across multiple sources and
          verify safety data.
        </p>
      </div>

      <div className="flex flex-wrap justify-center gap-2 max-w-lg">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => onSelect(s)}
            className="px-4 py-2 rounded-full border border-[#1e3a8a] text-[#1e3a8a] text-sm font-medium hover:bg-[#1e3a8a] hover:text-white transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
