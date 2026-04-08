import { BarChart3, Blocks, DatabaseZap, Flame, Lightbulb, MessageSquareWarning, PlayCircle } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Overview", href: "/", icon: BarChart3 },
  { label: "Complaints", href: "/complaints", icon: MessageSquareWarning },
  { label: "Clusters", href: "/clusters", icon: Blocks },
  { label: "Opportunities", href: "/opportunities", icon: Flame },
  { label: "Ideas", href: "/ideas", icon: Lightbulb },
  { label: "Sources", href: "/sources", icon: DatabaseZap },
  { label: "Runs", href: "/runs", icon: PlayCircle },
];

export function Sidebar() {
  return (
    <aside className="hidden min-h-screen w-72 shrink-0 border-r border-border bg-card/70 p-5 lg:block">
      <div className="mb-8">
        <p className="text-xs uppercase tracking-[0.35em] text-muted-foreground">Auto Foundry</p>
        <h1 className="mt-2 text-2xl font-semibold">Research Workbench</h1>
      </div>
      <nav className="space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.href}
            to={item.href}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-muted-foreground transition hover:bg-muted hover:text-foreground",
                isActive && "bg-primary/15 text-blue-100 ring-1 ring-primary/30",
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="mt-8 rounded-2xl border border-border bg-background/60 p-4">
        <p className="text-sm font-medium">Traceability rule</p>
        <p className="mt-2 text-xs leading-5 text-muted-foreground">
          Every generated idea links back to an opportunity, cluster, complaint, and original source.
        </p>
      </div>
    </aside>
  );
}
