import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { QueryProvider } from "@/lib/providers";
import { Toaster } from "sonner";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "AIVIUE - AI-Powered Hiring Platform",
    template: "%s | AIVIUE",
  },
  description: "Streamline your hiring process with AI-powered job posting and candidate screening.",
  keywords: ["hiring", "recruitment", "AI", "job posting", "candidate screening"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased min-h-screen`}
      >
        <QueryProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: 'white',
                border: '1px solid var(--neutral-border)',
                borderRadius: '8px',
              },
            }}
          />
        </QueryProvider>
      </body>
    </html>
  );
}
