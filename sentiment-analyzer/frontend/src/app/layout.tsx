import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SentimentAI — Phân tích cảm xúc",
  description: "Phân tích cảm xúc văn bản Tiếng Việt & Tiếng Anh",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body>{children}</body>
    </html>
  );
}
