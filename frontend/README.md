# Auto Foundry Frontend

React + TypeScript research workbench for Auto Foundry.

The frontend is mock-data-first and intentionally separate from the Python/FastAPI backend. It is structured so `src/lib/api.ts` can later swap the mock repository for FastAPI calls without rewriting pages.

## Stack

- Vite
- React
- TypeScript
- Tailwind CSS
- shadcn-style local UI primitives
- TanStack Table
- Recharts
- React Router

## Setup

```bash
cd frontend
npm install
npm run dev
```

Build and type-check:

```bash
npm run build
npm run lint
```

## Structure

```text
src/
  app/                 routing and workbench context
  components/layout/   sidebar, topbar, workbench shell
  components/ui/       local shadcn-style primitives
  components/tables/   TanStack Table wrapper
  data/                realistic linked mock data
  features/            page-level feature modules
  lib/                 API boundary and utility helpers
  types/               shared domain types
```

## Pages

- Overview: KPI cards, trend charts, source mix, top opportunities, fastest-rising pain points.
- Complaints: filterable evidence table and detail panel.
- Clusters: recurring pain cards and detail drawer.
- Opportunities: ranked opportunities with transparent score breakdowns and evidence drawer.
- Ideas: generated startup concepts visually separated from evidence-backed findings.
- Sources: source health and ingestion freshness.
- Runs: pipeline run history table.

## Traceability

The mock graph preserves:

```text
Idea -> Opportunity -> Problem Cluster -> Complaint -> Original Source
```

Generated ideas are intentionally marked as generated concepts and are not presented as evidence. Evidence-backed findings link back through score breakdowns, clusters, complaints, and source URLs.

## Backend Integration Later

Replace `MockWorkbenchRepository` in `src/lib/api.ts` with a FastAPI-backed implementation. Keep the existing `WorkbenchData` shape in `src/types/domain.ts` as the UI contract, or add an adapter that maps backend JSON into that shape.
