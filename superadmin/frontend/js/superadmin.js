const { useState, useEffect, useRef } = React;

const Icon = ({ name, size = 20, className = "" }) => {
    const iconRef = useRef(null);
    useEffect(() => {
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }, [name]);
    return (
        <i data-lucide={name} className={className} style={{ width: size, height: size, display: 'inline-flex', alignItems: 'center', justifyContent: 'center' }}></i>
    );
};

const App = () => {
    const [isLoggedIn, setIsLoggedIn] = useState(!!localStorage.getItem('superadmin_token'));
    const [loginData, setLoginData] = useState({ user: '', pass: '' });
    const [loginError, setLoginError] = useState('');
    const [activeTab, setActiveTab] = useState('overview');
    const [theme, setTheme] = useState(() => {
        const stored = localStorage.getItem('nta-theme');
        if (stored === 'light' || stored === 'dark') return stored;
        const legacy = localStorage.getItem('sa_theme');
        return legacy === 'light' || legacy === 'dark' ? legacy : 'dark';
    });
    const [lang, setLang] = useState(localStorage.getItem('sa_lang') || 'en');

    useEffect(() => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('nta-theme', theme);
        document.documentElement.classList.toggle('light-mode', theme === 'light');
        if (document.body) {
            document.body.classList.toggle('light-mode', theme === 'light');
        }
    }, [theme]);

    useEffect(() => {
        document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
        document.documentElement.lang = lang;
        localStorage.setItem('sa_lang', lang);
    }, [lang]);

    const translations = {
        en: {
            title: "AI Control",
            subtitle: "NTA Producer",
            logout: "Logout",
            overview: "Systems Overview",
            face: "Face Recognition",
            sorting: "Electronic Sorting",
            quiz: "Quiz Engine",
            connected: "Connected",
            readyTitle: "Ready to Dispatch"
        },
        ar: {
            title: "التحكم بالذكاء الاصطناعي",
            subtitle: "بنية NTA التحتية",
            logout: "تسجيل الخروج",
            overview: "نظرة عامة على الأنظمة",
            face: "التعرف على الوجه",
            sorting: "الفرز الإلكتروني",
            quiz: "محرك الاختبارات",
            connected: "متصل",
            readyTitle: "جاهز للتنفيذ"
        }
    };

    const t = (key) => translations[lang][key] || key;

    const [stats, setStats] = useState({
        pending_enrollment: 0,
        total_trainees: 0,
        unprocessed_ocr: 0,
        ocr_pct: 0,
        avg_latency: 0
    });

    const [isProcessing, setIsProcessing] = useState(null);

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoginError('');
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: loginData.user, password: loginData.pass })
            });
            const data = await response.json();
            if (response.ok) {
                localStorage.setItem('superadmin_token', data.access_token);
                setIsLoggedIn(true);
            } else {
                setLoginError(data.detail || 'Access Denied');
            }
        } catch (err) {
            setLoginError('Backend connection failed.');
        }
    };

    const simulateDispatch = async (service, endpoint, payload) => {
        setIsProcessing(service);
        try {
            const token = localStorage.getItem('superadmin_token');
            const response = await fetch('/api/ai/dispatch', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ service, endpoint, data: payload })
            });
            if (response.ok) {
                alert(`${service} processed successfully.`);
            }
        } catch (err) {
            alert('Service call failed.');
        } finally {
            setIsProcessing(null);
        }
    };

    if (!isLoggedIn) {
        return (
            <div className="min-h-screen bg-[var(--bg-dark)] flex items-center justify-center p-6">
                <div className="w-full max-w-md glass-panel p-10 rounded-[2.5rem]">
                    <h1 className="text-3xl font-black text-white text-center mb-8">AI Portal</h1>
                    <form onSubmit={handleLogin} className="space-y-6">
                        <input type="text" placeholder="Username" className="w-full p-4 rounded-xl bg-white/5 border border-white/10 text-white" value={loginData.user} onChange={e => setLoginData({...loginData, user: e.target.value})} />
                        <input type="password" placeholder="Password" className="w-full p-4 rounded-xl bg-white/5 border border-white/10 text-white" value={loginData.pass} onChange={e => setLoginData({...loginData, pass: e.target.value})} />
                        <button type="submit" className="w-full py-4 btn-premium text-white font-bold rounded-xl">Login</button>
                    </form>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-[var(--bg-dark)] text-[var(--text-main)] flex h-screen overflow-hidden">
            <aside className="w-72 bg-[var(--sidebar-bg)] border-r border-[var(--card-border)] backdrop-blur-xl flex flex-col p-6">
                <h1 className="font-bold text-xl mb-8">{t('title')}</h1>
                <nav className="space-y-2">
                    {[
                        { id: 'overview', label: t('overview'), icon: 'layout' },
                        { id: 'face', label: t('face'), icon: 'camera' },
                        { id: 'ocr', label: t('sorting'), icon: 'scan' },
                        { id: 'quiz', label: t('quiz'), icon: 'file-text' }
                    ].map(item => (
                        <button key={item.id} onClick={() => setActiveTab(item.id)} className={`w-full flex items-center gap-3 p-3 rounded-xl ${activeTab === item.id ? 'bg-indigo-600/20 text-indigo-400' : 'text-slate-400'}`}>
                            <Icon name={item.icon} size={18} />
                            {item.label}
                        </button>
                    ))}
                </nav>
                <button onClick={() => { localStorage.removeItem('superadmin_token'); setIsLoggedIn(false); }} className="mt-auto py-2 text-rose-500 font-bold uppercase text-xs flex items-center justify-center gap-2">
                    <Icon name="log-out" size={14} /> {t('logout')}
                </button>
            </aside>

            <main className="flex-1 flex flex-col overflow-hidden">
                <header className="h-16 border-b border-[var(--card-border)] bg-[var(--header-bg)] flex items-center justify-between px-8">
                    <span className="font-bold">{activeTab.toUpperCase()}</span>
                    <div className="flex items-center gap-4">
                        <span className="text-xs text-emerald-400 bg-emerald-500/10 px-3 py-1 rounded-full border border-emerald-500/20">{t('connected')}</span>
                    </div>
                </header>

                <div className="flex-1 p-8 overflow-y-auto">
                    {activeTab === 'overview' && (
                        <div className="p-10 glass-card rounded-[2.5rem]">
                            <h2 className="text-3xl font-bold mb-4">{t('readyTitle')}</h2>
                        </div>
                    )}
                </div>
            </main>

            <div className="floating-controls">
                <button onClick={() => setLang(lang === 'en' ? 'ar' : 'en')} className="control-btn"><Icon name="languages" size={20} /></button>
                <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')} className="control-btn"><Icon name={theme === 'dark' ? 'sun' : 'moon'} size={20} /></button>
            </div>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);
