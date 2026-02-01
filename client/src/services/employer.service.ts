/**
 * Employer Service - API calls for employer operations
 */

import { get, post, put, del } from '@/lib/api';
import { API_ENDPOINTS, buildQueryParams } from '@/constants';
import type {
  Employer,
  CreateEmployerRequest,
  UpdateEmployerRequest,
  EmployerFilters,
  PaginatedResponse,
} from '@/types';

// Get employer by ID
export async function getEmployerById(id: string): Promise<Employer> {
  return get<Employer>(API_ENDPOINTS.EMPLOYERS.BY_ID(id));
}

// Get employer by email
export async function getEmployerByEmail(email: string): Promise<Employer> {
  return get<Employer>(API_ENDPOINTS.EMPLOYERS.BY_EMAIL(email));
}

// Create employer
export async function createEmployer(data: CreateEmployerRequest): Promise<Employer> {
  return post<Employer>(API_ENDPOINTS.EMPLOYERS.BASE, data);
}

// Update employer
export async function updateEmployer(id: string, data: UpdateEmployerRequest): Promise<Employer> {
  return put<Employer>(API_ENDPOINTS.EMPLOYERS.BY_ID(id), data);
}

// Delete employer
export async function deleteEmployer(id: string, version: number): Promise<void> {
  return del<void>(`${API_ENDPOINTS.EMPLOYERS.BY_ID(id)}?version=${version}`);
}

// List employers
export async function listEmployers(
  filters?: EmployerFilters,
  cursor?: string,
  limit?: number
): Promise<PaginatedResponse<Employer>> {
  const params = buildQueryParams({
    ...filters,
    cursor,
    limit,
  });
  return get<PaginatedResponse<Employer>>(`${API_ENDPOINTS.EMPLOYERS.BASE}${params}`);
}
