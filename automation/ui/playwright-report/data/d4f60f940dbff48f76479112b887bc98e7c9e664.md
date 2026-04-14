# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: parts/create-part.spec.ts >> E2E: create → parameter → category view >> E2E-001: create part, add a parameter, verify part in category view
- Location: tests/parts/create-part.spec.ts:192:7

# Error details

```
Error: createParameterTemplateApi failed [404]: {"detail": "API endpoint not found", "url": "http://localhost:8000/api/part/parameter/template/"}
```

# Test source

```ts
  106 |   return response.json() as Promise<PartApiResponse>;
  107 | }
  108 | 
  109 | /**
  110 |  * Find a part by exact name. Returns the part pk or null if not found.
  111 |  * Uses the /api/part/?search= query parameter.
  112 |  */
  113 | export async function findPartByNameApi(
  114 |   ctx: APIRequestContext,
  115 |   name: string,
  116 | ): Promise<number | null> {
  117 |   const response = await ctx.get(`/api/part/?search=${encodeURIComponent(name)}&limit=50`);
  118 | 
  119 |   if (!response.ok()) return null;
  120 | 
  121 |   const data = (await response.json()) as PaginatedResponse<PartApiResponse>;
  122 |   const match = data.results.find((p) => p.name === name);
  123 |   return match?.pk ?? null;
  124 | }
  125 | 
  126 | /**
  127 |  * Delete a part by primary key.
  128 |  * Silently ignores 404 (already deleted) — safe to call in afterEach.
  129 |  */
  130 | export async function deletePartApi(ctx: APIRequestContext, pk: number): Promise<void> {
  131 |   const response = await ctx.delete(`/api/part/${pk}/`);
  132 | 
  133 |   if (!response.ok() && response.status() !== 404) {
  134 |     throw new Error(`deletePartApi failed [${response.status()}] for pk=${pk}`);
  135 |   }
  136 | }
  137 | 
  138 | // ── Categories ─────────────────────────────────────────────────────────────
  139 | 
  140 | /** Create a part category. Returns the new category's primary key. */
  141 | export async function createCategoryApi(
  142 |   ctx: APIRequestContext,
  143 |   name: string,
  144 |   parentPk?: number,
  145 | ): Promise<number> {
  146 |   const response = await ctx.post('/api/part/category/', {
  147 |     data: { name, parent: parentPk ?? null },
  148 |   });
  149 | 
  150 |   if (!response.ok()) {
  151 |     const body = await response.text();
  152 |     throw new Error(`createCategoryApi failed [${response.status()}]: ${body}`);
  153 |   }
  154 | 
  155 |   const cat = (await response.json()) as { pk: number };
  156 |   return cat.pk;
  157 | }
  158 | 
  159 | /**
  160 |  * Delete a category by primary key.
  161 |  * Silently ignores 404.
  162 |  */
  163 | export async function deleteCategoryApi(ctx: APIRequestContext, pk: number): Promise<void> {
  164 |   const response = await ctx.delete(`/api/part/category/${pk}/`);
  165 | 
  166 |   if (!response.ok() && response.status() !== 404) {
  167 |     throw new Error(`deleteCategoryApi failed [${response.status()}] for pk=${pk}`);
  168 |   }
  169 | }
  170 | 
  171 | // ── Stock ──────────────────────────────────────────────────────────────────
  172 | 
  173 | /** Add a stock item for the given part. Returns the stock item's pk. */
  174 | export async function addStockItemApi(
  175 |   ctx: APIRequestContext,
  176 |   partPk: number,
  177 |   quantity: number,
  178 | ): Promise<number> {
  179 |   const response = await ctx.post('/api/stock/', {
  180 |     data: { part: partPk, quantity },
  181 |   });
  182 | 
  183 |   if (!response.ok()) {
  184 |     const body = await response.text();
  185 |     throw new Error(`addStockItemApi failed [${response.status()}]: ${body}`);
  186 |   }
  187 | 
  188 |   const item = (await response.json()) as { pk: number };
  189 |   return item.pk;
  190 | }
  191 | 
  192 | // ── Parameter Templates ────────────────────────────────────────────────────
  193 | 
  194 | /** Create a parameter template. Returns its pk. */
  195 | export async function createParameterTemplateApi(
  196 |   ctx: APIRequestContext,
  197 |   name: string,
  198 |   units?: string,
  199 | ): Promise<number> {
  200 |   const response = await ctx.post('/api/part/parameter/template/', {
  201 |     data: { name, units: units ?? '' },
  202 |   });
  203 | 
  204 |   if (!response.ok()) {
  205 |     const body = await response.text();
> 206 |     throw new Error(`createParameterTemplateApi failed [${response.status()}]: ${body}`);
      |           ^ Error: createParameterTemplateApi failed [404]: {"detail": "API endpoint not found", "url": "http://localhost:8000/api/part/parameter/template/"}
  207 |   }
  208 | 
  209 |   const tmpl = (await response.json()) as { pk: number };
  210 |   return tmpl.pk;
  211 | }
  212 | 
  213 | /** Attach a parameter value to a part. Returns the parameter instance pk. */
  214 | export async function addPartParameterApi(
  215 |   ctx: APIRequestContext,
  216 |   partPk: number,
  217 |   templatePk: number,
  218 |   value: string,
  219 | ): Promise<number> {
  220 |   const response = await ctx.post('/api/part/parameter/', {
  221 |     data: { part: partPk, template: templatePk, data: value },
  222 |   });
  223 | 
  224 |   if (!response.ok()) {
  225 |     const body = await response.text();
  226 |     throw new Error(`addPartParameterApi failed [${response.status()}]: ${body}`);
  227 |   }
  228 | 
  229 |   const param = (await response.json()) as { pk: number };
  230 |   return param.pk;
  231 | }
  232 | 
  233 | // ── Utilities ──────────────────────────────────────────────────────────────
  234 | 
  235 | /**
  236 |  * Generate a unique name by appending a millisecond timestamp.
  237 |  * Prevents collisions when tests run in rapid succession.
  238 |  *
  239 |  * @example uniqueName('TestPart') → 'TestPart_1713084000123'
  240 |  */
  241 | export function uniqueName(base: string): string {
  242 |   return `${base}_${Date.now()}`;
  243 | }
  244 | 
```