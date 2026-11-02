import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PortPilot — Check your setup",
  description:
    "Evidence-backed compatibility checks for laptops and accessories.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
