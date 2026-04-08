import { mockData } from "@/data/mockData";
import type { WorkbenchData } from "@/types/domain";

export interface WorkbenchRepository {
  getWorkbenchData(): Promise<WorkbenchData>;
}

export class MockWorkbenchRepository implements WorkbenchRepository {
  async getWorkbenchData(): Promise<WorkbenchData> {
    return mockData;
  }
}

export const repository: WorkbenchRepository = new MockWorkbenchRepository();
