"use client";

import { AppProvider } from "@/context/AppContext";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  return <AppProvider>{children}</AppProvider>;
}
