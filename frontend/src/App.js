import React, { useState, useEffect } from 'react';
import './App.css';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Alert, AlertDescription } from './components/ui/alert';
import { Separator } from './components/ui/separator';
import { Shield, AlertTriangle, Users, Phone, Mail, MapPin, Clock, User, Languages } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [language, setLanguage] = useState('en');

  useEffect(() => {
    if (token) {
      fetchUserProfile();
    }
  }, [token]);

  const fetchUserProfile = async () => {
    try {
      const response = await axios.get(`${API}/students/me`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setUser(response.data);
    } catch (error) {
      console.error('Failed to fetch user profile:', error);
      logout();
    }
  };

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    setToken(token);
    setUser(userData);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const toggleLanguage = () => {
    setLanguage(prev => prev === 'en' ? 'bn' : 'en');
  };

  return (
    <AuthContext.Provider value={{ user, token, language, login, logout, toggleLanguage, fetchUserProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = React.useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Translations
const translations = {
  en: {
    appName: 'SafeTrack',
    tagline: 'Student Safety & Emergency Support',
    login: 'Login',
    register: 'Register',
    studentId: 'Student ID',
    password: 'Password',
    name: 'Full Name',
    email: 'Email Address',
    bloodGroup: 'Blood Group',
    location: 'Current Location',
    emergencyContacts: 'Emergency Contacts',
    contactName: 'Contact Name',
    relationship: 'Relationship',
    phone: 'Phone Number',
    addContact: 'Add Emergency Contact',
    emergencyAlert: 'EMERGENCY ALERT',
    sendAlert: 'Send Emergency Alert',
    profile: 'My Profile',
    dashboard: 'Emergency Dashboard',
    activeAlerts: 'Active Alerts',
    logout: 'Logout',
    admin: 'Admin Panel',
    welcome: 'Welcome',
    noAlerts: 'No active alerts',
    alertSent: 'Emergency alert sent successfully!',
    updating: 'Updating...',
    save: 'Save Changes'
  },
  bn: {
    appName: 'SafeTrack',
    tagline: 'ছাত্রছাত্রী নিরাপত্তা ও জরুরি সহায়তা',
    login: 'লগইন',
    register: 'নিবন্ধন',
    studentId: 'ছাত্র আইডি',
    password: 'পাসওয়ার্ড',
    name: 'পূর্ণ নাম',
    email: 'ইমেইল ঠিকানা',
    bloodGroup: 'রক্তের গ্রুপ',
    location: 'বর্তমান অবস্থান',
    emergencyContacts: 'জরুরি যোগাযোগ',
    contactName: 'যোগাযোগকারীর নাম',
    relationship: 'সম্পর্ক',
    phone: 'ফোন নম্বর',
    addContact: 'জরুরি যোগাযোগ যোগ করুন',
    emergencyAlert: 'জরুরি সতর্কতা',
    sendAlert: 'জরুরি সতর্কতা পাঠান',
    profile: 'আমার প্রোফাইল',
    dashboard: 'জরুরি ড্যাশবোর্ড',
    activeAlerts: 'সক্রিয় সতর্কতা',
    logout: 'লগআউট',
    admin: 'অ্যাডমিন প্যানেল',
    welcome: 'স্বাগতম',
    noAlerts: 'কোন সক্রিয় সতর্কতা নেই',
    alertSent: 'জরুরি সতর্কতা সফলভাবে পাঠানো হয়েছে!',
    updating: 'আপডেট হচ্ছে...',
    save: 'পরিবর্তন সংরক্ষণ করুন'
  }
};

const useTranslation = () => {
  const { language } = useAuth();
  const t = (key) => translations[language][key] || key;
  return { t, language };
};

// Components
const Header = () => {
  const { user, logout, toggleLanguage } = useAuth();
  const { t, language } = useTranslation();

  return (
    <header className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <Shield className="h-8 w-8 text-red-600" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">{t('appName')}</h1>
              <p className="text-xs text-gray-600">{t('tagline')}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <Button 
              variant="outline" 
              size="sm" 
              onClick={toggleLanguage}
              className="flex items-center space-x-1"
            >
              <Languages className="h-4 w-4" />
              <span>{language === 'en' ? 'বাংলা' : 'English'}</span>
            </Button>
            
            {user && (
              <>
                <span className="text-sm text-gray-700">{t('welcome')}, {user.name}</span>
                <Button variant="outline" size="sm" onClick={logout}>
                  {t('logout')}
                </Button>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

const LoginRegister = () => {
  const [activeTab, setActiveTab] = useState('login');
  const [formData, setFormData] = useState({
    studentId: '',
    password: '',
    name: '',
    email: '',
    bloodGroup: '',
    location: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, language } = useAuth();
  const { t } = useTranslation();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      if (activeTab === 'login') {
        const response = await axios.post(`${API}/auth/login?lang=${language}`, {
          student_id: formData.studentId,
          password: formData.password
        });
        login(response.data.access_token, response.data.user);
      } else {
        await axios.post(`${API}/auth/register?lang=${language}`, {
          name: formData.name,
          student_id: formData.studentId,
          email: formData.email,
          password: formData.password,
          blood_group: formData.bloodGroup,
          location: formData.location
        });
        setActiveTab('login');
        setError('Registration successful! Please login.');
      }
    } catch (error) {
      setError(error.response?.data?.detail || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-blue-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex justify-center mb-4">
            <Shield className="h-12 w-12 text-red-600" />
          </div>
          <CardTitle className="text-2xl">{t('appName')}</CardTitle>
          <CardDescription>{t('tagline')}</CardDescription>
        </CardHeader>
        
        <CardContent>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="login">{t('login')}</TabsTrigger>
              <TabsTrigger value="register">{t('register')}</TabsTrigger>
            </TabsList>
            
            <form onSubmit={handleSubmit} className="mt-6 space-y-4">
              {error && (
                <Alert variant={error.includes('successful') ? 'default' : 'destructive'}>
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}
              
              <TabsContent value="login" className="space-y-4">
                <div>
                  <Label htmlFor="studentId">{t('studentId')}</Label>
                  <Input
                    id="studentId"
                    value={formData.studentId}
                    onChange={(e) => setFormData({...formData, studentId: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="password">{t('password')}</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    required
                  />
                </div>
              </TabsContent>
              
              <TabsContent value="register" className="space-y-4">
                <div>
                  <Label htmlFor="name">{t('name')}</Label>
                  <Input
                    id="name"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="email">{t('email')}</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="studentId">{t('studentId')}</Label>
                  <Input
                    id="studentId"
                    value={formData.studentId}
                    onChange={(e) => setFormData({...formData, studentId: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="password">{t('password')}</Label>
                  <Input
                    id="password"
                    type="password"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="bloodGroup">{t('bloodGroup')}</Label>
                  <Input
                    id="bloodGroup"
                    value={formData.bloodGroup}
                    onChange={(e) => setFormData({...formData, bloodGroup: e.target.value})}
                    placeholder="e.g., A+, B-, O+"
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="location">{t('location')}</Label>
                  <Input
                    id="location"
                    value={formData.location}
                    onChange={(e) => setFormData({...formData, location: e.target.value})}
                    placeholder="Current location or address"
                  />
                </div>
              </TabsContent>
              
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? t('updating') : (activeTab === 'login' ? t('login') : t('register'))}
              </Button>
            </form>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
};

const EmergencyAlert = () => {
  const [alertMessage, setAlertMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [success, setSuccess] = useState(false);
  const { token, language } = useAuth();
  const { t } = useTranslation();

  const sendAlert = async () => {
    setSending(true);
    try {
      await axios.post(`${API}/alerts?lang=${language}`, 
        { message: alertMessage },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setSuccess(true);
      setAlertMessage('');
      setTimeout(() => setSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to send alert:', error);
    } finally {
      setSending(false);
    }
  };

  return (
    <Card className="border-red-200 bg-red-50">
      <CardHeader className="text-center">
        <AlertTriangle className="h-16 w-16 text-red-600 mx-auto mb-4" />
        <CardTitle className="text-2xl text-red-800">{t('emergencyAlert')}</CardTitle>
        <CardDescription>
          Press the button below to send an emergency alert to responders
        </CardDescription>
      </CardHeader>
      
      <CardContent className="text-center space-y-4">
        {success && (
          <Alert className="border-green-200 bg-green-50">
            <AlertDescription className="text-green-800">{t('alertSent')}</AlertDescription>
          </Alert>
        )}
        
        <textarea
          className="w-full p-3 border rounded-md"
          placeholder="Optional: Describe your emergency..."
          value={alertMessage}
          onChange={(e) => setAlertMessage(e.target.value)}
          rows={3}
        />
        
        <Button
          onClick={sendAlert}
          disabled={sending}
          size="lg"
          className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-4 text-lg"
        >
          {sending ? t('updating') : t('sendAlert')}
        </Button>
      </CardContent>
    </Card>
  );
};

const StudentProfile = () => {
  const { user, token, fetchUserProfile, language } = useAuth();
  const [contacts, setContacts] = useState(user?.emergency_contacts || []);
  const [newContact, setNewContact] = useState({ name: '', relationship: '', phone: '', email: '' });
  const [profileData, setProfileData] = useState({
    name: user?.name || '',
    blood_group: user?.blood_group || '',
    location: user?.location || ''
  });
  const [saving, setSaving] = useState(false);
  const { t } = useTranslation();

  const addContact = () => {
    if (newContact.name && newContact.phone) {
      setContacts([...contacts, newContact]);
      setNewContact({ name: '', relationship: '', phone: '', email: '' });
    }
  };

  const removeContact = (index) => {
    setContacts(contacts.filter((_, i) => i !== index));
  };

  const saveProfile = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/students/me?lang=${language}`, {
        ...profileData,
        emergency_contacts: contacts
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      await fetchUserProfile();
    } catch (error) {
      console.error('Failed to update profile:', error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <User className="h-5 w-5" />
            <span>{t('profile')}</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label htmlFor="name">{t('name')}</Label>
              <Input
                id="name"
                value={profileData.name}
                onChange={(e) => setProfileData({...profileData, name: e.target.value})}
              />
            </div>
            <div>
              <Label htmlFor="bloodGroup">{t('bloodGroup')}</Label>
              <Input
                id="bloodGroup"
                value={profileData.blood_group}
                onChange={(e) => setProfileData({...profileData, blood_group: e.target.value})}
              />
            </div>
            <div className="md:col-span-2">
              <Label htmlFor="location">{t('location')}</Label>
              <Input
                id="location"
                value={profileData.location}
                onChange={(e) => setProfileData({...profileData, location: e.target.value})}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Phone className="h-5 w-5" />
            <span>{t('emergencyContacts')}</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {contacts.map((contact, index) => (
            <div key={index} className="flex items-center justify-between p-3 border rounded-md">
              <div>
                <p className="font-semibold">{contact.name}</p>
                <p className="text-sm text-gray-600">{contact.relationship} - {contact.phone}</p>
              </div>
              <Button variant="outline" size="sm" onClick={() => removeContact(index)}>
                Remove
              </Button>
            </div>
          ))}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <Input
              placeholder={t('contactName')}
              value={newContact.name}
              onChange={(e) => setNewContact({...newContact, name: e.target.value})}
            />
            <Input
              placeholder={t('relationship')}
              value={newContact.relationship}
              onChange={(e) => setNewContact({...newContact, relationship: e.target.value})}
            />
            <Input
              placeholder={t('phone')}
              value={newContact.phone}
              onChange={(e) => setNewContact({...newContact, phone: e.target.value})}
            />
            <Input
              placeholder="Email (optional)"
              value={newContact.email}
              onChange={(e) => setNewContact({...newContact, email: e.target.value})}
            />
          </div>
          
          <Button onClick={addContact} variant="outline" className="w-full">
            {t('addContact')}
          </Button>
        </CardContent>
      </Card>

      <Button onClick={saveProfile} disabled={saving} className="w-full">
        {saving ? t('updating') : t('save')}
      </Button>
    </div>
  );
};

const AdminDashboard = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { token } = useAuth();
  const { t } = useTranslation();

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      const response = await axios.get(`${API}/alerts/active`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAlerts(response.data);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const resolveAlert = async (alertId) => {
    try {
      await axios.put(`${API}/alerts/${alertId}`, 
        { status: 'resolved' },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      fetchAlerts();
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading alerts...</div>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <AlertTriangle className="h-5 w-5 text-red-600" />
          <span>{t('activeAlerts')}</span>
          <Badge variant="secondary">{alerts.length}</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {alerts.length === 0 ? (
          <p className="text-center py-8 text-gray-500">{t('noAlerts')}</p>
        ) : (
          <div className="space-y-4">
            {alerts.map((alert) => (
              <div key={alert.id} className="border rounded-lg p-4 bg-red-50">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="font-semibold text-lg">{alert.student_name}</h3>
                    <p className="text-sm text-gray-600">ID: {alert.student_id}</p>
                  </div>
                  <div className="text-right text-sm text-gray-500">
                    <div className="flex items-center space-x-1">
                      <Clock className="h-4 w-4" />
                      <span>{new Date(alert.timestamp).toLocaleString()}</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                  <div className="flex items-center space-x-2">
                    <Mail className="h-4 w-4 text-gray-500" />
                    <span className="text-sm">{alert.student_email}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm font-medium">Blood Group: {alert.blood_group}</span>
                  </div>
                  {alert.location && (
                    <div className="flex items-center space-x-2 md:col-span-2">
                      <MapPin className="h-4 w-4 text-gray-500" />
                      <span className="text-sm">{alert.location}</span>
                    </div>
                  )}
                </div>

                {alert.message && (
                  <div className="mb-4">
                    <p className="text-sm"><strong>Message:</strong> {alert.message}</p>
                  </div>
                )}

                {alert.emergency_contacts.length > 0 && (
                  <div className="mb-4">
                    <h4 className="font-medium mb-2">{t('emergencyContacts')}:</h4>
                    <div className="space-y-1">
                      {alert.emergency_contacts.map((contact, index) => (
                        <div key={index} className="text-sm text-gray-700">
                          <strong>{contact.name}</strong> ({contact.relationship}) - {contact.phone}
                          {contact.email && ` - ${contact.email}`}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <Button 
                  onClick={() => resolveAlert(alert.id)}
                  className="w-full bg-green-600 hover:bg-green-700"
                >
                  Mark as Resolved
                </Button>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('alert');
  const { user } = useAuth();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="alert">{t('emergencyAlert')}</TabsTrigger>
            <TabsTrigger value="profile">{t('profile')}</TabsTrigger>
            {user?.is_admin && (
              <TabsTrigger value="admin">{t('admin')}</TabsTrigger>
            )}
          </TabsList>

          <div className="mt-8">
            <TabsContent value="alert">
              <EmergencyAlert />
            </TabsContent>
            
            <TabsContent value="profile">
              <StudentProfile />
            </TabsContent>
            
            {user?.is_admin && (
              <TabsContent value="admin">
                <AdminDashboard />
              </TabsContent>
            )}
          </div>
        </Tabs>
      </main>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginRegister />} />
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

const ProtectedRoute = ({ children }) => {
  const { token } = useAuth();
  return token ? children : <Navigate to="/login" />;
};

export default App;