import { useOutletContext } from "react-router-dom";
import type { WorkbenchOutletContext } from "@/app/App";

export function useWorkbench() {
  return useOutletContext<WorkbenchOutletContext>();
}
