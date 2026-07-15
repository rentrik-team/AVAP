import { MobileSidebar } from "@/components/shared/mobile-sidebar";
import { ThemeToggle } from "@/components/shared/theme-toggle";

export function AppTopbar() {
  return (
    <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-border bg-background px-4 lg:px-8">
      <div className="flex items-center gap-2 lg:hidden">
        <MobileSidebar />
      </div>
      <div className="flex-1" />
      <ThemeToggle />
    </header>
  );
}
