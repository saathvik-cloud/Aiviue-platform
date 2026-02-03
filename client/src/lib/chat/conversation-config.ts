/**
 * Conversation Configuration for AIVI Job Creation Bot.
 * 
 * This file defines the step-by-step flow for collecting job information.
 * The frontend uses this config as a state machine - NO LLM calls during steps.
 */

import type { ChatButton } from '@/types';

// ==================== STEP DEFINITIONS ====================

export type ConversationStep =
    | 'welcome'
    | 'choose_method'
    | 'paste_jd'
    | 'extracting'
    | 'job_title'
    | 'job_requirements'
    | 'job_country'
    | 'job_state'
    | 'job_city'
    | 'job_work_type'
    | 'job_currency'
    | 'job_salary'
    | 'job_experience'
    | 'job_shift'
    | 'job_openings'
    | 'generating'
    | 'preview'
    | 'complete';

// Step metadata
export interface StepConfig {
    id: ConversationStep;
    field?: string; // Field name in collected_data
    question?: string;
    inputType: 'text' | 'textarea' | 'buttons' | 'number' | 'none';
    placeholder?: string;
    buttons?: ChatButton[];
    getButtons?: (collectedData: Record<string, any>) => ChatButton[];
    nextStep: ConversationStep | ((value: string, collectedData: Record<string, any>) => ConversationStep);
    validate?: (value: string) => boolean;
}

// ==================== LOCATION DATA ====================

export const COUNTRIES = [
    { id: 'india', label: '🇮🇳 India', value: 'India' },
    { id: 'usa', label: '🇺🇸 USA', value: 'USA' },
    { id: 'uk', label: '🇬🇧 UK', value: 'UK' },
    { id: 'other', label: '✏️ Other', value: 'other' },
];

