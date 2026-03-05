import { Zap } from "lucide-react";

export function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-surface-800 bg-surface-950/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-lg bg-accent-600/20 text-accent-400">
            <Zap size={20} />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-surface-50 leading-tight">
              Agent Evaluation Studio
            </h1>
            <p className="text-xs text-surface-400">
              Test any agent endpoint with goal-driven conversations
            </p>
          </div>
        </div>
      </header>
      <main className="flex-1 max-w-6xl mx-auto w-full px-6 py-8">{children}</main>
    </div>
  );
}
