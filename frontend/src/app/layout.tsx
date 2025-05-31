import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Animated from "./components/Animated";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Data Visualizer",
  description: "LLM-powered SQL agent for dynamic data visualization",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${inter.className} min-h-screen bg-background text-white antialiased`}
      >
        <Animated>
          <main>{children}</main>
        </Animated>
      </body>
    </html>
  );
}
