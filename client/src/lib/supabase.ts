/**
 * Supabase Client - For Storage operations
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase credentials not configured. Storage features will be disabled.');
}

export const supabase = createClient(supabaseUrl || '', supabaseAnonKey || '');

// Storage bucket names
export const LOGO_BUCKET = 'aiviue-logos';
export const RESUME_BUCKET = 'resumes';

/**
 * Upload resume PDF to Supabase Storage
 * @param file - The PDF file
 * @param sessionId - The chat session ID
 * @returns The public URL of the uploaded file
 */
export async function uploadResume(file: File, sessionId: string): Promise<string> {
  const fileExt = file.name.split('.').pop();
  const fileName = `${sessionId}-${Date.now()}.${fileExt}`;
  // Simple path for resumes
  const filePath = fileName;

  const { error: uploadError } = await supabase.storage
    .from(RESUME_BUCKET)
    .upload(filePath, file, {
      cacheControl: '3600',
      upsert: true,
    });

  if (uploadError) {
    console.error('Upload error:', uploadError);
    throw new Error(`Failed to upload resume: ${uploadError.message}`);
  }

  const { data: { publicUrl } } = supabase.storage
    .from(RESUME_BUCKET)
    .getPublicUrl(filePath);

  return publicUrl;
}

/**
 * Upload company logo to Supabase Storage
 * @param file - The file to upload
 * @param employerId - The employer's ID (used as filename)
 * @returns The public URL of the uploaded file
 */
export async function uploadLogo(file: File, employerId: string): Promise<string> {
  // Generate unique filename with employer ID
  const fileExt = file.name.split('.').pop();
  const fileName = `${employerId}.${fileExt}`;
  const filePath = `logos/${fileName}`;

  // Upload file (upsert to replace if exists)
  const { error: uploadError } = await supabase.storage
    .from(LOGO_BUCKET)
    .upload(filePath, file, {
      cacheControl: '3600',
      upsert: true, // Replace if exists
    });

  if (uploadError) {
    console.error('Upload error:', uploadError);
    throw new Error(`Failed to upload logo: ${uploadError.message}`);
  }

  // Get public URL
  const { data: { publicUrl } } = supabase.storage
    .from(LOGO_BUCKET)
    .getPublicUrl(filePath);

  return publicUrl;
}

/**
 * Delete company logo from Supabase Storage
 * @param logoUrl - The URL of the logo to delete
 */
export async function deleteLogo(logoUrl: string): Promise<void> {
  // Extract file path from URL
  const url = new URL(logoUrl);
  const pathParts = url.pathname.split('/');
  const filePath = pathParts.slice(pathParts.indexOf('logos')).join('/');

  if (!filePath) {
    throw new Error('Invalid logo URL');
  }

  const { error } = await supabase.storage
    .from(LOGO_BUCKET)
    .remove([filePath]);

  if (error) {
    console.error('Delete error:', error);
    throw new Error(`Failed to delete logo: ${error.message}`);
  }
}
