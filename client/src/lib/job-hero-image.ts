/**
 * Job hero image: map job title to a curated Unsplash image for the "Job video" placeholder.
 *
 * Why this approach is efficient:
 * - No API key or server call: we use a fixed mapping (keyword → photo ID) and direct CDN URLs.
 * - Only one network request per job view: the browser loads the image from Unsplash when the
 *   job detail page renders. useMemo in the page ensures we only recompute the URL when job.title changes.
 * - Optional: prefetchHeroImages() can be called once (e.g. in employer layout) to preload all
 *   possible hero URLs so when the user opens any job the image is often already in cache.
 */

const UNSPLASH_BASE = 'https://images.unsplash.com';

/** Keyword (lowercase) -> Unsplash photo ID (from unsplash.com, free to use with attribution). */
const TITLE_TO_PHOTO: { keywords: string[]; photoId: string }[] = [
  { keywords: ['analyst', 'analysis', 'data'], photoId: '1551288049-bebda4e38f71' },
  { keywords: ['driver', 'truck', 'delivery', 'logistics'], photoId: '1519003722824-194d4455a60c' },
  { keywords: ['sales', 'business', 'marketing'], photoId: '1560472354-b33ff0c44a43' },
  { keywords: ['plumber', 'plumbing', 'technician', 'trade'], photoId: '1581092160562-40aa08e78837' },
  { keywords: ['manager', 'team', 'lead', 'supervisor'], photoId: '1573164713988-8665fc963095' },
  { keywords: ['engineer', 'developer', 'software', 'tech'], photoId: '1498050108023-2eeaed7b3b1c' },
  { keywords: ['nurse', 'health', 'care', 'medical'], photoId: '1579684385127-1ef15d508118' },
  { keywords: ['teacher', 'trainer', 'education'], photoId: '1522202176988-66273c2fd55f' },
];

const DEFAULT_PHOTO_ID = '1497366216548-37526070297c';

const ALL_PHOTO_IDS = [DEFAULT_PHOTO_ID, ...TITLE_TO_PHOTO.map((t) => t.photoId)];

export interface JobHeroImageResult {
  src: string;
  blurDataURL: string;
}

/** Small gray blur placeholder for skeleton while image loads. */
const BLUR_PLACEHOLDER =
  'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAIAAoDASIAAhEBAxEB/8QAFgABAQEAAAAAAAAAAAAAAAAAAAUH/8QAIhAAAgEDBAMBAAAAAAAAAAAAAQIDAAQRBRIhMQYTQVFh/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAZEQACAwEAAAAAAAAAAAAAAAABAgADESH/2gAMAwEAAhEDEEA/AJ/VtY1C11O5t4Lp0ijkKqo7ApSlVWxMRbZn/9k=';

/**
 * Returns Unsplash image URL and blur placeholder for a job title.
 * Pure function: safe to call with any title; useMemo in the page avoids recomputation.
 */
export function getJobHeroImage(title: string | null | undefined): JobHeroImageResult {
  const normalized = (title ?? '').toLowerCase().trim();
  let photoId = DEFAULT_PHOTO_ID;
  for (const { keywords, photoId: id } of TITLE_TO_PHOTO) {
    if (keywords.some((k) => normalized.includes(k))) {
      photoId = id;
      break;
    }
  }
  const src = `${UNSPLASH_BASE}/photo-${photoId}?w=800&q=80`;
  return { src, blurDataURL: BLUR_PLACEHOLDER };
}

const HERO_IMAGE_URLS = [...new Set(ALL_PHOTO_IDS.map((id) => `${UNSPLASH_BASE}/photo-${id}?w=800&q=80`))];
let prefetched = false;

/**
 * Prefetch all possible job hero images in the background (one go).
 * Call once when employer area mounts (e.g. dashboard layout) so when user opens any job
 * the image is often already in browser cache. Idempotent: only runs once per session.
 */
export function prefetchHeroImages(): void {
  if (typeof window === 'undefined' || prefetched) return;
  prefetched = true;
  HERO_IMAGE_URLS.forEach((url) => {
    const img = new window.Image();
    img.src = url;
  });
}
