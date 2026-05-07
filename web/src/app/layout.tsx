import type { Metadata } from "next";
import "./globals.css";
import { QueryProvider } from "@/providers/query-provider";
import { TopNav } from "@/components/layout/top-nav";

export const metadata: Metadata = {
  title: "NewsRadar - Newsroom Intel",
  description: "AI-powered newsroom intelligence platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="zh-CN"
      className="h-full antialiased"
    >
      <body className="min-h-full flex flex-col">
        <QueryProvider>
          <TopNav />
          <main className="flex-1">{children}</main>
        </QueryProvider>
      </body>
    </html>
  );
}
