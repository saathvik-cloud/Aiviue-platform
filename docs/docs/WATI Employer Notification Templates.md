# WATI EMPLOYER NOTIFICATION TEMPLATES

## Template 1: Weekly Application Updates (Active Jobs)

**Template Name:** `weekly_job_applications_update`

**Trigger:** Every 7 days after job is published (recurring)

**Target:** Employers with active published jobs

---

### Template 1A: Single Job Update

**Use Case:** Employer has only 1 active job

```
Hi {{employer_name}},

Here's your weekly update for *{{job_title}}*:

*{{application_count}}* new applications this week
Total applications: *{{total_applications}}*

{{#if has_shortlisted}}
Shortlisted: *{{shortlisted_count}}*
{{/if}}

{{#if has_interviews}}
Interviews scheduled: *{{interview_count}}*
{{/if}}

View all candidates: {{job_dashboard_link}}

Need help? Reply to this message anytime.

- Team Aiviue
```

**Variables:**
- `{{employer_name}}` - Employer's first name
- `{{job_title}}` - Job title
- `{{application_count}}` - New applications in past 7 days
- `{{total_applications}}` - Total applications since job posted
- `{{shortlisted_count}}` - Number of shortlisted candidates (conditional)
- `{{interview_count}}` - Number of scheduled interviews (conditional)
- `{{job_dashboard_link}}` - Direct link to job dashboard

---

### Template 1B: Multiple Jobs Update

**Use Case:** Employer has 2+ active jobs

```
Hi {{employer_name}},

Your weekly hiring update across all jobs:

{{#each jobs}}
*{{job_title}}*
   • {{application_count}} new applications
   • {{total_applications}} total applications
   {{#if shortlisted_count}}• {{shortlisted_count}} shortlisted{{/if}}

{{/each}}

*Total across all jobs:* {{overall_total}} applications

View your dashboard: {{dashboard_link}}

Keep the momentum going!

- Team Aiviue
```

**Variables:**
- `{{employer_name}}` - Employer's first name
- `{{jobs}}` - Array of job objects, each containing:
  - `{{job_title}}` - Job title
  - `{{application_count}}` - New applications (past 7 days)
  - `{{total_applications}}` - Total applications
  - `{{shortlisted_count}}` - Shortlisted count (optional)
- `{{overall_total}}` - Sum of all applications across all jobs
- `{{dashboard_link}}` - Link to employer dashboard

---

### Template 1C: Multiple Jobs Update (Alternative - Compact)

**Use Case:** Employer has many jobs (5+), keep it concise

```
Hi {{employer_name}},

Weekly Update - You received *{{total_new_applications}}* new applications:

{{#each jobs}}
• *{{job_title}}*: {{application_count}} new
{{/each}}

Total applications: *{{overall_total}}*

View all candidates: {{dashboard_link}}

Questions? Just reply here.

- Team Aiviue
```

**Variables:**
- `{{employer_name}}` - Employer's first name
- `{{total_new_applications}}` - Sum of new applications across all jobs
- `{{jobs}}` - Array with `job_title` and `application_count`
- `{{overall_total}}` - Total applications across all jobs
- `{{dashboard_link}}` - Employer dashboard link

---

## Template 2: Job Creation Reminder (Inactive Employers)

**Template Name:** `job_creation_reminder`

**Trigger:** Day 3, Day 6, Day 9 after signup (if no job published)

**Target:** Employers who signed up but haven't published a job

---

### Template 2A: First Reminder (Day 3)

```
Hi {{employer_name}},

Welcome to Aiviue! We're excited to help you find great talent.

We noticed you haven't posted your first job yet. It takes just *2 minutes* to get started.

*Why post now?*
• AI-powered candidate matching
• Automated screening
• Video JDs that attract 3x more applicants

Ready to hire? Post your first job: {{create_job_link}}

Need help? Reply here or call us at {{support_number}}

- Team Aiviue
```

