'use client';

/**
 * Candidate Profile Page - Full Profile Management
 *
 * Features:
 * - Profile photo upload with crop (placeholder for now)
 * - Personal information (email, DOB)
 * - Job preferences (category, role, location)
 * - Languages known (multi-select)
 * - About section (textarea)
 * - Salary information
 * - Document details (Aadhaar, PAN with masking)
 * - Optimistic locking with version
 * - Auto-save feedback
 *
 * Design: Glassmorphism cards with teal accents (candidate theme)
 */

import { CANDIDATE_VALIDATION } from '@/constants';
import { useJobCategories, useRolesByCategory, useUpdateCandidate } from '@/lib/hooks';
import { uploadProfilePhoto } from '@/lib/supabase';
import { getInitials } from '@/lib/utils';
import { useCandidateAuthStore } from '@/stores';
import type { CandidateUpdateRequest, JobCategory, JobRole } from '@/types';
import {
  AlertCircle,
  Briefcase,
  Calendar,
  Camera,
  Check,
  CreditCard,
  Globe,
  IndianRupee,
  Loader2,
  Mail,
  MapPin,
  Phone,
  Save,
  Shield,
  User
} from 'lucide-react';
import Image from 'next/image';
import { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

// ==================== TYPES ====================

interface ProfileFormData {
  name: string;
  email: string;
  date_of_birth: string;
  current_location: string;
  preferred_job_category_id: string;
  preferred_job_role_id: string;
  preferred_job_location: string;
  languages_known: string[];
  about: string;
  current_monthly_salary: string;
  aadhaar_number: string;
  pan_number: string;
}

const COMMON_LANGUAGES = [
  'Hindi',
  'English',
  'Tamil',
  'Telugu',
  'Kannada',
  'Malayalam',
  'Marathi',
  'Bengali',
  'Gujarati',
  'Punjabi',
  'Odia',
  'Assamese',
  'Urdu',
];

const INDIAN_CITIES = [
  'Mumbai',
  'Delhi NCR',
  'Bangalore',
  'Hyderabad',
  'Chennai',
  'Kolkata',
  'Pune',
  'Ahmedabad',
  'Jaipur',
  'Lucknow',
  'Chandigarh',
  'Kochi',
  'Coimbatore',
  'Indore',
  'Bhopal',
  'Nagpur',
  'Surat',
  'Visakhapatnam',
];

// ==================== COMPONENT ====================

export default function CandidateProfilePage() {
  const candidate = useCandidateAuthStore((state) => state.candidate);
  const setCandidate = useCandidateAuthStore((state) => state.setCandidate);

  const updateCandidateMutation = useUpdateCandidate();
  const { data: categories, isLoading: categoriesLoading } = useJobCategories();

  // Get roles when category changes
  const [selectedCategoryId, setSelectedCategoryId] = useState<string>('');
  const { data: roles, isLoading: rolesLoading } = useRolesByCategory(
    selectedCategoryId || undefined
  );

  // Form state
  const [formData, setFormData] = useState<ProfileFormData>({
    name: '',
    email: '',
    date_of_birth: '',
    current_location: '',
    preferred_job_category_id: '',
    preferred_job_role_id: '',
    preferred_job_location: '',
    languages_known: [],
    about: '',
    current_monthly_salary: '',
    aadhaar_number: '',
    pan_number: '',
  });

  const [errors, setErrors] = useState<Partial<Record<keyof ProfileFormData, string>>>({});
  const [isDirty, setIsDirty] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isUploadingPhoto, setIsUploadingPhoto] = useState(false);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initialize form from candidate data
  useEffect(() => {
    if (candidate) {
      setFormData({
        name: candidate.name || '',
        email: candidate.email || '',
        date_of_birth: candidate.date_of_birth || '',
        current_location: candidate.current_location || '',
        preferred_job_category_id: candidate.preferred_job_category_id || '',
        preferred_job_role_id: candidate.preferred_job_role_id || '',
        preferred_job_location: candidate.preferred_job_location || '',
        languages_known: candidate.languages_known || [],
        about: candidate.about || '',
        current_monthly_salary: candidate.current_monthly_salary?.toString() || '',
        aadhaar_number: '', // Don't populate encrypted values
        pan_number: '',
      });
      setSelectedCategoryId(candidate.preferred_job_category_id || '');
    }
  }, [candidate]);

  // Sync photo preview from store (on load or when candidate/photo URL changes). Don't overwrite when user has a pending file.
  useEffect(() => {
    if (!candidate) {
      setPhotoPreview(null);
      setPhotoFile(null);
      return;
    }
    setPhotoPreview((prev) => {
      if (prev?.startsWith('blob:')) return prev; // keep local preview when photoFile is set
      return candidate.profile_photo_url || null;
    });
  }, [candidate]);

  // ==================== HANDLERS ====================

  const handleInputChange = useCallback(
    (field: keyof ProfileFormData, value: string | string[]) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
      setIsDirty(true);

      // Clear error when user starts typing
      if (errors[field]) {
        setErrors((prev) => ({ ...prev, [field]: undefined }));
      }

      // Handle category change
      if (field === 'preferred_job_category_id' && typeof value === 'string') {
        setSelectedCategoryId(value);
        // Reset role when category changes
        setFormData((prev) => ({ ...prev, preferred_job_role_id: '' }));
      }
    },
    [errors]
  );

  const handleLanguageToggle = useCallback((language: string) => {
    setFormData((prev) => {
      const current = prev.languages_known;
      const updated = current.includes(language)
        ? current.filter((l) => l !== language)
        : [...current, language];
      return { ...prev, languages_known: updated };
    });
    setIsDirty(true);
  }, []);

  const validateForm = useCallback((): boolean => {
    const newErrors: Partial<Record<keyof ProfileFormData, string>> = {};

    // Required fields
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    }

    // Email validation
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Invalid email format';
    }

    // DOB validation (must be 18+)
    if (formData.date_of_birth) {
      const dob = new Date(formData.date_of_birth);
      const today = new Date();
      const age = today.getFullYear() - dob.getFullYear();
      if (age < 18) {
        newErrors.date_of_birth = 'You must be at least 18 years old';
      }
    }

    // Aadhaar validation (12 digits)
    if (formData.aadhaar_number && !/^\d{12}$/.test(formData.aadhaar_number.replace(/\s/g, ''))) {
      newErrors.aadhaar_number = 'Aadhaar must be 12 digits';
    }

    // PAN validation (ABCDE1234F format)
    if (formData.pan_number && !/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(formData.pan_number.toUpperCase())) {
      newErrors.pan_number = 'Invalid PAN format (e.g., ABCDE1234F)';
    }

    // Salary validation
    if (formData.current_monthly_salary) {
      const salary = parseFloat(formData.current_monthly_salary);
      if (isNaN(salary) || salary < 0) {
        newErrors.current_monthly_salary = 'Invalid salary amount';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [formData]);

  const handleSubmit = async () => {
    if (!candidate) {
      toast.error('Please login first');
      return;
    }

    if (!validateForm()) {
      toast.error('Please fix the errors before saving');
      return;
    }

    setIsSaving(true);

    try {
      let profilePhotoUrl: string | undefined = candidate.profile_photo_url ?? undefined;

      // Upload new photo to Supabase if user selected one (employer-style: save on Submit)
      if (photoFile) {
        setIsUploadingPhoto(true);
        try {
          profilePhotoUrl = await uploadProfilePhoto(photoFile, candidate.id);
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Photo upload failed';
          setPhotoError(msg);
          toast.error(msg);
          setIsUploadingPhoto(false);
          setIsSaving(false);
          return;
        }
        setIsUploadingPhoto(false);
      }

      const updateData: CandidateUpdateRequest = {
        name: formData.name,
        email: formData.email || undefined,
        date_of_birth: formData.date_of_birth || undefined,
        current_location: formData.current_location || undefined,
        preferred_job_category_id: formData.preferred_job_category_id || undefined,
        preferred_job_role_id: formData.preferred_job_role_id || undefined,
        preferred_job_location: formData.preferred_job_location || undefined,
        languages_known: formData.languages_known.length > 0 ? formData.languages_known : undefined,
        about: formData.about || undefined,
        current_monthly_salary: formData.current_monthly_salary
          ? parseFloat(formData.current_monthly_salary)
          : undefined,
        aadhaar_number: formData.aadhaar_number || undefined,
        pan_number: formData.pan_number?.toUpperCase() || undefined,
        profile_photo_url: profilePhotoUrl,
        version: candidate.version,
      };

      const updatedCandidate = await updateCandidateMutation.mutateAsync({
        id: candidate.id,
        data: updateData,
      });

      // Update store and local photo state so profile box shows saved image (like employer)
      setCandidate(updatedCandidate);
      setPhotoPreview(updatedCandidate.profile_photo_url || null);
      if (photoPreview?.startsWith('blob:')) URL.revokeObjectURL(photoPreview);
      setPhotoFile(null);
      setPhotoError(null);
      setIsDirty(false);

      // Clear sensitive fields after save
      setFormData((prev) => ({
        ...prev,
        aadhaar_number: '',
        pan_number: '',
      }));

      toast.success('Profile updated successfully! ✅');
    } catch (error) {
      console.error('[Profile] Update failed:', error);
      if ((error as { status?: number })?.status === 409) {
        toast.error('Profile was updated elsewhere. Please refresh and try again.');
      } else {
        toast.error(error instanceof Error ? error.message : 'Failed to update profile');
      }
    } finally {
      setIsSaving(false);
    }
  };

  // ==================== RENDER HELPER ====================

  const renderSection = (
    title: string,
    icon: React.ReactNode,
    children: React.ReactNode
  ) => (
    <div
      className="rounded-2xl p-6"
      style={{
        background: 'rgba(255, 255, 255, 0.9)',
        backdropFilter: 'blur(12px)',
        border: '1px solid var(--neutral-border)',
        boxShadow: '0 4px 20px rgba(13, 148, 136, 0.05)',
      }}
    >
      <div className="flex items-center gap-3 mb-5">
        <div
          className="w-10 h-10 rounded-xl flex items-center justify-center"
          style={{ background: 'rgba(13, 148, 136, 0.1)' }}
        >
          {icon}
        </div>
        <h3 className="text-lg font-semibold" style={{ color: 'var(--text-primary)' }}>
          {title}
        </h3>
      </div>
      {children}
    </div>
  );

  const renderInput = (
    field: keyof ProfileFormData,
    label: string,
    icon: React.ReactNode,
    type: string = 'text',
    placeholder: string = '',
    disabled: boolean = false
  ) => (
    <div className="space-y-2">
      <label className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
        {label}
      </label>
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--neutral-gray)' }}>
          {icon}
        </div>
        <input
          type={type}
          value={formData[field] as string}
          onChange={(e) => handleInputChange(field, e.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          className={`w-full pl-10 pr-4 py-3 rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-teal-500/30 ${disabled ? 'opacity-70 cursor-not-allowed' : ''
            }`}
          style={{
            background: 'rgba(246, 239, 214, 0.5)',
            border: errors[field] ? '1px solid var(--status-closed)' : '1px solid var(--neutral-border)',
            color: 'var(--text-primary)',
          }}
        />
      </div>
      {errors[field] && (
        <p className="text-xs flex items-center gap-1" style={{ color: 'var(--status-closed)' }}>
          <AlertCircle className="w-3 h-3" />
          {errors[field]}
        </p>
      )}
    </div>
  );

  const renderSelect = (
    field: keyof ProfileFormData,
    label: string,
    icon: React.ReactNode,
    options: { value: string; label: string }[],
    placeholder: string = 'Select...',
    isLoading: boolean = false
  ) => (
    <div className="space-y-2">
      <label className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
        {label}
      </label>
      <div className="relative">
        <div className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--neutral-gray)' }}>
          {icon}
        </div>
        <select
          value={formData[field] as string}
          onChange={(e) => handleInputChange(field, e.target.value)}
          disabled={isLoading}
          className="w-full pl-10 pr-4 py-3 rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-teal-500/30 appearance-none cursor-pointer"
          style={{
            background: 'rgba(246, 239, 214, 0.5)',
            border: '1px solid var(--neutral-border)',
            color: 'var(--text-primary)',
          }}
        >
          <option value="">{isLoading ? 'Loading...' : placeholder}</option>
          {options.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
        {isLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <Loader2 className="w-4 h-4 animate-spin text-teal-500" />
          </div>
        )}
      </div>
    </div>
  );

  // ==================== RENDER ====================

  if (!candidate) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-teal-500" />
          <p style={{ color: 'var(--neutral-gray)' }}>Loading profile...</p>
        </div>
      </div>
    );
  }

  const categoryOptions: { value: string; label: string }[] = (categories || []).map(
    (cat: JobCategory) => ({ value: cat.id, label: cat.name })
  );

  const roleOptions: { value: string; label: string }[] = (roles || []).map(
    (role: JobRole) => ({ value: role.id, label: role.name })
  );

  const locationOptions = INDIAN_CITIES.map((city) => ({ value: city, label: city }));

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--text-primary)' }}>
            Profile Settings
          </h1>
          <p className="text-sm mt-1" style={{ color: 'var(--neutral-gray)' }}>
            Manage your personal information and preferences
          </p>
        </div>

        <button
          onClick={handleSubmit}
          disabled={!isDirty || isSaving || isUploadingPhoto}
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-medium text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
          style={{
            background: isDirty
              ? 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)'
              : 'var(--neutral-gray)',
          }}
        >
          {isUploadingPhoto ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Uploading photo...
            </>
          ) : isSaving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save Changes
            </>
          )}
        </button>
      </div>

      {/* Dirty indicator */}
      {isDirty && (
        <div
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm"
          style={{
            background: 'rgba(245, 158, 11, 0.1)',
            color: '#F59E0B',
          }}
        >
          <AlertCircle className="w-4 h-4" />
          You have unsaved changes
        </div>
      )}

      {/* Profile Photo Section */}
      {renderSection(
        'Profile Photo',
        <Camera className="w-5 h-5 text-teal-600" />,
        <div className="flex items-center gap-6">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0];
              e.target.value = '';
              if (!file || !candidate) return;
              setPhotoError(null);
              const maxBytes = CANDIDATE_VALIDATION.PROFILE_PHOTO_MAX_SIZE_MB * 1024 * 1024;
              if (file.size > maxBytes) {
                setPhotoError(`Photo must be under ${CANDIDATE_VALIDATION.PROFILE_PHOTO_MAX_SIZE_MB}MB`);
                toast.error(`File too large. Max ${CANDIDATE_VALIDATION.PROFILE_PHOTO_MAX_SIZE_MB}MB.`);
                return;
              }
              // Revoke previous blob if any (like employer module: store file, show preview, activate Save)
              setPhotoPreview((prev) => {
                if (prev?.startsWith('blob:')) URL.revokeObjectURL(prev);
                return null;
              });
              const blobUrl = URL.createObjectURL(file);
              setPhotoPreview(blobUrl);
              setPhotoFile(file);
              setIsDirty(true);
            }}
          />
          {/* Photo Preview: pending file → blob; else use store URL so profile box stays in sync after save (like header/sidebar) */}
          <div className="relative">
            <div
              className="w-24 h-24 rounded-2xl overflow-hidden flex items-center justify-center"
              style={{
                background: 'linear-gradient(135deg, rgba(13, 148, 136, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)',
                border: '2px solid var(--neutral-border)',
              }}
            >
              {(() => {
                const displayUrl = photoFile ? photoPreview : (candidate.profile_photo_url ?? photoPreview);
                return displayUrl ? (
                  <Image
                    src={displayUrl}
                    alt={candidate.name}
                    width={96}
                    height={96}
                    className="object-cover w-full h-full"
                    unoptimized={displayUrl.startsWith('blob:')}
                  />
                ) : (
                <div
                  className="w-full h-full flex items-center justify-center text-white text-2xl font-bold"
                  style={{ backgroundColor: 'var(--primary)' }}
                >
                  {getInitials(candidate.name || '')}
                </div>
              );
            })()}
            </div>
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploadingPhoto}
              className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full flex items-center justify-center text-white shadow-lg disabled:opacity-60"
              style={{ background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)' }}
            >
              {isUploadingPhoto ? <Loader2 className="w-4 h-4 animate-spin" /> : <Camera className="w-4 h-4" />}
            </button>
          </div>

          <div>
            <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
              Upload a professional photo
            </p>
            <p className="text-xs mt-1" style={{ color: 'var(--neutral-gray)' }}>
              JPG or PNG, max 2MB. Square images work best.
            </p>
            {photoError && (
              <p className="mt-1 text-xs text-red-600">{photoError}</p>
            )}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploadingPhoto}
              className="mt-3 px-4 py-2 rounded-lg text-sm font-medium btn-glass border border-neutral-200 hover:border-teal-300 transition-all disabled:opacity-60"
              style={{ color: 'var(--neutral-dark)' }}
            >
              {isUploadingPhoto ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin inline-block mr-2" />
                  Uploading...
                </>
              ) : (
                'Upload Photo'
              )}
            </button>
          </div>
        </div>
      )}

      {/* Personal Information */}
      {renderSection(
        'Personal Information',
        <User className="w-5 h-5 text-teal-600" />,
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {renderInput('name', 'Full Name *', <User className="w-4 h-4" />, 'text', 'Enter your name')}

          <div className="space-y-2">
            <label className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
              Mobile Number
            </label>
            <div className="relative">
              <div className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--neutral-gray)' }}>
                <Phone className="w-4 h-4" />
              </div>
              <input
                type="text"
                value={candidate.mobile}
                disabled
                className="w-full pl-10 pr-4 py-3 rounded-xl text-sm opacity-70 cursor-not-allowed"
                style={{
                  background: 'rgba(246, 239, 214, 0.5)',
                  border: '1px solid var(--neutral-border)',
                  color: 'var(--text-primary)',
                }}
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <Shield className="w-4 h-4 text-teal-500" />
              </div>
            </div>
            <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
              Mobile number cannot be changed
            </p>
          </div>

          {renderInput('email', 'Email Address', <Mail className="w-4 h-4" />, 'email', 'Enter your email')}
          {renderInput('date_of_birth', 'Date of Birth', <Calendar className="w-4 h-4" />, 'date')}
        </div>
      )}

      {/* Job Preferences */}
      {renderSection(
        'Job Preferences',
        <Briefcase className="w-5 h-5 text-teal-600" />,
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {renderSelect(
            'preferred_job_category_id',
            'Job Category',
            <Briefcase className="w-4 h-4" />,
            categoryOptions,
            'Select category',
            categoriesLoading
          )}

          {renderSelect(
            'preferred_job_role_id',
            'Job Role',
            <Briefcase className="w-4 h-4" />,
            roleOptions,
            selectedCategoryId ? 'Select role' : 'Select category first',
            rolesLoading
          )}

          {renderSelect(
            'current_location',
            'Current Location',
            <MapPin className="w-4 h-4" />,
            locationOptions,
            'Select city'
          )}

          {renderSelect(
            'preferred_job_location',
            'Preferred Job Location',
            <MapPin className="w-4 h-4" />,
            locationOptions,
            'Select preferred city'
          )}
        </div>
      )}

      {/* Languages */}
      {renderSection(
        'Languages Known',
        <Globe className="w-5 h-5 text-teal-600" />,
        <div>
          <p className="text-sm mb-4" style={{ color: 'var(--neutral-gray)' }}>
            Select all languages you can communicate in
          </p>
          <div className="flex flex-wrap gap-2">
            {COMMON_LANGUAGES.map((lang) => {
              const isSelected = formData.languages_known.includes(lang);
              return (
                <button
                  key={lang}
                  onClick={() => handleLanguageToggle(lang)}
                  className={`px-4 py-2 rounded-xl text-sm font-medium transition-all ${isSelected
                      ? 'text-white'
                      : 'btn-glass border border-neutral-200 hover:border-teal-300'
                    }`}
                  style={
                    isSelected
                      ? { background: 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)' }
                      : { color: 'var(--neutral-dark)' }
                  }
                >
                  {isSelected && <Check className="w-3 h-3 inline mr-1" />}
                  {lang}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* About */}
      {renderSection(
        'About Me',
        <User className="w-5 h-5 text-teal-600" />,
        <div className="space-y-2">
          <label className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
            Tell us about yourself
          </label>
          <textarea
            value={formData.about}
            onChange={(e) => handleInputChange('about', e.target.value)}
            placeholder="Write a brief introduction about yourself, your skills, and career goals..."
            rows={4}
            className="w-full px-4 py-3 rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-teal-500/30 resize-none"
            style={{
              background: 'rgba(246, 239, 214, 0.5)',
              border: '1px solid var(--neutral-border)',
              color: 'var(--text-primary)',
            }}
          />
          <p className="text-xs" style={{ color: 'var(--neutral-gray)' }}>
            {formData.about.length}/500 characters
          </p>
        </div>
      )}

      {/* Salary */}
      {renderSection(
        'Salary Information',
        <IndianRupee className="w-5 h-5 text-teal-600" />,
        <div className="max-w-md">
          {renderInput(
            'current_monthly_salary',
            'Current Monthly Salary (₹)',
            <IndianRupee className="w-4 h-4" />,
            'number',
            'e.g., 25000'
          )}
          <p className="text-xs mt-2" style={{ color: 'var(--neutral-gray)' }}>
            This helps us match you with suitable job opportunities
          </p>
        </div>
      )}

      {/* Documents */}
      {renderSection(
        'Identity Documents',
        <CreditCard className="w-5 h-5 text-teal-600" />,
        <div className="space-y-5">
          <div
            className="flex items-start gap-3 p-4 rounded-xl"
            style={{ background: 'rgba(13, 148, 136, 0.05)' }}
          >
            <Shield className="w-5 h-5 text-teal-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>
                Your documents are encrypted and secure
              </p>
              <p className="text-xs mt-1" style={{ color: 'var(--neutral-gray)' }}>
                We use industry-standard encryption to protect your sensitive information.
                {candidate.aadhaar_number_encrypted && ' Aadhaar: ****-****-saved'}
                {candidate.pan_number_encrypted && ' | PAN: *****saved'}
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="space-y-2">
              <label className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                Aadhaar Number
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--neutral-gray)' }}>
                  <CreditCard className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={formData.aadhaar_number}
                  onChange={(e) => {
                    // Only allow digits and limit to 12
                    const value = e.target.value.replace(/\D/g, '').slice(0, 12);
                    handleInputChange('aadhaar_number', value);
                  }}
                  placeholder={candidate.aadhaar_number_encrypted ? '****-****-saved' : '12-digit Aadhaar'}
                  className="w-full pl-10 pr-4 py-3 rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-teal-500/30"
                  style={{
                    background: 'rgba(246, 239, 214, 0.5)',
                    border: errors.aadhaar_number ? '1px solid var(--status-closed)' : '1px solid var(--neutral-border)',
                    color: 'var(--text-primary)',
                  }}
                />
              </div>
              {errors.aadhaar_number && (
                <p className="text-xs flex items-center gap-1" style={{ color: 'var(--status-closed)' }}>
                  <AlertCircle className="w-3 h-3" />
                  {errors.aadhaar_number}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium" style={{ color: 'var(--neutral-dark)' }}>
                PAN Number
              </label>
              <div className="relative">
                <div className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--neutral-gray)' }}>
                  <CreditCard className="w-4 h-4" />
                </div>
                <input
                  type="text"
                  value={formData.pan_number}
                  onChange={(e) => {
                    // Uppercase and limit to 10 chars
                    const value = e.target.value.toUpperCase().slice(0, 10);
                    handleInputChange('pan_number', value);
                  }}
                  placeholder={candidate.pan_number_encrypted ? '*****saved' : 'ABCDE1234F'}
                  className="w-full pl-10 pr-4 py-3 rounded-xl text-sm transition-all focus:outline-none focus:ring-2 focus:ring-teal-500/30"
                  style={{
                    background: 'rgba(246, 239, 214, 0.5)',
                    border: errors.pan_number ? '1px solid var(--status-closed)' : '1px solid var(--neutral-border)',
                    color: 'var(--text-primary)',
                  }}
                />
              </div>
              {errors.pan_number && (
                <p className="text-xs flex items-center gap-1" style={{ color: 'var(--status-closed)' }}>
                  <AlertCircle className="w-3 h-3" />
                  {errors.pan_number}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Bottom Save Button */}
      <div className="flex justify-end pt-4">
        <button
          onClick={handleSubmit}
          disabled={!isDirty || isSaving || isUploadingPhoto}
          className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium text-white transition-all hover:scale-105 active:scale-95 disabled:opacity-50 disabled:hover:scale-100"
          style={{
            background: isDirty
              ? 'linear-gradient(135deg, #0D9488 0%, #7C3AED 100%)'
              : 'var(--neutral-gray)',
          }}
        >
          {isUploadingPhoto ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Uploading photo...
            </>
          ) : isSaving ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" />
              Save All Changes
            </>
          )}
        </button>
      </div>
    </div>
  );
}
