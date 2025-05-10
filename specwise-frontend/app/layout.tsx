import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "./globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/toaster"
import { QueryProvider } from "@/components/query-provider"
import { TasksDrawer } from "@/components/tasks-drawer"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "SPECWISE File Processor",
  description: "Process and manage files with SPECWISE",
  generator: 'specwise',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <ThemeProvider attribute="class" defaultTheme="system">
          <QueryProvider>
            <div className="relative min-h-screen">
              <TasksDrawer />
              <main className="container mx-auto py-6 px-4">{children}</main>
              <Toaster />
            </div>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}