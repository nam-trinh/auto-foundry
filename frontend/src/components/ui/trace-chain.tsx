import { ChevronRight } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export function TraceChain({ items }: { items: string[] }) {
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs">
      {items.map((item, index) => (
        <span key={`${item}-${index}`} className="flex items-center gap-2">
          <Badge tone={index === 0 ? "purple" : index === items.length - 1 ? "green" : "blue"}>{item}</Badge>
          {index < items.length - 1 && <ChevronRight className="h-3 w-3 text-muted-foreground" />}
        </span>
      ))}
    </div>
  );
}
