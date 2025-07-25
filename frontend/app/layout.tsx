import './globals.css'
import { Inter } from 'next/font/google'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'AI Video Chaptering - Dojo Flask',
  description: 'AI-powered video chaptering application using Chapter-Llama for automatic chapter generation',
  keywords: 'video chaptering, AI, machine learning, video processing, chapters',
  authors: [{ name: 'Dojo Flask Team' }],
  openGraph: {
    title: 'AI Video Chaptering',
    description: 'AI-powered video chaptering application',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="h-full">
      <body className={`${inter.className} h-full bg-gray-50 antialiased`}>
        <div id="root" className="h-full">
          {children}
        </div>
      </body>
    </html>
  )
}
