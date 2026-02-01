/**
 * Application Routes
 */

export const ROUTES = {
  // Public Routes
  HOME: '/',
  LOGIN: '/login',
  REGISTER: '/register',

  // Dashboard Routes
  DASHBOARD: '/dashboard',
  DASHBOARD_PROFILE: '/dashboard/profile',
  
  // Jobs Routes
  JOBS: '/dashboard/jobs',
  JOB_DETAILS: (id: string) => `/dashboard/jobs/${id}`,
  JOB_NEW: '/dashboard/jobs/new',
  JOB_EDIT: (id: string) => `/dashboard/jobs/${id}/edit`,
} as const;

// Navigation items for sidebar
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

export default ROUTES;
