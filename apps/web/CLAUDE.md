# apps/web — Next.js Application

Next.js 15 App Router project. UI, auth, MongoDB persistence, orchestration.

## Architecture
- App Router (no `pages/` directory)
- Server Components by default; `"use client"` only where needed for interactivity
- Database access via Mongoose, only inside server components / route handlers
- Calls the FastAPI ML service over HTTP using `lib/ml-client.ts`

## Folder map
- `app/(auth)/`        — login/signup UI (route group, no URL prefix)
- `app/dashboard/`     — list of analyses + detailed clause view at `[id]`
- `app/upload/`        — drag-and-drop UI
- `app/api/`           — REST routes (auth, signup, documents, analyses)
- `components/ui/`     — shadcn primitives (don't edit; compose them)
- `components/`        — feature components (clause-card, risk-badge, etc.)
- `lib/db/models/`     — Mongoose schemas (one file per collection)
- `lib/ml-client.ts`   — typed client for FastAPI; calls `/v1/analyze`
- `lib/validations.ts` — zod schemas, shared by forms and route handlers
- `types/`             — shared types mirroring the FastAPI response (see @docs/api-contract.md)
- `auth.ts`            — Auth.js v5 config (top-level, not in app/)
- `middleware.ts`      — route protection

## Conventions
- TypeScript strict mode. No `any`. No `@ts-ignore` without an inline reason.
- Validate all API inputs with zod. Reuse the same schema in client forms.
- Use TanStack Query for data fetched after page load (e.g., polling analysis status).
- Tailwind for styling. No CSS modules.
- Mongoose: use the `connectDb()` singleton in `lib/db/mongoose.ts`. Never reconnect per request.

## Commands (run from this directory, or repo root with `--workspace web`)
- `npm run dev`        → dev server on :3000
- `npm run build`      → production build (run before merging to main)
- `npm run lint`       → ESLint
- `npm run typecheck`  → tsc --noEmit
- `npm run format`     → Prettier

## When adding a new MongoDB field
1. Update the Mongoose schema in `lib/db/models/`
2. Update the matching TypeScript type in `types/`
3. Update the zod schema in `lib/validations.ts` if user input is involved
4. If the field appears in FastAPI responses, update `@docs/api-contract.md` AND `apps/ml/app/schemas/`

## When adding a new API route
1. Create the route handler under `app/api/<name>/route.ts`
2. Define request validation in `lib/validations.ts` (zod)
3. Use `connectDb()` at the top of the handler
4. Return `NextResponse.json()` — never raw `Response`
