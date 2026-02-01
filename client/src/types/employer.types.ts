/**
 * Employer Types
 */

import type { BaseEntity } from './api.types';

// Employer Entity
export interface Employer extends BaseEntity {
  name: string;
  email: string;
  phone?: string;
  company_name: string;
  company_description?: string;
  company_website?: string;
  company_size?: string;
  industry?: string;
  headquarters_location?: string;
  city?: string;
  state?: string;
  country?: string;
  is_verified: boolean;
  verified_at?: string;
}

// Create Employer Request
export interface CreateEmployerRequest {
  name: string;
  email: string;
  phone?: string;
  company_name: string;
  company_description?: string;
  company_website?: string;
  company_size?: string;
  industry?: string;
  headquarters_location?: string;
  city?: string;
  state?: string;
  country?: string;
}

// Update Employer Request
export interface UpdateEmployerRequest {
  name?: string;
  phone?: string;
  company_name?: string;
  company_description?: string;
  company_website?: string;
  company_size?: string;
  industry?: string;
  headquarters_location?: string;
  city?: string;
  state?: string;
  country?: string;
  version: number;
}

// Employer Filters
export interface EmployerFilters {
  search?: string;
  company_size?: string;
  industry?: string;
  is_verified?: boolean;
  is_active?: boolean;
}
