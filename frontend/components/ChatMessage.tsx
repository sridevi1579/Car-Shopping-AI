import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Message } from "@/types";
import CarResultCards from "@/components/CarResultCards";

interface Props {
  message: Message;
  onSendMessage?: (text: string) => void;
}

export default function ChatMessage({ message, onSendMessage }: Props) {
  const isUser = message.role === "user";

  return (
    <div
      className={`flex items-end gap-2 animate-fadeSlideUp ${
        isUser ? "flex-row-reverse" : "flex-row"
      }`}
    >
      {/* Avatar */}
      <div className="shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm bg-slate-100 select-none">
        {isUser ? "👤" : "🤖"}
      </div>

      {/* Bubble */}
      {isUser ? (
        <div className="max-w-[75%] px-4 py-3 rounded-2xl rounded-br-sm bg-[#1e3a8a] text-white text-sm leading-relaxed shadow-sm">
          {message.content}
        </div>
      ) : (
        <div className="max-w-[85%] px-4 py-3 rounded-2xl rounded-bl-sm bg-white shadow-md text-[#0f172a] text-sm">
          <div className="agent-markdown">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                table: ({ children }) => (
                  <div className="table-wrapper">
                    <table>{children}</table>
                  </div>
                ),
                a: ({ href, children }) => (
                  <a href={href} target="_blank" rel="noopener noreferrer">
                    {children}
                  </a>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
          {message.cars && message.cars.length > 0 && (
            <CarResultCards cars={message.cars} onSendMessage={onSendMessage} />
          )}
          {/EMI|APR|loan amount|down payment|monthly payment/i.test(message.content) && (
            <p className="mt-3 text-[11px] text-slate-400 italic border-t border-slate-100 pt-2">
              ⚠️ These are financing estimates for demonstration purposes only. Actual rates depend on lender approval.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
