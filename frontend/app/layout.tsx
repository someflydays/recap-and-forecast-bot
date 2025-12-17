import "./globals.css";
import type { Metadata } from "next";
import { Inter } from "next/font/google";

const inter = Inter({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Recap & Forecast",
  description: "AI-powered insights on any topic — past events or future predictions",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className={`${inter.className} antialiased`}>
        <div className="bg-glow" aria-hidden="true" />
        <div className="bg-orb" aria-hidden="true" />
        <div className="bg-noise" aria-hidden="true" />
        {children}
      </body>
    </html>
  );
}
