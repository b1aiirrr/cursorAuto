import { Analytics } from "@vercel/analytics/next";
import { IBM_Plex_Sans, JetBrains_Mono } from "next/font/google";

export const metadata = {
  metadataBase: new URL("https://squareautomation.vercel.app"),
  title: "SquareAutomation Dashboard",
  description: "Command center for autonomous Binance Square automation",
  openGraph: {
    title: "SquareAutomation Dashboard",
    description: "Command center for autonomous Binance Square automation",
    url: "https://squareautomation.vercel.app",
    siteName: "SquareAutomation",
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
      </body>
    </html>
  );
}
