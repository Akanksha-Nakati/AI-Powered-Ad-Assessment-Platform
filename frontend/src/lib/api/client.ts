/**
 * API client.
 *
 * Requests go to a relative /api path which Vite proxies to the backend in
 * development, so there is no hardcoded localhost:8000 to change before
 * deploying.
 */
import type {
  Assessment,
  Brand,
  Comparison,
  CorrelationResult,
  DataSourceConnection,
  KnowledgeDocument,
} from "./types";

const BASE = "/api/v1";

/** The backend's error envelope, from app/api/errors.py. */
type ErrorBody = { detail?: string; error?: string };

export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
    readonly code?: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, init);

  if (!response.ok) {
    let body: ErrorBody = {};
    try {
      body = (await response.json()) as ErrorBody;
    } catch {
      // A non-JSON error body (a proxy timeout, say) is still an error.
    }
    throw new ApiError(
      response.status,
      body.detail ?? `Request failed (${response.status})`,
      body.error,
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export type AssessInput = {
  image: File;
  platform: string;
  industry: string;
  adType: string;
  brandId?: string | null;
};

function assessmentForm(input: AssessInput, imageField: string): FormData {
  const form = new FormData();
  form.append(imageField, input.image);
  form.append("platform", input.platform);
  form.append("industry", input.industry);
  form.append("ad_type", input.adType);
  if (input.brandId) form.append("brand_id", input.brandId);
  return form;
}

export type Health = {
  status: string;
  knowledge_ready: boolean;
  vision_provider: string;
  scoring_provider: string;
};

export const api = {
  health: () => request<Health>("/health"),

  assess: (input: AssessInput) =>
    request<Assessment>("/assessments", {
      method: "POST",
      body: assessmentForm(input, "ad_image"),
    }),

  listAssessments: (limit = 20, offset = 0) =>
    request<Assessment[]>(`/assessments?limit=${limit}&offset=${offset}`),

  getAssessment: (id: string) => request<Assessment>(`/assessments/${id}`),

  tagAssessment: (id: string, externalAdId: string | null) =>
    request<Assessment>(`/assessments/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ external_ad_id: externalAdId }),
    }),

  compare: (input: Omit<AssessInput, "image"> & { images: File[] }) => {
    const form = new FormData();
    input.images.forEach((image) => form.append("ad_images", image));
    form.append("platform", input.platform);
    form.append("industry", input.industry);
    form.append("ad_type", input.adType);
    if (input.brandId) form.append("brand_id", input.brandId);
    return request<Comparison>("/comparisons", { method: "POST", body: form });
  },

  listBrands: () => request<Brand[]>("/brands"),

  createBrand: (name: string) =>
    request<Brand>("/brands", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name }),
    }),

  deleteBrand: (id: string) =>
    request<void>(`/brands/${id}`, { method: "DELETE" }),

  listDocuments: (brandId: string) =>
    request<KnowledgeDocument[]>(`/brands/${brandId}/documents`),

  uploadDocument: (brandId: string, file: File) => {
    const form = new FormData();
    form.append("document", file);
    return request<KnowledgeDocument>(`/brands/${brandId}/documents`, {
      method: "POST",
      body: form,
    });
  },

  listDataSources: () => request<DataSourceConnection[]>("/data-sources"),

  createDataSource: (input: {
    name: string;
    dialect: string;
    connectionUri: string;
    query: string;
  }) =>
    request<DataSourceConnection>("/data-sources", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: input.name,
        dialect: input.dialect,
        connection_uri: input.connectionUri,
        query: input.query,
      }),
    }),

  deleteDataSource: (id: string) =>
    request<void>(`/data-sources/${id}`, { method: "DELETE" }),

  testDataSource: (id: string) =>
    request<DataSourceConnection>(`/data-sources/${id}/test`, { method: "POST" }),

  refreshDataSource: (id: string) =>
    request<{ rows_fetched: number }>(`/data-sources/${id}/refresh`, {
      method: "POST",
    }),

  getCorrelation: (id: string) =>
    request<CorrelationResult>(`/data-sources/${id}/correlation`),
};
