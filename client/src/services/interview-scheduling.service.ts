/**
 * Interview scheduling service – employer availability, slots, send offer, confirm, cancel;
 * candidate: list offers, get offer with slots, pick slot, cancel.
 */

import { get, post, put, patch } from '@/lib/api';
import { API_ENDPOINTS, buildQueryParams } from '@/constants';
import type {
  EmployerAvailabilityResponse,
  EmployerAvailabilityCreate,
  EmployerAvailabilityUpdate,
  GeneratedSlotResponse,
  SendOfferRequest,
  InterviewScheduleResponse,
  OfferWithSlotsResponse,
  InterviewScheduleListResponse,
  PickSlotRequest,
} from '@/types';

const IS = API_ENDPOINTS.INTERVIEW_SCHEDULING;

// —— Employer ——

export async function getAvailability(): Promise<EmployerAvailabilityResponse> {
  return get<EmployerAvailabilityResponse>(IS.AVAILABILITY);
}

export async function setAvailability(
  body: EmployerAvailabilityCreate
): Promise<EmployerAvailabilityResponse> {
  return put<EmployerAvailabilityResponse>(IS.AVAILABILITY, body);
}

export async function updateAvailability(
  body: EmployerAvailabilityUpdate
): Promise<EmployerAvailabilityResponse> {
  return patch<EmployerAvailabilityResponse>(IS.AVAILABILITY, body);
}

export async function getScheduleForApplication(
  applicationId: string
): Promise<InterviewScheduleResponse | null> {
  try {
    return await get<InterviewScheduleResponse>(IS.SCHEDULE_BY_APPLICATION(applicationId));
  } catch (e: unknown) {
    if (typeof e === 'object' && e !== null && 'response' in e) {
      const ax = e as { response?: { status?: number } };
      if (ax.response?.status === 404) return null;
    }
    throw e;
  }
}

export async function getAvailableSlotsForApplication(
  applicationId: string,
  fromDate?: string
): Promise<GeneratedSlotResponse[]> {
  const qs = buildQueryParams({ from_date: fromDate });
  return get<GeneratedSlotResponse[]>(IS.AVAILABLE_SLOTS(applicationId) + qs);
}

export async function sendOffer(
  applicationId: string,
  body: SendOfferRequest
): Promise<InterviewScheduleResponse> {
  return post<InterviewScheduleResponse>(IS.SEND_OFFER(applicationId), body);
}

export async function employerConfirmSlot(
  applicationId: string
): Promise<InterviewScheduleResponse> {
  return post<InterviewScheduleResponse>(IS.CONFIRM_SLOT(applicationId));
}

export async function employerCancel(
  applicationId: string
): Promise<InterviewScheduleResponse> {
  return post<InterviewScheduleResponse>(IS.EMPLOYER_CANCEL(applicationId));
}

// —— Candidate ——

export async function listMyOffers(): Promise<InterviewScheduleListResponse> {
  return get<InterviewScheduleListResponse>(IS.CANDIDATE_OFFERS);
}

export async function getOfferWithSlots(
  scheduleId: string
): Promise<OfferWithSlotsResponse> {
  return get<OfferWithSlotsResponse>(IS.CANDIDATE_OFFER_BY_ID(scheduleId));
}

export async function pickSlot(
  scheduleId: string,
  body: PickSlotRequest
): Promise<InterviewScheduleResponse> {
  return post<InterviewScheduleResponse>(
    IS.CANDIDATE_PICK_SLOT(scheduleId),
    body
  );
}

export async function candidateCancel(
  scheduleId: string
): Promise<InterviewScheduleResponse> {
  return post<InterviewScheduleResponse>(IS.CANDIDATE_CANCEL(scheduleId));
}
