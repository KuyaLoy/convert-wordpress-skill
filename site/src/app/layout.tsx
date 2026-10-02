import type { Metadata, Viewport } from "next";
import "@fontsource/ibm-plex-sans/latin-400.css";
import "@fontsource/ibm-plex-sans/latin-600.css";
import "@fontsource/ibm-plex-mono/latin-400.css";
import "@fontsource/pixelify-sans/latin-500.css";
import "@fontsource/pixelify-sans/latin-600.css";
import "@fontsource/press-start-2p/latin-400.css";
import "./globals.css";

const site = "https://kuyaloy.github.io/convert-wordpress-skill/";
const description =
  "A free Agent Skill: an AI agent rebuilds your website in WordPress, page by page, with the same look and web addresses and every word editable.";

export const metadata: Metadata = {
  metadataBase: new URL(site),
  title: "convert-to-wordpress: move any website to WordPress, 1:1",
  description,
  alternates: { canonical: site },
  openGraph: {
    type: "website",
    url: site,
    siteName: "convert-to-wordpress",
    title: "Move your old website to WordPress, 1:1",
    description,
  },
  twitter: { card: "summary", title: "Move your old website to WordPress, 1:1", description },
};

export const viewport: Viewport = { themeColor: "#0e0e0e", colorScheme: "dark" };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="dark">
      <body className="flex min-h-dvh flex-col">
        <a
          href="#main"
          className="sr-only z-50 bg-brand px-4 py-3 font-pixel text-ink focus:not-sr-only focus:fixed focus:top-3 focus:left-3"
        >
          Skip to content
        </a>
        {children}
      </body>
    </html>
  );
}
