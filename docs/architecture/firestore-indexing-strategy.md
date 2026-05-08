# Firestore Indexing & Filtering Strategy

This document outlines a strategy to prevent "Index Explosion" in Firestore while maintaining a highly dynamic and filterable dashboard.

## The Problem: Index Explosion
Firestore requires a **Composite Index** for every unique combination of filters and sort orders used in a query. 
In a typical dashboard, users can toggle multiple filter categories and change sort orders simultaneously.

Without optimization, this requires:
`[Group Filter] * [Signal A] * [Signal B] * [Signal C] * [Sort Order]` combinations.
This results in hundreds of indexes, making deployments slow and reaching Firebase project limits.

## The Solution: The Hybrid Filtering Pattern
We use a **Hybrid Filtering** approach that splits the workload between the Firestore server and the client's browser.

### 1. Server-Side: Heavy Lifting
Firestore handles the operations that are most expensive to do on the client:
*   **Group Filtering**: Filtering by collection groups or categories (using `array-contains-any`).
*   **Sorting**: Ordering results by frequency, velocity, timestamps, etc.
*   **Pagination**: Using cursors (`startAfter`) to fetch batches of data.

**Index Requirement:** Only `[Group Field] + [Sort Field]` (approx. 10-15 indexes total).

### 2. Client-Side: Precision Filtering
The frontend performs the final refinement on the result pool:
*   **Signal Filtering**: Checking score thresholds or boolean flags.
*   **Keyword Search**: Filtering by names, summaries, or keywords.
*   **Multi-Select Logic**: Handling complex combinations that Firestore cannot do in a single query.

### 3. The "High-Quality Pool" Mechanism
To ensure the client-side filtering doesn't result in "empty pages," we use a dynamic limit:
*   **Standard View**: Fetch a small batch (e.g., 12-20 items for initial display).
*   **Filter/Search Mode**: Fetch **500 items** from the server.
*   **Result**: Even after filtering out 90% of the results on the client, the user still sees a full page of the highest-quality, most relevant topics.

## When to Create a New Index
You should **ONLY** create a new composite index if:
1.  You add a **new sorting field** (e.g., `revenue_potential`).
2.  You add a **new mandatory group filter** that must be performed on millions of documents.

**Do NOT** create an index for a new "toggle" or "score" filter. Simply add it to the client-side filtering logic.

## Implementation Reference
*   **Query Logic**: Your service layer handling Firestore queries
*   **UI Logic**: Your dashboard/listing page components
*   **Index Config**: `firestore.indexes.json`
