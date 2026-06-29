import React, { createContext, useContext, useEffect, useState } from 'react';

export type Lang = 'en' | 'ar';

const STRINGS = {
  en: {
    dir: 'ltr',
    header: {
      nav: ['About', 'Programs', 'Community', 'Partners', 'News', 'Contact'],
      login: 'Log in',
      signup: 'Sign up',
      trainerPortal: 'Trainer portal',
      traineePortal: 'Trainee portal',
      searchPlaceholder: 'Search programs, news, alumni…',
      search: 'Search',
      closeSearch: 'Close search',
      openMenu: 'Open menu',
      closeMenu: 'Close menu',
      searchSite: 'Search the site',
      other: 'AR',
    },
    hero: {
      lead: 'Empowering Leaders.',
      rest: 'Transforming',
      highlight: 'Communities.',
      subtitle:
        "Egypt's premier institution for leadership development, capacity building, and executive education, preparing the next generation to shape national progress.",
      explore: 'Explore Programs',
      about: 'About NTA',
    },
    facts: {
      eyebrow: 'Facts & Figures',
      heading: 'A decade of measurable impact.',
      labels: ['Training Programs', 'Trainees Graduated', 'Training Hours', 'Partner Institutions'],
    },
    programs: {
      eyebrow: 'Executive Education',
      heading: 'Programs that shape national leaders.',
      intro:
        'Carefully designed curricula combining global best practice with local insight, preparing executives, policymakers, and emerging leaders to deliver lasting impact.',
      learnMore: 'Learn more',
      items: [
        { title: 'Presidential Leadership Program', desc: "An elite program shaping Egypt's most senior public-sector leaders through immersive strategic learning." },
        { title: 'Executive Education', desc: 'Advanced programs designed for executives ready to drive organizational transformation at scale.' },
        { title: 'Future Leaders', desc: "Cultivating ambitious young professionals with the vision and tools to lead Egypt's next chapter." },
        { title: 'Public Policy', desc: 'Evidence-based policy training that equips officials to design and implement effective national initiatives.' },
        { title: 'Digital Transformation', desc: 'Building digital fluency and innovation mindset across government and public services.' },
        { title: 'Strategic Management', desc: 'Equipping leaders with frameworks to navigate complexity, ambiguity, and long-term strategy.' },
      ],
    },
    moments: {
      eyebrow: 'NTA Moments',
      heading: 'Inside the Academy.',
      viewAll: 'View all videos',
      featured: { label: 'Featured', title: 'Presidential Leadership Program: 2026 Cohort Closing Ceremony' },
      secondary: [
        { label: 'Event', title: 'NTA Summit on Public Sector Innovation' },
        { label: 'Story', title: 'Future Leaders: Voices of the Next Generation' },
      ],
    },
    partners: {
      eyebrow: 'Our Partners',
      heading: "In collaboration with the world's leading institutions.",
      viewAll: 'View All Partners',
    },
    testimonials: {
      eyebrow: 'Testimonials',
      heading: 'Voices from our alumni.',
      prev: 'Previous testimonial',
      next: 'Next testimonial',
      tabLabel: (index: number) => `Testimonial ${index + 1}`,
      items: [
        { quote: 'NTA reshaped how I think about leadership at a national scale. The program combined rigor, empathy, and a deep sense of purpose I have not encountered elsewhere.', name: 'Dr. Layla Hassan', role: 'Senior Advisor, Ministry of Planning' },
        { quote: 'The Presidential Leadership Program brought together extraordinary peers and faculty. It is the most consequential professional experience of my career.', name: 'Ahmed El-Sayed', role: 'Director General, Digital Egypt' },
        { quote: "An institution that holds itself to a global standard while remaining grounded in Egypt's priorities. NTA is genuinely shaping the future of public service.", name: 'Nour Abdelrahman', role: 'Chief of Staff, Governorate Office' },
      ],
    },
    news: {
      eyebrow: 'In the News',
      heading: 'Stories, updates, and insights.',
      allNews: 'All news',
      readMore: 'Read more',
      items: [
        { category: 'Announcement', date: 'May 28, 2026', title: 'NTA Launches New Cohort of the Presidential Leadership Program', excerpt: 'A new generation of senior officials begins an immersive 18-month journey across strategy, policy, and innovation.' },
        { category: 'Partnership', date: 'May 14, 2026', title: 'Strategic Partnership Signed with Saïd Business School, Oxford', excerpt: 'Expanded collaboration brings world-class executive curricula and joint research initiatives to Cairo.' },
        { category: 'Insight', date: 'April 30, 2026', title: 'Reimagining Capacity Building for the Digital Era', excerpt: 'NTA faculty outline a new framework for upskilling public servants across data, AI, and digital service design.' },
      ],
    },
    footer: {
      desc: "Egypt's flagship institution for leadership development and executive education, equipping public servants to deliver meaningful national impact.",
      address: 'New Administrative Capital, Egypt',
      quickLinks: 'Quick Links',
      campusesTitle: 'Campuses',
      campuses: ['New Administrative Capital', 'Cairo Campus', 'Alexandria Hub', 'Virtual Campus', 'Library', 'Alumni Portal'],
      stayUpdated: 'Stay Updated',
      newsletterDesc: 'Subscribe for program announcements, research, and stories from across NTA.',
      emailPlaceholder: 'Your email address',
      subscribe: 'Subscribe',
      privacyHint: 'We respect your privacy. Unsubscribe at any time.',
      rights: 'National Training Academy. All rights reserved.',
      privacy: 'Privacy Policy',
      terms: 'Terms of Use',
      accessibility: 'Accessibility',
    },
    auth: {
      publicRegistration: 'Public registration',
      portalAccess: 'Portal access',
      signupTitle: 'Join the NTA trainee pipeline',
      loginTitle: 'Sign in to your portal',
      signupSubtitle: 'The flow matches the original four-step signup path.',
      loginSubtitle: 'Pick the right portal, then we will redirect you after validation.',
      closeDialog: 'Close dialog',
      signupStep: 'Step',
      signupOf: 'of',
      signupNationalId: 'National ID',
      signupFullName: 'Full name',
      signupPhone: 'Phone number',
      signupPassword: 'Password',
      signupHints: [
        'We will use this to check if the trainee profile already exists.',
        'Enter the name you want to appear in the registration records.',
        'Add a reachable mobile number for updates and verification.',
        'Finish by setting your password and optional email address.',
      ],
      nationalIdError: 'National ID must be 10 to 20 digits.',
      nationalIdValidationError: 'Could not validate National ID right now.',
      nationalIdTakenError: 'This National ID is already registered.',
      loginFailed: 'Login failed.',
      signupFailed: 'Signup failed.',
      fullNameError: 'Full name must be at least 3 characters.',
      phoneError: 'Please enter a valid phone number.',
      passwordError: 'Password must be at least 6 characters.',
      passwordMismatch: 'Passwords do not match.',
      checkIdButton: 'Check National ID',
      continueButton: 'Continue',
      backButton: 'Back',
      submitButton: 'Submit',
      trainee: 'Trainee',
      trainer: 'Trainer',
      emailOptional: 'Email address (optional)',
      loginNationalId: 'National ID',
      loginPassword: 'Password',
      loginButton: 'Login',
      signupButton: 'Create account',
      switchToSignup: 'Create a new account',
      switchToLogin: 'Already have an account?',
      rolePrompt: 'Select your portal',
      roleTrainee: 'Trainee portal',
      roleTrainer: 'Trainer portal',
      stepHint: 'Step',
    },
  },
  ar: {
    dir: 'rtl',
    header: {
      nav: ['نبذة', 'البرامج', 'المجتمع', 'الشركاء', 'الأخبار', 'تواصل'],
      login: 'تسجيل الدخول',
      signup: 'إنشاء حساب',
      trainerPortal: 'بوابة المدرب',
      traineePortal: 'بوابة المتدرب',
      searchPlaceholder: 'ابحث عن البرامج والأخبار والخريجين…',
      search: 'بحث',
      closeSearch: 'إغلاق البحث',
      openMenu: 'فتح القائمة',
      closeMenu: 'إغلاق القائمة',
      searchSite: 'ابحث في الموقع',
      other: 'EN',
    },
    hero: {
      lead: 'تمكين القادة.',
      rest: 'تحويل',
      highlight: 'المجتمعات.',
      subtitle:
        'المؤسسة الرائدة في مصر لتنمية القيادات وبناء القدرات والتعليم التنفيذي، لإعداد الجيل القادم لصناعة التقدّم الوطني.',
      explore: 'استكشف البرامج',
      about: 'عن الأكاديمية',
    },
    facts: {
      eyebrow: 'حقائق وأرقام',
      heading: 'عقدٌ من الأثر الملموس.',
      labels: ['برنامج تدريبي', 'متدرب تخرّج', 'ساعة تدريبية', 'مؤسسة شريكة'],
    },
    programs: {
      eyebrow: 'التعليم التنفيذي',
      heading: 'برامج تصنع قادة الوطن.',
      intro:
        'مناهج مصمّمة بعناية تجمع بين أفضل الممارسات العالمية والرؤية المحلية، لإعداد التنفيذيين وصُنّاع السياسات والقادة الناشئين لتحقيق أثرٍ دائم.',
      learnMore: 'اعرف المزيد',
      items: [
        { title: 'برنامج القيادة الرئاسية', desc: 'برنامج نخبوي يُعِدّ كبار قادة القطاع العام في مصر عبر تعلّم استراتيجي غامر.' },
        { title: 'التعليم التنفيذي', desc: 'برامج متقدمة مصممة للتنفيذيين المستعدين لقيادة التحول المؤسسي على نطاق واسع.' },
        { title: 'قادة المستقبل', desc: 'إعداد المهنيين الشباب الطموحين بالرؤية والأدوات لقيادة الفصل القادم من مسيرة مصر.' },
        { title: 'السياسات العامة', desc: 'تدريب على السياسات قائم على الأدلة يُمكّن المسؤولين من تصميم وتنفيذ مبادرات وطنية فعّالة.' },
        { title: 'التحول الرقمي', desc: 'بناء الطلاقة الرقمية وعقلية الابتكار عبر الحكومة والخدمات العامة.' },
        { title: 'الإدارة الاستراتيجية', desc: 'تزويد القادة بأطر عمل للتعامل مع التعقيد والغموض والاستراتيجية بعيدة المدى.' },
      ],
    },
    moments: {
      eyebrow: 'لقطات من الأكاديمية',
      heading: 'داخل الأكاديمية.',
      viewAll: 'عرض كل الفيديوهات',
      featured: { label: 'مميّز', title: 'برنامج القيادة الرئاسية: حفل ختام دفعة 2026' },
      secondary: [
        { label: 'فعالية', title: 'قمة الأكاديمية للابتكار في القطاع العام' },
        { label: 'قصة', title: 'قادة المستقبل: أصوات الجيل القادم' },
      ],
    },
    partners: {
      eyebrow: 'شركاؤنا',
      heading: 'بالتعاون مع أعرق المؤسسات حول العالم.',
      viewAll: 'عرض كل الشركاء',
    },
    testimonials: {
      eyebrow: 'شهادات',
      heading: 'أصوات من خريجينا.',
      prev: 'الشهادة السابقة',
      next: 'الشهادة التالية',
      tabLabel: (index: number) => `شهادة ${index + 1}`,
      items: [
        { quote: 'أعادت الأكاديمية تشكيل طريقة تفكيري في القيادة على المستوى الوطني. جمع البرنامج بين الصرامة والتعاطف وإحساس عميق بالهدف لم أجده في مكان آخر.', name: 'د. ليلى حسن', role: 'مستشار أول، وزارة التخطيط' },
        { quote: 'جمع برنامج القيادة الرئاسية نخبة استثنائية من الزملاء وأعضاء هيئة التدريس. إنها أهم تجربة مهنية في مسيرتي.', name: 'أحمد السيد', role: 'مدير عام، مصر الرقمية' },
        { quote: 'مؤسسة تلتزم بمعيار عالمي مع بقائها متجذّرة في أولويات مصر. الأكاديمية تصنع بحقّ مستقبل الخدمة العامة.', name: 'نور عبدالرحمن', role: 'رئيس ديوان، مكتب المحافظة' },
      ],
    },
    news: {
      eyebrow: 'في الأخبار',
      heading: 'قصص وتحديثات ورؤى.',
      allNews: 'كل الأخبار',
      readMore: 'اقرأ المزيد',
      items: [
        { category: 'إعلان', date: '٢٨ مايو ٢٠٢٦', title: 'الأكاديمية تُطلق دفعة جديدة من برنامج القيادة الرئاسية', excerpt: 'جيل جديد من كبار المسؤولين يبدأ رحلة غامرة مدتها ١٨ شهرًا عبر الاستراتيجية والسياسات والابتكار.' },
        { category: 'شراكة', date: '١٤ مايو ٢٠٢٦', title: 'توقيع شراكة استراتيجية مع كلية سعيد للأعمال بأكسفورد', excerpt: 'تعاون موسّع يجلب مناهج تنفيذية عالمية المستوى ومبادرات بحثية مشتركة إلى القاهرة.' },
        { category: 'رؤية', date: '٣٠ أبريل ٢٠٢٦', title: 'إعادة تصوّر بناء القدرات في العصر الرقمي', excerpt: 'يضع خبراء الأكاديمية إطارًا جديدًا لرفع مهارات موظفي الخدمة العامة في البيانات والذكاء الاصطناعي وتصميم الخدمات الرقمية.' },
      ],
    },
    footer: {
      desc: 'المؤسسة الرائدة في مصر لتنمية القيادات والتعليم التنفيذي، لتمكين موظفي الخدمة العامة من تحقيق أثرٍ وطني ملموس.',
      address: 'العاصمة الإدارية الجديدة، مصر',
      quickLinks: 'روابط سريعة',
      campusesTitle: 'الفروع',
      campuses: ['العاصمة الإدارية الجديدة', 'فرع القاهرة', 'مركز الإسكندرية', 'الفرع الافتراضي', 'المكتبة', 'بوابة الخريجين'],
      stayUpdated: 'ابقَ على اطلاع',
      newsletterDesc: 'اشترك لتصلك إعلانات البرامج والأبحاث والقصص من الأكاديمية.',
      emailPlaceholder: 'بريدك الإلكتروني',
      subscribe: 'اشترك',
      privacyHint: 'نحترم خصوصيتك. يمكنك إلغاء الاشتراك في أي وقت.',
      rights: 'الأكاديمية الوطنية للتدريب. جميع الحقوق محفوظة.',
      privacy: 'سياسة الخصوصية',
      terms: 'شروط الاستخدام',
      accessibility: 'إمكانية الوصول',
    },
    auth: {
      publicRegistration: 'التسجيل العام',
      portalAccess: 'الدخول إلى البوابة',
      signupTitle: 'انضم إلى مسار المتدربين في الأكاديمية',
      loginTitle: 'سجّل الدخول إلى بوابتك',
      signupSubtitle: 'هذه الخطوات تطابق مسار التسجيل الأصلي من أربع مراحل.',
      loginSubtitle: 'اختر البوابة المناسبة ثم سنحوّلك بعد التحقق.',
      closeDialog: 'إغلاق النافذة',
      signupStep: 'الخطوة',
      signupOf: 'من',
      signupNationalId: 'الرقم القومي',
      signupFullName: 'الاسم الكامل',
      signupPhone: 'رقم الهاتف',
      signupPassword: 'كلمة المرور',
      signupHints: [
        'سنستخدمه للتحقق من عدم وجود ملف متدرب سابق.',
        'اكتب الاسم كما تريد ظهوره في سجلات التسجيل.',
        'أضف رقم هاتف يمكن الوصول إليه للتحديثات والتحقق.',
        'أنهِ التسجيل بتعيين كلمة المرور والبريد الإلكتروني اختياريًا.',
      ],
      nationalIdError: 'يجب أن يكون الرقم القومي من 10 إلى 20 رقمًا.',
      nationalIdValidationError: 'تعذر التحقق من الرقم القومي الآن.',
      nationalIdTakenError: 'هذا الرقم القومي مسجّل بالفعل.',
      loginFailed: 'فشل تسجيل الدخول.',
      signupFailed: 'فشل التسجيل.',
      fullNameError: 'يجب أن يكون الاسم الكامل 3 أحرف على الأقل.',
      phoneError: 'يرجى إدخال رقم هاتف صحيح.',
      passwordError: 'يجب أن تكون كلمة المرور 6 أحرف على الأقل.',
      passwordMismatch: 'كلمتا المرور غير متطابقتين.',
      checkIdButton: 'التحقق من الرقم القومي',
      continueButton: 'التالي',
      backButton: 'رجوع',
      submitButton: 'إرسال',
      trainee: 'متدرب',
      trainer: 'مدرب',
      emailOptional: 'البريد الإلكتروني (اختياري)',
      loginNationalId: 'الرقم القومي',
      loginPassword: 'كلمة المرور',
      loginButton: 'دخول',
      signupButton: 'إنشاء حساب',
      switchToSignup: 'إنشاء حساب جديد',
      switchToLogin: 'لديك حساب بالفعل؟',
      rolePrompt: 'اختر البوابة',
      roleTrainee: 'بوابة المتدرب',
      roleTrainer: 'بوابة المدرب',
      stepHint: 'الخطوة',
    },
  },
} as const;

type Dict = (typeof STRINGS)['en'];

const LangContext = createContext<{ lang: Lang; dir: 'ltr' | 'rtl'; t: Dict; toggle: () => void }>({
  lang: 'en',
  dir: 'ltr',
  t: STRINGS.en,
  toggle: () => {},
});

export function LangProvider({ children }: { children: React.ReactNode }) {
  const [lang, setLang] = useState<Lang>(() => {
    try {
      const s = localStorage.getItem('nta_lang');
      if (s === 'ar' || s === 'en') return s;
    } catch (e) {}
    return 'en';
  });
  const dir = lang === 'ar' ? 'rtl' : 'ltr';
  useEffect(() => {
    try { localStorage.setItem('nta_lang', lang); } catch (e) {}
    const html = document.documentElement;
    html.lang = lang;
    html.dir = dir;
  }, [lang, dir]);
  const toggle = () => setLang((l) => (l === 'en' ? 'ar' : 'en'));
  return (
    <LangContext.Provider value={{ lang, dir, t: STRINGS[lang] as Dict, toggle }}>
      {children}
    </LangContext.Provider>
  );
}

export function useLang() {
  return useContext(LangContext);
}
