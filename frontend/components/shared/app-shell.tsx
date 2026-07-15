import { AppSidebar } from "@/components/shared/app-sidebar";
import { AppTopbar } from "@/components/shared/app-topbar";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <AppSidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        <AppTopbar />
        {/* design_system.md §8 Page Spacing: mobile 16px, tablet 24px,
            desktop 32px, large desktop 40px horizontal padding. */}
        <main className="flex-1 overflow-y-auto px-4 py-7 sm:px-6 lg:px-8 lg:py-8 xl:px-10">
          {children}
        </main>
      </div>
    </div>
  );
}
