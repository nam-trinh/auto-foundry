import { Outlet } from "react-router-dom";
import type { WorkbenchOutletContext } from "@/app/App";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

export function WorkbenchLayout({ context }: { context: WorkbenchOutletContext }) {
  return (
    <div className="workbench-grid min-h-screen bg-background">
      <div className="flex min-h-screen">
        <Sidebar />
        <main className="min-w-0 flex-1">
          <Topbar data={context.data} filters={context.filters} setFilters={context.setFilters} />
          <div className="p-5 lg:p-8">
            <Outlet context={context} />
          </div>
        </main>
      </div>
    </div>
  );
}
