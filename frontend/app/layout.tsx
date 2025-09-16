import "./globals.css";
import type { Metadata } from "next";
import { cn } from "../lib/utils";

export const metadata: Metadata = {
  title: "IsoFlicker Control",
  description: "Research-grade preset browser for the Windows entrainment engine"
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={cn("min-h-screen bg-slate-950 text-slate-100")}>{children}</body>
    </html>
  );
}
