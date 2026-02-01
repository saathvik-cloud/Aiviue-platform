'use client';

import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { COMPANY_SIZES } from '@/constants';
import { useAuthStore } from '@/stores';
import { useUpdateEmployer } from '@/lib/hooks';
import { getInitials } from '@/lib/utils';
import type { UpdateEmployerRequest } from '@/types';
import { Loader2, CheckCircle, User, Building, Mail, Phone, Globe, MapPin } from 'lucide-react';

/**
 * Profile Page - Glassmorphism design
 */
export default function ProfilePage() {
  const { employer, setEmployer } = useAuthStore();
  const updateEmployer = useUpdateEmployer();
  const [formData, setFormData] = useState<Partial<UpdateEmployerRequest>>({});

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
        version: employer.version,
      });
    }
  }, [employer]);

  const handleFieldChange = (field: keyof UpdateEmployerRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSubmit = async () => {
    if (!employer) return;
    if (!formData.name || !formData.company_name) {
      toast.error('Name and company name are required');
      return;
    }

    try {
      const updated = await updateEmployer.mutateAsync({ id: employer.id, data: formData as UpdateEmployerRequest });
      setEmployer(updated);
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

      {/* Profile Card */}
      <div className="glass-card rounded-2xl p-6 mb-6 relative overflow-hidden">
        {/* Background decoration */}
        <div 
          className="absolute top-0 right-0 w-40 h-40 rounded-full opacity-10 blur-3xl"
          style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
        />
        
        <div className="flex items-center gap-4 relative">
          <div 
            className="w-20 h-20 rounded-2xl flex items-center justify-center text-white text-2xl font-bold"
            style={{ background: 'linear-gradient(135deg, #7C3AED 0%, #EC4899 100%)' }}
          >
            {getInitials(employer.name)}
          </div>
          <div>
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
        </div>
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
              <select
                value={formData.company_size || ''}
                onChange={(e) => handleFieldChange('company_size', e.target.value)}
                className={`${inputStyle} bg-white`}
                style={{ borderColor: 'var(--neutral-border)', '--tw-ring-color': 'var(--primary)' } as React.CSSProperties}
              >
                <option value="">Select size...</option>
                {COMPANY_SIZES.map(size => (
                  <option key={size.value} value={size.value}>{size.label}</option>
                ))}
              </select>
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

          <div>
            <label className="block text-sm font-medium mb-2" style={{ color: 'var(--neutral-dark)' }}>
              <MapPin className="w-4 h-4 inline mr-1" />
              Headquarters Location
            </label>
            <input
              type="text"
              value={formData.headquarters_location || ''}
              onChange={(e) => handleFieldChange('headquarters_location', e.target.value)}
              placeholder="e.g., San Francisco, CA, USA"
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
          disabled={updateEmployer.isPending || !formData.name || !formData.company_name}
          className="btn-gradient flex items-center gap-2 px-6 py-3 rounded-xl text-sm font-medium disabled:opacity-50"
        >
          {updateEmployer.isPending ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              <CheckCircle className="w-4 h-4" />
              Save Changes
            </>
          )}
        </button>
      </div>
    </div>
  );
}
