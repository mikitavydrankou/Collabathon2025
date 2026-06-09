import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const _geist = Geist({ subsets: ["latin"] });
const _geistMono = Geist_Mono({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Commerzbank - Mobile Banking",
  description: "Secure online banking with Commerzbank",
  generator: "v0.app",
  viewport:
    "width=device-width, initial-scale=1, viewport-fit=cover, user-scalable=no",
  icons: {
    icon: [
      {
        url: "/icon-light-32x32.png",
        media: "(prefers-color-scheme: light)",
      },
      {
        url: "/icon-dark-32x32.png",
        media: "(prefers-color-scheme: dark)",
      },
      {
        url: "/icon.svg",
        type: "image/svg+xml",
      },
    ],
    apple: "/apple-icon.png",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta
          name="apple-mobile-web-app-status-bar-style"
          content="black-translucent"
        />
      </head>
      <body
        className={`font-sans antialiased`}
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      >
        {/* Desktop-only note: this app is designed for mobile screens. */}
        <aside className="hidden lg:flex fixed left-6 top-1/2 -translate-y-1/2 z-[100] w-56 flex-col gap-2 pointer-events-none">
          <div className="flex items-center gap-2 text-slate-400">
            <svg
              className="w-5 h-5 shrink-0"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <rect x="7" y="2" width="10" height="20" rx="2" strokeWidth={1.8} />
              <line x1="11" y1="18" x2="13" y2="18" strokeWidth={1.8} strokeLinecap="round" />
            </svg>
            <span className="text-sm font-semibold text-slate-500">Built for mobile</span>
          </div>
          <p className="text-xs leading-relaxed text-slate-400">
            This app was designed for mobile devices. For the best experience,
            open it on a phone or resize your browser to a narrow window.
          </p>
        </aside>
        {children}
      </body>
    </html>
  );
}
