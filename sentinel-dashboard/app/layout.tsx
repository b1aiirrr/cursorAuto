import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { IBM_Plex_Sans, JetBrains_Mono } from "next/font/google";

export const metadata = {
  metadataBase: new URL("https://squareautomation.vercel.app"),
  title: "MOMIGI 2026 | High-Conviction Degenerate Analyst Dashboard",
  description: "Official real-time monitoring dashboard for the MOMIGI 2026 autonomous Binance Square agent. Maximizing Write-to-Earn rewards and yield optimization.",
  keywords: ["MOMIGI", "Binance Square", "Write to Earn", "Crypto Analyst", "Yield Optimization", "Autonomous Trading"],
  authors: [{ name: "MOMIGI 2026" }],
  openGraph: {
    title: "MOMIGI 2026 | High-Conviction Analyst Dashboard",
    description: "Real-time alpha and yield monitoring for MOMIGI 2026.",
    url: "https://squareautomation.vercel.app",
    siteName: "MOMIGI 2026",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
      },
    ],
    locale: "en_US",
    type: "website",
  },
};

import "./globals.css";

const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-plex-sans",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  weight: ["500", "700"],
  variable: "--font-jetbrains-mono",
});

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${plexSans.variable} ${jetbrainsMono.variable}`}>
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
