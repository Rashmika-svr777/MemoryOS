import "./globals.css";
import Shell from "@/components/Shell";

export const metadata = { title: "MemoryOS", description: "AI employees that remember, learn, and collaborate." };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en"><body><Shell>{children}</Shell></body></html>
  );
}
