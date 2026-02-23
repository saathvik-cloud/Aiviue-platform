/**
 * Interview scheduling types (employer availability, schedules, slots).
 * Matches server schemas: availability, interview_schedule, offered_slots.
 */

// 0 = Monday .. 6 = Sunday (ISO weekday)
export const SLOT_DURATION_CHOICES = [15, 30, 45] as const;
export const BUFFER_CHOICES = [5, 10, 15, 30] as const;

export interface EmployerAvailabilityResponse {
  id: string;
  employer_id: string;
  working_days: number[];
  start_time: string; // "HH:MM:SS"
  end_time: string;
  timezone: string;
  slot_duration_minutes: number;
  buffer_minutes: number;
}

export interface EmployerAvailabilityCreate {
  working_days: number[];
  start_time: string;
  end_time: string;
  timezone: string;
  slot_duration_minutes: number;
  buffer_minutes: number;
}

export interface EmployerAvailabilityUpdate {
  working_days?: number[];
  start_time?: string;
  end_time?: string;
  timezone?: string;
  slot_duration_minutes?: number;
  buffer_minutes?: number;
}

export interface GeneratedSlotResponse {
  start_utc: string; // ISO datetime
  end_utc: string;
}

export interface SendOfferRequest {
  slots: { start_utc: string; end_utc: string }[];
}

export type InterviewScheduleState =
  | 'slots_offered'
  | 'candidate_picked_slot'
  | 'employer_confirmed'
  | 'scheduled'
  | 'cancelled';

export interface InterviewScheduleResponse {
  id: string;
  job_id: string;
  application_id: string;
  employer_id: string;
  candidate_id: string;
  state: InterviewScheduleState;
  state_version: number;
  source_of_cancellation: string | null;
  chosen_slot_start_utc: string | null;
  chosen_slot_end_utc: string | null;
  offer_sent_at: string | null;
  candidate_confirmed_at: string | null;
  meeting_link: string | null;
  google_event_id: string | null;
  interview_locked_until: string | null;
  created_at: string;
  updated_at: string;
}

export interface OfferedSlotResponse {
  id: string;
  interview_schedule_id: string;
  slot_start_utc: string;
  slot_end_utc: string;
  status: 'offered' | 'confirmed' | 'released';
}

export interface OfferWithSlotsResponse {
  schedule: InterviewScheduleResponse;
  slots: OfferedSlotResponse[];
}

export interface InterviewScheduleListResponse {
  items: InterviewScheduleResponse[];
}

export interface PickSlotRequest {
  slot_id: string;
}
