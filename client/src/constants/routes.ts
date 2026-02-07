/**
 * Application Routes
 */

export const ROUTES = {
  // Public Routes
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',

  // Employer Dashboard Routes
  DASHBOARD: '/dashboard',
  DASHBOARD_PROFILE: '/dashboard/profile',
  
  // Employer Jobs Routes
  JOBS: '/dashboard/jobs',
  JOB_DETAILS: (id: string) => `/dashboard/jobs/${id}`,
  JOB_NEW: '/dashboard/jobs/new',
  JOB_EDIT: (id: string) => `/dashboard/jobs/${id}/edit`,

  // Candidate Public Routes
  CANDIDATE_HOME: '/candidate',
  CANDIDATE_LOGIN: '/candidate/login',
  CANDIDATE_REGISTER: '/candidate/register',

  // Candidate Dashboard Routes
  CANDIDATE_DASHBOARD: '/candidate/dashboard',
  CANDIDATE_DASHBOARD_COMPLETE_PROFILE: '/candidate/dashboard/complete-profile',
  CANDIDATE_DASHBOARD_RESUME: '/candidate/dashboard/resume',
  CANDIDATE_DASHBOARD_RESUME_NEW: '/candidate/dashboard/resume/new',
  CANDIDATE_DASHBOARD_RESUME_HISTORY: '/candidate/dashboard/resume/history',
  CANDIDATE_DASHBOARD_RESUME_VIEW: (resumeId: string) =>
    `/candidate/dashboard/resume/history/${resumeId}`,
  CANDIDATE_DASHBOARD_PROFILE: '/candidate/dashboard/profile',
  CANDIDATE_DASHBOARD_JOBS: '/candidate/dashboard/jobs',
} as const;

// Navigation items for employer sidebar
export const NAV_ITEMS = [
  {
    label: 'Dashboard',
    href: ROUTES.DASHBOARD,
    icon: 'LayoutDashboard',
  },
  {
    label: 'Jobs',
    href: ROUTES.JOBS,
    icon: 'Briefcase',
  },
  {
    label: 'Profile',
    href: ROUTES.DASHBOARD_PROFILE,
    icon: 'User',
  },
] as const;

// Navigation items for candidate sidebar
export const CANDIDATE_NAV_ITEMS = [
  {
    label: 'Dashboard',
    href: ROUTES.CANDIDATE_DASHBOARD,
    icon: 'LayoutDashboard',
  },
  {
    label: 'Resume',
    href: ROUTES.CANDIDATE_DASHBOARD_RESUME,
    icon: 'FileText',
  },
  {
    label: 'Jobs',
    href: ROUTES.CANDIDATE_DASHBOARD_JOBS,
    icon: 'Briefcase',
  },
  {
    label: 'Profile',
    href: ROUTES.CANDIDATE_DASHBOARD_PROFILE,
    icon: 'User',
  },
] as const;

export default ROUTES;