export const STATES: Record<string, ChatButton[]> = {
    India: [
        { id: 'mh', label: 'Maharashtra', value: 'Maharashtra' },
        { id: 'ka', label: 'Karnataka', value: 'Karnataka' },
        { id: 'dl', label: 'Delhi NCR', value: 'Delhi NCR' },
        { id: 'tn', label: 'Tamil Nadu', value: 'Tamil Nadu' },
        { id: 'tg', label: 'Telangana', value: 'Telangana' },
        { id: 'gj', label: 'Gujarat', value: 'Gujarat' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    USA: [
        { id: 'ca', label: 'California', value: 'California' },
        { id: 'ny', label: 'New York', value: 'New York' },
        { id: 'tx', label: 'Texas', value: 'Texas' },
        { id: 'wa', label: 'Washington', value: 'Washington' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    UK: [
        { id: 'england', label: 'England', value: 'England' },
        { id: 'scotland', label: 'Scotland', value: 'Scotland' },
        { id: 'wales', label: 'Wales', value: 'Wales' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
};

export const CITIES: Record<string, ChatButton[]> = {
    Maharashtra: [
        { id: 'mumbai', label: 'Mumbai', value: 'Mumbai' },
        { id: 'pune', label: 'Pune', value: 'Pune' },
        { id: 'nagpur', label: 'Nagpur', value: 'Nagpur' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    Karnataka: [
        { id: 'bangalore', label: 'Bangalore', value: 'Bangalore' },
        { id: 'mysore', label: 'Mysore', value: 'Mysore' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    'Delhi NCR': [
        { id: 'delhi', label: 'New Delhi', value: 'New Delhi' },
        { id: 'gurgaon', label: 'Gurgaon', value: 'Gurgaon' },
        { id: 'noida', label: 'Noida', value: 'Noida' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    'Tamil Nadu': [
        { id: 'chennai', label: 'Chennai', value: 'Chennai' },
        { id: 'coimbatore', label: 'Coimbatore', value: 'Coimbatore' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    Telangana: [
        { id: 'hyderabad', label: 'Hyderabad', value: 'Hyderabad' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    Gujarat: [
        { id: 'ahmedabad', label: 'Ahmedabad', value: 'Ahmedabad' },
        { id: 'surat', label: 'Surat', value: 'Surat' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    California: [
        { id: 'sf', label: 'San Francisco', value: 'San Francisco' },
        { id: 'la', label: 'Los Angeles', value: 'Los Angeles' },
        { id: 'sj', label: 'San Jose', value: 'San Jose' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    'New York': [
        { id: 'nyc', label: 'New York City', value: 'New York City' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    Texas: [
        { id: 'austin', label: 'Austin', value: 'Austin' },
        { id: 'dallas', label: 'Dallas', value: 'Dallas' },
        { id: 'houston', label: 'Houston', value: 'Houston' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    Washington: [
        { id: 'seattle', label: 'Seattle', value: 'Seattle' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    England: [
        { id: 'london', label: 'London', value: 'London' },
        { id: 'manchester', label: 'Manchester', value: 'Manchester' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    Scotland: [
        { id: 'edinburgh', label: 'Edinburgh', value: 'Edinburgh' },
        { id: 'glasgow', label: 'Glasgow', value: 'Glasgow' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
    Wales: [
        { id: 'cardiff', label: 'Cardiff', value: 'Cardiff' },
        { id: 'other', label: '✏️ Other', value: 'other' },
    ],
};

// ==================== JOB OPTIONS ====================

export const WORK_TYPES: ChatButton[] = [
    { id: 'onsite', label: '🏢 On-site', value: 'onsite' },
    { id: 'remote', label: '🏠 Remote', value: 'remote' },
    { id: 'hybrid', label: '🔄 Hybrid', value: 'hybrid' },
];

export const CURRENCIES: ChatButton[] = [
    { id: 'inr', label: '₹ INR', value: 'INR' },
    { id: 'usd', label: '$ USD', value: 'USD' },
    { id: 'gbp', label: '£ GBP', value: 'GBP' },
    { id: 'eur', label: '€ EUR', value: 'EUR' },
];

export const SALARY_RANGES: Record<string, ChatButton[]> = {
    INR: [
        { id: 'inr_5_10', label: '₹5L - 10L', value: '500000-1000000' },
        { id: 'inr_10_25', label: '₹10L - 25L', value: '1000000-2500000' },
        { id: 'inr_25_50', label: '₹25L - 50L', value: '2500000-5000000' },
        { id: 'inr_50_plus', label: '₹50L+', value: '5000000-0' },
        { id: 'custom', label: '✏️ Custom', value: 'custom' },
    ],
    USD: [
        { id: 'usd_50_100', label: '$50K - 100K', value: '50000-100000' },
        { id: 'usd_100_150', label: '$100K - 150K', value: '100000-150000' },
        { id: 'usd_150_200', label: '$150K - 200K', value: '150000-200000' },
        { id: 'usd_200_plus', label: '$200K+', value: '200000-0' },
        { id: 'custom', label: '✏️ Custom', value: 'custom' },
    ],
    GBP: [
        { id: 'gbp_40_80', label: '£40K - 80K', value: '40000-80000' },
        { id: 'gbp_80_120', label: '£80K - 120K', value: '80000-120000' },
        { id: 'gbp_120_plus', label: '£120K+', value: '120000-0' },
        { id: 'custom', label: '✏️ Custom', value: 'custom' },
    ],
    EUR: [
        { id: 'eur_40_80', label: '€40K - 80K', value: '40000-80000' },
        { id: 'eur_80_120', label: '€80K - 120K', value: '80000-120000' },
        { id: 'eur_120_plus', label: '€120K+', value: '120000-0' },
        { id: 'custom', label: '✏️ Custom', value: 'custom' },
    ],
};

export const EXPERIENCE_LEVELS: ChatButton[] = [
    { id: 'fresher', label: 'Fresher (0-1 yr)', value: '0-1' },
    { id: 'junior', label: '1-3 years', value: '1-3' },
    { id: 'mid', label: '3-5 years', value: '3-5' },
    { id: 'senior', label: '5-10 years', value: '5-10' },
    { id: 'expert', label: '10+ years', value: '10-99' },
    { id: 'custom', label: '✏️ Custom', value: 'custom' },
];

export const SHIFT_PREFERENCES: ChatButton[] = [
    { id: 'day', label: '☀️ Day Shift', value: 'day' },
    { id: 'night', label: '🌙 Night Shift', value: 'night' },
    { id: 'flexible', label: '🌤️ Flexible', value: 'flexible' },
];

export const OPENINGS_COUNT: ChatButton[] = [
    { id: '1', label: '1', value: '1' },
    { id: '2', label: '2', value: '2' },
    { id: '3', label: '3', value: '3' },
    { id: '5', label: '5', value: '5' },
    { id: 'custom', label: '✏️ Custom', value: 'custom' },
];

// ==================== STEP FLOW CONFIGURATION ====================

export const CONVERSATION_STEPS: Record<ConversationStep, StepConfig> = {
    welcome: {
        id: 'welcome',
        inputType: 'none',
        nextStep: 'choose_method',
    },
    choose_method: {
        id: 'choose_method',
        question: "I'm here to help you create a job posting.\n\nHow would you like to proceed?",
        inputType: 'buttons',
        buttons: [
            { id: 'paste_jd', label: '📋 Paste JD', value: 'paste_jd' },
            { id: 'use_aivi', label: '💬 Use AIVI Bot', value: 'use_aivi' },
        ],
        nextStep: (value) => value === 'paste_jd' ? 'paste_jd' : 'job_title',
    },
    paste_jd: {
        id: 'paste_jd',
        question: 'Great! Please paste your job description below, and I\'ll extract all the details for you.',
        inputType: 'textarea',
        placeholder: 'Paste your job description here...',
        nextStep: 'extracting',
        validate: (value) => value.length >= 50,
    },
    extracting: {
        id: 'extracting',
        inputType: 'none',
        nextStep: 'preview',
    },
    job_title: {
        id: 'job_title',
        field: 'title',
        question: "Great choice! Let's create your job posting together. 🎯\n\nWhat's the job title you're hiring for?",
        inputType: 'text',
        placeholder: 'e.g., Senior Software Engineer',
        nextStep: 'job_requirements',
        validate: (value) => value.length >= 3,
    },
    job_requirements: {
        id: 'job_requirements',
        field: 'requirements',
        question: 'Nice! What skills and qualifications are you looking for?',
        inputType: 'textarea',
        placeholder: 'e.g., 5+ years in React, Node.js, PostgreSQL...',
        nextStep: 'job_country',
        validate: (value) => value.length >= 10,
    },
    job_country: {
        id: 'job_country',
        field: 'country',
        question: 'Which country is this job located in?',
        inputType: 'buttons',
        buttons: COUNTRIES,
        nextStep: 'job_state',
    },
    job_state: {
        id: 'job_state',
        field: 'state',
        question: 'Which state/region?',
        inputType: 'buttons',
        getButtons: (data) => STATES[data.country] || [{ id: 'other', label: '✏️ Enter manually', value: 'other' }],
        nextStep: 'job_city',
    },
    job_city: {
        id: 'job_city',
        field: 'city',
        question: 'Which city?',
        inputType: 'buttons',
        getButtons: (data) => CITIES[data.state] || [{ id: 'other', label: '✏️ Enter manually', value: 'other' }],
        nextStep: 'job_work_type',
    },
    job_work_type: {
        id: 'job_work_type',
        field: 'work_type',
        question: "What's the work arrangement?",
        inputType: 'buttons',
        buttons: WORK_TYPES,
        nextStep: 'job_currency',
    },
    job_currency: {
        id: 'job_currency',
        field: 'currency',
        question: 'Select the salary currency:',
        inputType: 'buttons',
        buttons: CURRENCIES,
        nextStep: 'job_salary',
    },
    job_salary: {
        id: 'job_salary',
        field: 'salary_range',
        question: 'What\'s the salary range?',
        inputType: 'buttons',
        getButtons: (data) => SALARY_RANGES[data.currency] || SALARY_RANGES.INR,
        nextStep: 'job_experience',
    },
    job_experience: {
        id: 'job_experience',
        field: 'experience_range',
        question: 'What experience level are you looking for?',
        inputType: 'buttons',
        buttons: EXPERIENCE_LEVELS,
        nextStep: 'job_shift',
    },
    job_shift: {
        id: 'job_shift',
        field: 'shift_preference',
        question: 'Preferred shift timing?',
        inputType: 'buttons',
        buttons: SHIFT_PREFERENCES,
        nextStep: 'job_openings',
    },
    job_openings: {
        id: 'job_openings',
        field: 'openings_count',
        question: 'How many positions are you hiring for?',
        inputType: 'buttons',
        buttons: OPENINGS_COUNT,
        nextStep: 'generating',
    },
    generating: {
        id: 'generating',
        inputType: 'none',
        nextStep: 'preview',
    },
    preview: {
        id: 'preview',
        inputType: 'none',
        nextStep: 'complete',
    },
    complete: {
        id: 'complete',
        inputType: 'none',
        nextStep: 'complete',
    },
};

// ==================== HELPER FUNCTIONS ====================

/**
 * Parse salary range string to min/max values.
 * Format: "500000-1000000"
 */
export function parseSalaryRange(value: string): { min: number; max: number } {
    if (value === 'custom') return { min: 0, max: 0 };
    const [min, max] = value.split('-').map(Number);
    return { min, max };
}

/**
 * Parse experience range string to min/max values.
 * Format: "3-5"
 */
export function parseExperienceRange(value: string): { min: number; max: number } {
    if (value === 'custom') return { min: 0, max: 0 };
    const [min, max] = value.split('-').map(Number);
    return { min, max };
}

/**
 * Get the next step based on current step and value.
 */
export function getNextStep(
    currentStep: ConversationStep,
    value: string,
    collectedData: Record<string, any>
): ConversationStep {
    const config = CONVERSATION_STEPS[currentStep];
    if (!config) return 'welcome';

    if (typeof config.nextStep === 'function') {
        return config.nextStep(value, collectedData);
    }
    return config.nextStep;
}

/**
 * Get buttons for a step (static or dynamic).
 */
export function getStepButtons(
    step: ConversationStep,
    collectedData: Record<string, any>
): ChatButton[] {
    const config = CONVERSATION_STEPS[step];
    if (!config) return [];

    if (config.getButtons) {
        return config.getButtons(collectedData);
    }
    return config.buttons || [];
}
