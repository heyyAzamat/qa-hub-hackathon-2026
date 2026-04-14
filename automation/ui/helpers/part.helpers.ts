/**
 * API-level helpers for InvenTree's REST API.
 *
 * Tests use these for fast, reliable setup (beforeAll/beforeEach) and
 * teardown (afterAll/afterEach) without touching the UI.
 * All requests use HTTP Basic auth so they work independently of any
 * browser session — no CSRF token is required for BasicAuth.
 *
 * InvenTree REST API root: /api/
 * Reference: https://docs.inventree.org/en/stable/api/
 */
import { APIRequestContext, request as globalRequest } from '@playwright/test';

// ── Constants ──────────────────────────────────────────────────────────────

export const BASE_URL = 'http://localhost:8000';

export const BASIC_AUTH_HEADER = {
  Authorization: `Basic ${Buffer.from('admin:inventree').toString('base64')}`,
} as const;

// ── Types ──────────────────────────────────────────────────────────────────

export interface PartCreateData {
  name: string;
  category: number;
  ipn?: string;
  description?: string;
  active?: boolean;
  virtual?: boolean;
  is_template?: boolean;
  assembly?: boolean;
  component?: boolean;
  trackable?: boolean;
  purchaseable?: boolean;
  saleable?: boolean;
  units?: string;
  revision?: string;
}

export interface PartApiResponse {
  pk: number;
  name: string;
  full_name: string;
  active: boolean;
  virtual: boolean;
  is_template: boolean;
  assembly: boolean;
  component: boolean;
  trackable: boolean;
  purchaseable: boolean;
  saleable: boolean;
  category: number;
  in_stock: number;
  revision: string | null;
}

interface PaginatedResponse<T> {
  count: number;
  results: T[];
}

// ── Factories ──────────────────────────────────────────────────────────────

/** Create a shared API request context authenticated as admin. */
export async function makeApiContext(): Promise<APIRequestContext> {
  return globalRequest.newContext({
    baseURL: BASE_URL,
    extraHTTPHeaders: { ...BASIC_AUTH_HEADER, 'Content-Type': 'application/json' },
  });
}

// ── Parts ──────────────────────────────────────────────────────────────────

/** Create a part via REST API. Returns the new part's primary key. */
export async function createPartApi(
  ctx: APIRequestContext,
  data: PartCreateData,
): Promise<number> {
  const response = await ctx.post('/api/part/', {
    data: {
      active: true,
      component: true,
      purchaseable: true,
      ...data,
    },
  });

  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`createPartApi failed [${response.status()}]: ${body}`);
  }

  const part = (await response.json()) as PartApiResponse;
  return part.pk;
}

/** Fetch a single part by primary key. */
export async function getPartApi(ctx: APIRequestContext, pk: number): Promise<PartApiResponse> {
  const response = await ctx.get(`/api/part/${pk}/`);

  if (!response.ok()) {
    throw new Error(`getPartApi failed [${response.status()}] for pk=${pk}`);
  }

  return response.json() as Promise<PartApiResponse>;
}

/**
 * Find a part by exact name. Returns the part pk or null if not found.
 * Uses the /api/part/?search= query parameter.
 */
export async function findPartByNameApi(
  ctx: APIRequestContext,
  name: string,
): Promise<number | null> {
  const response = await ctx.get(`/api/part/?search=${encodeURIComponent(name)}&limit=50`);

  if (!response.ok()) return null;

  const data = (await response.json()) as PaginatedResponse<PartApiResponse>;
  const match = data.results.find((p) => p.name === name);
  return match?.pk ?? null;
}

/**
 * Delete a part by primary key.
 * Silently ignores 404 (already deleted) — safe to call in afterEach.
 */
export async function deletePartApi(ctx: APIRequestContext, pk: number): Promise<void> {
  const response = await ctx.delete(`/api/part/${pk}/`);

  if (!response.ok() && response.status() !== 404) {
    throw new Error(`deletePartApi failed [${response.status()}] for pk=${pk}`);
  }
}

// ── Categories ─────────────────────────────────────────────────────────────

/** Create a part category. Returns the new category's primary key. */
export async function createCategoryApi(
  ctx: APIRequestContext,
  name: string,
  parentPk?: number,
): Promise<number> {
  const response = await ctx.post('/api/part/category/', {
    data: { name, parent: parentPk ?? null },
  });

  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`createCategoryApi failed [${response.status()}]: ${body}`);
  }

  const cat = (await response.json()) as { pk: number };
  return cat.pk;
}

/**
 * Delete a category by primary key.
 * Silently ignores 404.
 */
export async function deleteCategoryApi(ctx: APIRequestContext, pk: number): Promise<void> {
  const response = await ctx.delete(`/api/part/category/${pk}/`);

  if (!response.ok() && response.status() !== 404) {
    throw new Error(`deleteCategoryApi failed [${response.status()}] for pk=${pk}`);
  }
}

// ── Stock ──────────────────────────────────────────────────────────────────

/** Add a stock item for the given part. Returns the stock item's pk. */
export async function addStockItemApi(
  ctx: APIRequestContext,
  partPk: number,
  quantity: number,
): Promise<number> {
  const response = await ctx.post('/api/stock/', {
    data: { part: partPk, quantity },
  });

  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`addStockItemApi failed [${response.status()}]: ${body}`);
  }

  const item = (await response.json()) as { pk: number };
  return item.pk;
}

// ── Parameter Templates ────────────────────────────────────────────────────

/** Create a parameter template. Returns its pk. */
export async function createParameterTemplateApi(
  ctx: APIRequestContext,
  name: string,
  units?: string,
): Promise<number> {
  const response = await ctx.post('/api/part/parameter/template/', {
    data: { name, units: units ?? '' },
  });

  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`createParameterTemplateApi failed [${response.status()}]: ${body}`);
  }

  const tmpl = (await response.json()) as { pk: number };
  return tmpl.pk;
}

/** Attach a parameter value to a part. Returns the parameter instance pk. */
export async function addPartParameterApi(
  ctx: APIRequestContext,
  partPk: number,
  templatePk: number,
  value: string,
): Promise<number> {
  const response = await ctx.post('/api/part/parameter/', {
    data: { part: partPk, template: templatePk, data: value },
  });

  if (!response.ok()) {
    const body = await response.text();
    throw new Error(`addPartParameterApi failed [${response.status()}]: ${body}`);
  }

  const param = (await response.json()) as { pk: number };
  return param.pk;
}

// ── Utilities ──────────────────────────────────────────────────────────────

/**
 * Generate a unique name by appending a millisecond timestamp.
 * Prevents collisions when tests run in rapid succession.
 *
 * @example uniqueName('TestPart') → 'TestPart_1713084000123'
 */
export function uniqueName(base: string): string {
  return `${base}_${Date.now()}`;
}
