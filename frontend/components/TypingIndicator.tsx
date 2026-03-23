export default function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 animate-fadeSlideUp">
      <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm bg-slate-100 select-none">
        🤖
      </div>
      <div className="px-4 py-3 rounded-2xl rounded-bl-sm bg-white shadow-md flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-2 h-2 rounded-full bg-[#3b82f6] inline-block animate-bounce3"
            style={{ animationDelay: `${i * 0.18}s` }}
          />
        ))}
      </div>
    </div>
  );
}
