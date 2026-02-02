'use client';

import { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { useAuthStore } from '@/stores';
import { useUpdateEmployer } from '@/lib/hooks';
import { uploadLogo } from '@/lib/supabase';
import { getInitials } from '@/lib/utils';
import { SelectDropdown } from '@/components';
import type { UpdateEmployerRequest } from '@/types';
import { 
  Loader2, 
  User, 
  Building, 
  Mail, 
  Phone, 
  Globe, 
  MapPin, 
  Users, 
  Briefcase, 
  Building2, 
  Landmark,
  Upload,
  X,
  FileText,
  Image as ImageIcon
} from 'lucide-react';

// Company size options with icons
const COMPANY_SIZE_OPTIONS = [
  { value: '', label: 'Select company size...' },
  { value: 'startup', label: '1-10 employees (Startup)', icon: <Users className="w-4 h-4" style={{ color: 'var(--secondary-teal)' }} /> },
  { value: 'small', label: '11-50 employees (Small)', icon: <Building className="w-4 h-4" style={{ color: 'var(--primary)' }} /> },
  { value: 'medium', label: '51-200 employees (Medium)', icon: <Briefcase className="w-4 h-4" style={{ color: 'var(--accent)' }} /> },
  { value: 'large', label: '201-1000 employees (Large)', icon: <Building2 className="w-4 h-4" style={{ color: 'var(--status-published)' }} /> },
  { value: 'enterprise', label: '1000+ employees (Enterprise)', icon: <Landmark className="w-4 h-4" style={{ color: 'var(--status-pending)' }} /> },
];

/**
 * Profile Page - Glassmorphism design with logo upload
 */
export default function ProfilePage() {
  const { employer, setEmployer } = useAuthStore();
  const updateEmployer = useUpdateEmployer();
  const [formData, setFormData] = useState<Partial<UpdateEmployerRequest>>({});
  const [logoFile, setLogoFile] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const [isUploadingLogo, setIsUploadingLogo] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (employer) {
      setFormData({
        name: employer.name,
        phone: employer.phone || '',
        company_name: employer.company_name,
        company_description: employer.company_description || '',
        company_website: employer.company_website || '',
        company_size: employer.company_size || '',
        industry: employer.industry || '',
        headquarters_location: employer.headquarters_location || '',
        city: employer.city || '',
        state: employer.state || '',
        country: employer.country || '',
        gst_number: employer.gst_number || '',
        logo_url: employer.logo_url || '',
        version: employer.version,
      });
      // Set logo preview if exists
      if (employer.logo_url) {
        setLogoPreview(employer.logo_url);
      }
    }
  }, [employer]);

  const handleFieldChange = (field: keyof UpdateEmployerRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleLogoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    // Validate file type
    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      toast.error('Image size must be less than 5MB');
      return;
    }

    setLogoFile(file);
    
    // Create preview
    const reader = new FileReader();
    reader.onloadend = () => {
      setLogoPreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveLogo = () => {
    setLogoFile(null);
    setLogoPreview(employer?.logo_url || null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async () => {
    if (!employer) return;
    if (!formData.name || !formData.company_name) {
      toast.error('Name and company name are required');
      return;
    }

    try {
      let logoUrl = formData.logo_url;

      // Upload new logo if selected
      if (logoFile) {
        setIsUploadingLogo(true);
        try {
          logoUrl = await uploadLogo(logoFile, employer.id);
          toast.success('Logo uploaded successfully!');
        } catch (err) {
          console.error('Logo upload failed:', err);
          toast.error('Failed to upload logo. Please try again.');
          setIsUploadingLogo(false);
          return;
        }
        setIsUploadingLogo(false);
      }

      // Update employer with all data including logo URL
      const updated = await updateEmployer.mutateAsync({ 
        id: employer.id, 
        data: {
          ...formData,
          logo_url: logoUrl,
        } as UpdateEmployerRequest 
      });
      
      setEmployer(updated);
      // Update formData with new version to prevent 409 conflicts on next save
      setFormData(prev => ({ ...prev, version: updated.version, logo_url: updated.logo_url }));
      setLogoFile(null); // Clear file after successful upload
      toast.success('Profile updated successfully!');
    } catch {
      toast.error('Failed to update profile');
    }
  };

  const inputStyle = "w-full px-4 py-3 rounded-xl border text-sm outline-none transition-all bg-white/50 focus:bg-white focus:ring-2";

  if (!employer) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-10 h-10 rounded-full border-4 border-t-transparent animate-spin" style={{ borderColor: 'var(--primary)', borderTopColor: 'transparent' }} />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold" style={{ color: 'var(--neutral-dark)' }}>Profile Settings</h1>
        <p className="text-sm mt-1" style={{ color: 'var(--neutral-gray)' }}>Manage your account and company information</p>
      </div>

      {/* Profile Card with Logo */}
      <div className="glass-card rounded-2xl p-6 mb-6 relative overflow-hidden">
        {/* Background decoration */}
        <div 
          className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-10 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
        />
        
        <div className="flex items-center gap-4 relative">
          {/* Logo/Avatar */}
          <div className="relative group">
            {logoPreview ? (
              <img
                src={logoPreview}
                alt="Company Logo"
                className="w-20 h-20 rounded-2xl object-cover"
              />
            ) : (
              <div 
                className="w-20 h-20 rounded-2xl flex items-center justify-center text-white text-2xl font-bold"
                style={{ backgroundColor: 'var(--primary)' }}
              >
                {getInitials(employer.name)}
              </div>
            )}
            
            {/* Upload overlay */}
            <label 
              className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleLogoSelect}
                className="hidden"
              />
              <Upload className="w-6 h-6 text-white" />
            </label>
          </div>

          <div className="flex-1">
            <h2 className="text-xl font-semibold" style={{ color: 'var(--neutral-dark)' }}>{employer.name}</h2>
            <p className="text-sm flex items-center gap-1" style={{ color: 'var(--neutral-gray)' }}>
              <Mail className="w-4 h-4" />
              {employer.email}
            </p>
            <p className="text-sm flex items-center gap-1" style={{ color: 'var(--neutral-gray)' }}>
              <Building className="w-4 h-4" />
              {employer.company_name}
            </p>
          </div>

          {/* Logo actions */}
          {logoFile && (
            <button
              onClick={handleRemoveLogo}
              className="p-2 rounded-xl bg-red-50 text-red-500 hover:bg-red-100 transition-colors"
              title="Remove selected logo"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Logo upload hint */}
        <p className="text-xs mt-4" style={{ color: 'var(--neutral-gray)' }}>
          <ImageIcon className="w-3 h-3 inline mr-1" />
          Hover over the logo to upload a new one (PNG, JPG, max 5MB)
        </p>
      </div>

      {/* Personal Information */}
      <div className="glass-card rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-2 mb-5">
          <div 
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, rgba(124, 58, 237, 0.1) 0%, rgba(236, 72, 153, 0.1) 100%)' }}
          >
            <User className="w-4 h-4" style={{ color: 'var(--primary)' }} />
          </div>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--neutral-dark)' }}>Personal Information</h3>
        </div>

        <div className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Full Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.name || ''}
                onChange={(e) => handleFieldChange('name', e.target.value)}
                className={inputStyle}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Email</label>
              <div 
                className="flex items-center gap-2 px-4 py-3 rounded-xl text-sm bg-white/30"
                style={{ border: '1px solid var(--neutral-border)', color: 'var(--neutral-gray)' }}
              >
                <Mail className="w-4 h-4" />
                {employer.email}
              </div>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
              <Phone className="w-4 h-4 inline mr-1" />
              Phone Number
            </label>
            <input
              type="tel"
              value={formData.phone || ''}
              onChange={(e) => handleFieldChange('phone', e.target.value)}
              placeholder="+1-234-567-8900"
              className={inputStyle}
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>
        </div>
      </div>

      {/* Company Information */}
      <div className="glass-card rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-2 mb-5">
          <div 
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, rgba(236, 72, 153, 0.1) 0%, rgba(20, 184, 166, 0.1) 100%)' }}
          >
            <Building className="w-4 h-4" style={{ color: 'var(--accent)' }} />
          </div>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--neutral-dark)' }}>Company Information</h3>
        </div>

        <div className="space-y-4">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                Company Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={formData.company_name || ''}
                onChange={(e) => handleFieldChange('company_name', e.target.value)}
                className={inputStyle}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Industry</label>
              <input
                type="text"
                value={formData.industry || ''}
                onChange={(e) => handleFieldChange('industry', e.target.value)}
                placeholder="Technology, Healthcare, etc."
                className={inputStyle}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Company Size</label>
              <SelectDropdown
                options={COMPANY_SIZE_OPTIONS}
                value={formData.company_size || ''}
                onChange={(val) => handleFieldChange('company_size', val)}
                placeholder="Select company size..."
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
                <Globe className="w-4 h-4 inline mr-1" />
                Website
              </label>
              <input
                type="url"
                value={formData.company_website || ''}
                onChange={(e) => handleFieldChange('company_website', e.target.value)}
                placeholder="https://www.company.com"
                className={inputStyle}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
              <FileText className="w-4 h-4 inline mr-1" />
              GST Number
            </label>
            <input
              type="text"
              value={formData.gst_number || ''}
              onChange={(e) => handleFieldChange('gst_number', e.target.value)}
              placeholder="e.g., 22AAAAA0000A1Z5"
              className={inputStyle}
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Company Description</label>
            <textarea
              value={formData.company_description || ''}
              onChange={(e) => handleFieldChange('company_description', e.target.value)}
              placeholder="Brief description of your company..."
              rows={3}
              className={`${inputStyle} resize-none`}
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>
        </div>
      </div>

      {/* Location Information */}
      <div className="glass-card rounded-2xl p-6 mb-6">
        <div className="flex items-center gap-2 mb-5">
          <div 
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, rgba(124, 58, 237, 0.1) 100%)' }}
          >
            <MapPin className="w-4 h-4" style={{ color: 'var(--secondary-teal)' }} />
          </div>
          <h3 className="text-lg font-semibold" style={{ color: 'var(--neutral-dark)' }}>Location</h3>
        </div>

        <div className="space-y-4">
          <div className="grid sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>City</label>
              <input
                type="text"
                value={formData.city || ''}
                onChange={(e) => handleFieldChange('city', e.target.value)}
                placeholder="e.g., Mumbai"
                className={inputStyle}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>State</label>
              <input
                type="text"
                value={formData.state || ''}
                onChange={(e) => handleFieldChange('state', e.target.value)}
                placeholder="e.g., Maharashtra"
                className={inputStyle}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>Country</label>
              <input
                type="text"
                value={formData.country || ''}
                onChange={(e) => handleFieldChange('country', e.target.value)}
                placeholder="e.g., India"
                className={inputStyle}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
              Headquarters Location (Full Address)
            </label>
            <input
              type="text"
              value={formData.headquarters_location || ''}
              onChange={(e) => handleFieldChange('headquarters_location', e.target.value)}
              placeholder="e.g., 123 Business Park, Andheri West, Mumbai"
              className={inputStyle}
              style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
            />
          </div>
        </div>
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          onClick={handleSubmit}
          disabled={updateEmployer.isPending || isUploadingLogo || !formData.name || !formData.company_name}
          className="flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium text-white disabled:opacity-50 transition-colors hover:opacity-90"
          style={{ backgroundColor: 'var(--primary)' }}
        >
          {(updateEmployer.isPending || isUploadingLogo) ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              {isUploadingLogo ? 'Uploading Logo...' : 'Saving...'}
            </>
          ) : (
            'Save Changes'
          )}
        </button>
      </div>
    </div>
  );
}
