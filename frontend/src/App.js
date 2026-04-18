import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Shield, AlertTriangle, Phone, Mail, MapPin, Clock, User, Languages, CheckCircle, Bell, LogOut } from 'lucide-react';

const API = 'http://127.0.0.1:8000/api';
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [language, setLanguage] = useState('en');
  useEffect(() => { if (token) fetchUserProfile(); }, [token]);
  const fetchUserProfile = async () => {
    try { const r = await axios.get(`${API}/students/me`, { headers: { Authorization: `Bearer ${token}` } }); setUser(r.data); }
    catch { logout(); }
  };
  const login = (tok, userData) => { localStorage.setItem('token', tok); setToken(tok); setUser(userData); };
  const logout = () => { localStorage.removeItem('token'); setToken(null); setUser(null); };
  const toggleLanguage = () => setLanguage(p => p === 'en' ? 'bn' : 'en');
  return <AuthContext.Provider value={{ user, token, language, login, logout, toggleLanguage, fetchUserProfile }}>{children}</AuthContext.Provider>;
};

const useAuth = () => React.useContext(AuthContext);

const T = {
  en: { appName:'SafeTrack', tagline:'Student Safety & Emergency Support', login:'Login', register:'Register', studentId:'Student ID', password:'Password', name:'Full Name', email:'Email Address', bloodGroup:'Blood Group', location:'Current Location', emergencyContacts:'Emergency Contacts', contactName:'Contact Name', relationship:'Relationship', phone:'Phone Number', addContact:'Add Contact', emergencyAlert:'EMERGENCY ALERT', sendAlert:'Send Emergency Alert', profile:'My Profile', activeAlerts:'Active Alerts', logout:'Logout', admin:'Admin Panel', welcome:'Welcome', noAlerts:'No active alerts', alertSent:'Emergency alert sent!', updating:'Sending…', save:'Save Changes', saving:'Saving…' },
  bn: { appName:'SafeTrack', tagline:'ছাত্রছাত্রী নিরাপত্তা', login:'লগইন', register:'নিবন্ধন', studentId:'ছাত্র আইডি', password:'পাসওয়ার্ড', name:'পূর্ণ নাম', email:'ইমেইল', bloodGroup:'রক্তের গ্রুপ', location:'অবস্থান', emergencyContacts:'জরুরি যোগাযোগ', contactName:'নাম', relationship:'সম্পর্ক', phone:'ফোন', addContact:'যোগ করুন', emergencyAlert:'জরুরি সতর্কতা', sendAlert:'পাঠান', profile:'প্রোফাইল', activeAlerts:'সক্রিয়', logout:'লগআউট', admin:'অ্যাডমিন', welcome:'স্বাগতম', noAlerts:'কোন সতর্কতা নেই', alertSent:'পাঠানো হয়েছে!', updating:'পাঠানো হচ্ছে…', save:'সংরক্ষণ', saving:'সংরক্ষণ হচ্ছে…' }
};

const useT = () => { const { language } = useAuth(); return k => T[language][k] || k; };

const Header = () => {
  const { user, logout, toggleLanguage, language } = useAuth();
  const t = useT();
  return (
    <header className="app-header">
      <div className="header-inner">
        <div className="header-brand">
          <div className="header-logo"><Shield size={18} /></div>
          <div><div className="header-title">{t('appName')}</div><div className="header-subtitle">{t('tagline')}</div></div>
        </div>
        <div className="header-actions">
          <button className="btn-ghost" onClick={toggleLanguage}><Languages size={15} />{language === 'en' ? 'বাংলা' : 'English'}</button>
          {user && <><span className="header-user">{t('welcome')}, {user.name}</span><button className="btn-ghost" onClick={logout}><LogOut size={15} />{t('logout')}</button></>}
        </div>
      </div>
    </header>
  );
};