**Variables:**
- `{{employer_name}}` - Employer's first name
- `{{create_job_link}}` - Direct link to job creation page
- `{{support_number}}` - Support phone number

---

### Template 2B: Second Reminder (Day 6)

```
Hi {{employer_name}},

Still looking to hire? We'd love to help!

*Here's what you're missing:*
• AI screens candidates 24/7
• Only qualified applicants reach you
• Automated interview scheduling

{{#if has_template}}
We've saved a job template for you based on your industry ({{industry}}). Just fill in the details and publish!
{{/if}}

Post your first job now: {{create_job_link}}

Questions? Just reply - we're here to help.

- Team Aiviue
```

**Variables:**
- `{{employer_name}}` - Employer's first name
- `{{industry}}` - Employer's industry (if available)
- `{{has_template}}` - Boolean flag if template available
- `{{create_job_link}}` - Job creation link
- `{{support_number}}` - Support contact

---

### Template 2C: Final Reminder (Day 9)

```
Hi {{employer_name}},

This is our last reminder about posting your first job on Aiviue.

*Quick wins with Aiviue:*
• Post in 2 minutes
• Get qualified candidates in 24 hours
• AI handles screening automatically

We're here if you need help getting started!

Post your job: {{create_job_link}}
Or book a demo call: {{demo_link}}

Have questions? Reply here or call {{support_number}}

Thanks,
Team Aiviue

P.S. We won't send more reminders, but your account stays active. Post a job anytime you're ready!
```

**Variables:**
- `{{employer_name}}` - Employer's first name
- `{{create_job_link}}` - Job creation link
- `{{demo_link}}` - Link to schedule demo/onboarding call
- `{{support_number}}` - Support contact

---

## Implementation Notes

### Template 1: Weekly Updates
**Logic:**
```javascript
// Determine which template variant to use
if (activeJobsCount === 1) {
  sendTemplate('weekly_job_applications_update_single', data);
} else if (activeJobsCount >= 2 && activeJobsCount <= 4) {
  sendTemplate('weekly_job_applications_update_multiple', data);
} else if (activeJobsCount >= 5) {
  sendTemplate('weekly_job_applications_update_compact', data);
}
```

**Timing:**
- Send every Sunday at 10:00 AM (or Monday at 9:00 AM)
- First send: 7 days after job publication
- Stop sending if: Job is closed/paused

### Template 2: Job Creation Reminders
**Logic:**
```javascript
// Send on Day 3, 6, 9 since signup
const reminderSchedule = [
  { day: 3, template: 'job_creation_reminder_day3' },
  { day: 6, template: 'job_creation_reminder_day6' },
  { day: 9, template: 'job_creation_reminder_day9' }
];

// Stop if employer publishes a job
```

**Timing:**
- Day 3: 10:00 AM
- Day 6: 10:00 AM  
- Day 9: 10:00 AM (final reminder)

---

## WATI Setup Requirements

### Conditional Logic Support
If WATI doesn't support `{{#if}}` conditionals, create separate templates:
- `weekly_update_single_basic` (no shortlist/interview data)
- `weekly_update_single_detailed` (with shortlist/interview data)

### Message Approval
All templates need WhatsApp Business API approval before use. Submit for review with:
- Template category: "UTILITY" or "MARKETING"
- Language: English
- Sample values for all variables

### Character Limits
- Keep messages under 1024 characters
- Test with maximum variable lengths
- Consider SMS fallback for users without WhatsApp

---

## Testing Checklist

- [ ] Test with 1 job, 0 applications
- [ ] Test with 1 job, 5+ applications
- [ ] Test with 3 jobs, varying application counts
- [ ] Test with 10+ jobs (compact template)
- [ ] Test all reminder sequence (Day 3, 6, 9)
- [ ] Test variable replacement (all placeholders)
- [ ] Test link rendering (clickable)
- [ ] Check character count
- [ ] Test on different phone types
