/**
 * State → cities mapping for location dropdowns (candidate signup, profile, etc.).
 * Same data as backend server/app/shared/constants/state_cities.json — keep in sync when updating.
 */

import citiesData from './state_cities.json';

export interface CityOption {
  id: string;
  label: string;
  value: string;
}

export const CITIES: Record<string, CityOption[]> = citiesData as Record<string, CityOption[]>;

export function getStates(): string[] {
  return Object.keys(CITIES);
}

export function getCitiesByState(state: string): CityOption[] {
  return CITIES[state] ?? [];
}

/** Find state key that contains a city with the given value (exact match). */
export function getStateByCityValue(cityValue: string): string | null {
  const v = cityValue.trim();
  if (!v) return null;
  for (const [state, cities] of Object.entries(CITIES)) {
    if (cities.some((c) => c.value === v)) return state;
  }
  return null;
}

/**
 * Normalize location string for display/storage consistency.
 * - Trim and collapse spaces
 * - Take first segment if comma-separated
 * - Title-case
 */
export function normalizeLocation(value: string | null | undefined): string | null {
  if (value == null) return null;
  let s = value.trim();
  if (!s) return null;
  if (s.includes(',')) s = s.split(',')[0].trim();
  if (!s) return null;
  s = s.replace(/\s+/g, ' ');
  return s.toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
}