const LoginRegister = () => {
  const [tab, setTab] = useState('login');
  const [msg, setMsg] = useState({ text: '', type: '' });
  const [loading, setLoading] = useState(false);
  const { login, language } = useAuth();
  const t = useT();
  const sidRef = useRef();
  const pwdRef = useRef();
  const nameRef = useRef();
  const emailRef = useRef();
  const bgRef = useRef();
  const locRef = useRef();

  const handleSubmit = async () => {
    setLoading(true);
    setMsg({ text: '', type: '' });
    try {
      if (tab === 'login') {
        const res = await axios.post(`${API}/auth/login?lang=${language}`, {
          student_id: sidRef.current.value,
          password: pwdRef.current.value
        });
        login(res.data.access_token, res.data.user);
        window.location.href = '/';
      } else {
        await axios.post(`${API}/auth/register?lang=${language}`, {
          name: nameRef.current.value,
          student_id: sidRef.current.value,
          email: emailRef.current.value,
          password: pwdRef.current.value,
          blood_group: bgRef.current.value,
          location: locRef.current?.value || ''
        });
        setTab('login');
        setMsg({ text: 'Registered! Please login.', type: 'success' });
      }
    } catch (err) {
      setMsg({ text: err.response?.data?.detail || 'An error occurred', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-hero">
        <div className="hero-content">
          <div className="hero-badge"><Shield size={12} /> Emergency Response Platform</div>
          <h1 className="hero-title">Stay Safe. <span>Stay Connected.</span></h1>
          <p className="hero-desc">A real-time safety platform built for students — instant emergency alerts, secure authentication, and bilingual support.</p>
          <div className="hero-stats">
            <div className="stat-item"><div className="stat-number">65%</div><div className="stat-label">Faster alerts</div></div>
            <div className="stat-item"><div className="stat-number">2K+</div><div className="stat-label">Users protected</div></div>
            <div className="stat-item"><div className="stat-number">2</div><div className="stat-label">Languages</div></div>
          </div>
        </div>
      </div>
      <div className="login-form-side">
        <div className="login-form-container">
          <div className="login-logo"><div className="logo-icon"><Shield size={22} /></div><div className="logo-text">{t('appName')}</div></div>
          <h2 className="login-heading">{tab === 'login' ? 'Welcome back' : 'Create account'}</h2>
          <p className="login-subheading">{tab === 'login' ? 'Sign in to your SafeTrack account' : 'Join the safety network'}</p>
          <div className="tab-switcher">
            <button className={`tab-btn ${tab === 'login' ? 'active' : ''}`} onClick={() => setTab('login')}>{t('login')}</button>
            <button className={`tab-btn ${tab === 'register' ? 'active' : ''}`} onClick={() => setTab('register')}>{t('register')}</button>
          </div>
          {msg.text && <div className={msg.type === 'error' ? 'form-error' : 'form-success'}>{msg.text}</div>}
          {tab === 'register' && (
            <>
              <div className="form-group"><label className="form-label">{t('name')}</label><input className="form-input" ref={nameRef} /></div>
              <div className="form-group"><label className="form-label">{t('email')}</label><input className="form-input" type="email" ref={emailRef} /></div>
            </>
          )}
          <div className="form-group"><label className="form-label">{t('studentId')}</label><input className="form-input" ref={sidRef} /></div>
          <div className="form-group"><label className="form-label">{t('password')}</label><input className="form-input" type="password" ref={pwdRef} /></div>
          {tab === 'register' && (
            <>
              <div className="form-group"><label className="form-label">{t('bloodGroup')}</label><input className="form-input" ref={bgRef} placeholder="e.g. A+, B-, O+" /></div>
              <div className="form-group"><label className="form-label">{t('location')}</label><input className="form-input" ref={locRef} placeholder="Current location" /></div>
            </>
          )}
          <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
            {loading ? t('updating') : (tab === 'login' ? t('login') : t('register'))}
          </button>
        </div>
      </div>
    </div>
  );
};

const EmergencyAlert = () => {
  const [message, setMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [success, setSuccess] = useState(false);
  const { token, language } = useAuth();
  const t = useT();
  const send = async () => {
    setSending(true);
    try { await axios.post(`${API}/alerts?lang=${language}`, { message }, { headers: { Authorization: `Bearer ${token}` } }); setSuccess(true); setMessage(''); setTimeout(() => setSuccess(false), 4000); }
    catch (e) { console.error(e); } finally { setSending(false); }
  };
  return (
    <div className="emergency-card">
      <div className="emergency-icon"><AlertTriangle size={32} /></div>
      <h2 className="emergency-title">{t('emergencyAlert')}</h2>
      <p className="emergency-desc">Press the button below to instantly alert emergency responders.</p>
      {success && <div className="success-banner"><CheckCircle size={18} />{t('alertSent')}</div>}
      <textarea className="emergency-textarea" placeholder="Optional: describe your emergency…" value={message} onChange={e => setMessage(e.target.value)} rows={3} />
      <button className="btn-danger-lg" onClick={send} disabled={sending}><AlertTriangle size={20} />{sending ? t('updating') : t('sendAlert')}</button>
    </div>
  );
};

const StudentProfile = () => {
  const { user, token, fetchUserProfile, language } = useAuth();
  const [contacts, setContacts] = useState(user?.emergency_contacts || []);
  const [nc, setNc] = useState({ name:'', relationship:'', phone:'', email:'' });
  const [profile, setProfile] = useState({ name: user?.name||'', blood_group: user?.blood_group||'', location: user?.location||'' });
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const t = useT();
  const save = async () => {
    setSaving(true);
    try { await axios.put(`${API}/students/me?lang=${language}`, { ...profile, emergency_contacts: contacts }, { headers: { Authorization: `Bearer ${token}` } }); await fetchUserProfile(); setSaved(true); setTimeout(() => setSaved(false), 3000); }
    catch (e) { console.error(e); } finally { setSaving(false); }
  };
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:20 }}>
      <div className="card">
        <div className="card-title"><User size={18} /> {t('profile')}</div>
        <div className="profile-grid">
          <div className="form-group" style={{marginBottom:0}}><label className="form-label">{t('name')}</label><input className="form-input" value={profile.name} onChange={e => setProfile(p=>({...p,name:e.target.value}))} /></div>
          <div className="form-group" style={{marginBottom:0}}><label className="form-label">{t('bloodGroup')}</label><input className="form-input" value={profile.blood_group} onChange={e => setProfile(p=>({...p,blood_group:e.target.value}))} /></div>
          <div className="form-group profile-full" style={{marginBottom:0}}><label className="form-label">{t('location')}</label><input className="form-input" value={profile.location} onChange={e => setProfile(p=>({...p,location:e.target.value}))} /></div>
        </div>
      </div>
      <div className="card">
        <div className="card-title"><Phone size={18} /> {t('emergencyContacts')}</div>
        {contacts.map((c,i) => <div key={i} className="alert-item" style={{marginBottom:10}}><div style={{display:'flex',justifyContent:'space-between',alignItems:'center'}}><div><div style={{fontWeight:600,fontSize:14}}>{c.name}</div><div style={{fontSize:12,color:'var(--slate-500)'}}>{c.relationship} · {c.phone}</div></div><button className="btn-ghost" style={{color:'var(--red-600)'}} onClick={() => setContacts(p=>p.filter((_,j)=>j!==i))}>Remove</button></div></div>)}
        <div className="profile-grid" style={{marginTop:12}}>
          <div style={{marginBottom:0}}><input className="form-input" placeholder={t('contactName')} value={nc.name} onChange={e=>setNc(p=>({...p,name:e.target.value}))} /></div>
          <div style={{marginBottom:0}}><input className="form-input" placeholder={t('relationship')} value={nc.relationship} onChange={e=>setNc(p=>({...p,relationship:e.target.value}))} /></div>
          <div style={{marginBottom:0}}><input className="form-input" placeholder={t('phone')} value={nc.phone} onChange={e=>setNc(p=>({...p,phone:e.target.value}))} /></div>
          <div style={{marginBottom:0}}><input className="form-input" placeholder="Email (optional)" value={nc.email} onChange={e=>setNc(p=>({...p,email:e.target.value}))} /></div>
        </div>
        <button className="btn-secondary" style={{width:'100%',marginTop:12}} onClick={() => { if(nc.name&&nc.phone){setContacts(p=>[...p,nc]);setNc({name:'',relationship:'',phone:'',email:''});} }}>+ {t('addContact')}</button>
      </div>
      {saved && <div className="form-success" style={{display:'flex',alignItems:'center',gap:8}}><CheckCircle size={16} /> Saved!</div>}
      <button className="btn-primary" onClick={save} disabled={saving}>{saving ? t('saving') : t('save')}</button>
    </div>
  );
};

const AdminDashboard = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();
  const t = useT();
  useEffect(() => { fetchAlerts(); }, []);
  const fetchAlerts = async () => {
    try { const res = await axios.get(`${API}/alerts/active`, { headers: { Authorization: `Bearer ${token}` } }); setAlerts(res.data); }
    catch (e) { console.error(e); } finally { setLoading(false); }
  };
  const resolve = async id => {
    try { await axios.put(`${API}/alerts/${id}`, { status:'resolved' }, { headers: { Authorization: `Bearer ${token}` } }); fetchAlerts(); }
    catch (e) { console.error(e); }
  };
  if (loading) return <div className="loading-state">Loading alerts…</div>;
  return (
    <div>
      <div className="admin-header">
        <div><div className="section-heading">{t('activeAlerts')}</div><div className="section-sub">{alerts.length} alert{alerts.length!==1?'s':''} requiring attention</div></div>
        {alerts.length > 0 && <span className="count-badge">{alerts.length}</span>}
      </div>
      {alerts.length === 0 ? <div className="empty-state"><div className="empty-icon"><Bell size={24} /></div><div className="empty-title">{t('noAlerts')}</div></div>
      : alerts.map(alert => (
        <div key={alert.id} className="alert-item">
          <div className="alert-header">
            <div><div className="alert-student-name">{alert.student_name}</div><div className="alert-student-id">ID: {alert.student_id}</div></div>
            <div className="alert-time"><Clock size={12} />{new Date(alert.timestamp).toLocaleString()}</div>
          </div>
          <div className="alert-meta">
            {alert.student_email && <div className="alert-meta-item"><Mail size={12} />{alert.student_email}</div>}
            {alert.blood_group && <span className="blood-badge">⚕ {alert.blood_group}</span>}
            {alert.location && <div className="alert-meta-item"><MapPin size={12} />{alert.location}</div>}
          </div>
          {alert.message && <div className="alert-message">"{alert.message}"</div>}
          {alert.emergency_contacts?.length > 0 && <div className="contacts-list"><div className="contacts-title">{t('emergencyContacts')}</div>{alert.emergency_contacts.map((c,i) => <div key={i} className="contact-item"><Phone size={12} style={{color:'#94a3b8'}} /><span className="contact-name">{c.name}</span><span className="contact-rel">({c.relationship})</span><span>— {c.phone}</span></div>)}</div>}
          <button className="btn-resolve" onClick={() => resolve(alert.id)}><CheckCircle size={15} style={{display:'inline',marginRight:6}} />Mark as Resolved</button>
        </div>
      ))}
    </div>
  );
};

const Dashboard = () => {
  const [tab, setTab] = useState('alert');
  const { user } = useAuth();
  const t = useT();
  return (
    <div style={{minHeight:'100vh',background:'var(--slate-50)'}}>
      <Header />
      <main className="app-main">
        <nav className="nav-tabs">
          <button className={`nav-tab ${tab==='alert'?'active danger':''}`} onClick={()=>setTab('alert')}><AlertTriangle size={15}/> {t('emergencyAlert')}</button>
          <button className={`nav-tab ${tab==='profile'?'active':''}`} onClick={()=>setTab('profile')}><User size={15}/> {t('profile')}</button>
          {user?.is_admin && <button className={`nav-tab ${tab==='admin'?'active':''}`} onClick={()=>setTab('admin')}><Bell size={15}/> {t('admin')}</button>}
        </nav>
        {tab==='alert' && <EmergencyAlert />}
        {tab==='profile' && <StudentProfile />}
        {tab==='admin' && user?.is_admin && <AdminDashboard />}
      </main>
    </div>
  );
};

const ProtectedRoute = ({children}) => { const {token} = useAuth(); return token ? children : <Navigate to="/login" />; };

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginRegister />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
