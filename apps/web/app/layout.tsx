import type { Metadata } from 'next';
import { Nav } from '@/components/nav';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Legal Intent Rewriter',
  description:
    'Upload a contract and get a clause-by-clause plain-English explanation with risk flags.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="min-h-screen bg-background antialiased" suppressHydrationWarning>
        <div className="relative flex min-h-screen flex-col">
          <Nav />
          {children}
        </div>
      </body>
    </html>
  );
}
