import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "InternPilot AI — System Status & Platform Dashboard",
  description:
    "AI-powered platform empowering students to discover vetted internships, analyze credibility, and streamline outreach.",
  keywords: ["internship", "AI copilot", "student careers", "internship finder"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans antialiased text-slate-100 flex flex-col min-h-screen">
        <header className="sticky top-0 z-50 w-full border-b border-slate-800/80 bg-slate-950/70 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center space-x-3 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-500 to-sky-400 flex items-center justify-center font-bold text-white shadow-lg shadow-indigo-500/20 group-hover:scale-105 transition-transform">
                IP
              </div>
              <div>
                <span className="font-semibold text-base text-white tracking-tight">InternPilot</span>
                <span className="ml-1 text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 border border-indigo-400/30 text-indigo-300 font-medium">
                  AI
                </span>
              </div>
            </Link>

            <nav className="flex items-center space-x-2">
              <Link
                href="/"
                className="px-3 py-1.5 text-sm font-medium rounded-lg text-slate-300 hover:text-white hover:bg-slate-800/60 transition-colors"
              >
                Overview
              </Link>
              <Link
                href="/status"
                className="px-3 py-1.5 text-sm font-medium rounded-lg text-indigo-300 bg-indigo-950/60 border border-indigo-800/50 hover:bg-indigo-900/60 hover:text-indigo-200 transition-colors flex items-center gap-1.5"
              >
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                System Status
              </Link>
            </nav>
          </div>
        </header>

        <main className="flex-1 flex flex-col">{children}</main>

        <footer className="border-t border-slate-800/60 py-6 text-center text-xs text-slate-500 bg-slate-950/50">
          <p>© 2026 InternPilot AI. Phase 1 Core Infrastructure.</p>
        </footer>
      </body>
    </html>
  );
}
