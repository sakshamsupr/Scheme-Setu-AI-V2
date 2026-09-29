import { createContext, useContext, useMemo, useState } from 'react';

const defaults = {
  name: '', age: '', gender: '', category: '', state: 'Uttar Pradesh', district: '', business_type: 'Manufacturing', loan_amount: 500000, income: '', education_status: '',
};

const ProfileContext = createContext(null);

export function ProfileProvider({ children }) {
  const [profile, setProfile] = useState(() => {
    try { return { ...defaults, ...JSON.parse(localStorage.getItem('schemeSetuProfile') || '{}') }; } catch { return defaults; }
  });
  const updateProfile = (patch) => setProfile(prev => {
    const next = { ...prev, ...patch };
    localStorage.setItem('schemeSetuProfile', JSON.stringify(next));
    return next;
  });
  const value = useMemo(() => ({ profile, updateProfile }), [profile]);
  return <ProfileContext.Provider value={value}>{children}</ProfileContext.Provider>;
}

export function useProfile() {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error('useProfile must be used inside ProfileProvider');
  return ctx;
}
