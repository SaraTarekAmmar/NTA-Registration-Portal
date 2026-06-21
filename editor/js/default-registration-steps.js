var DEFAULT_REGISTRATION_STEPS = [
    {
        "step_type": "personal_info",
        "step_key": "step_1",
        "title_ar": "البيانات الشخصية الأساسية",
        "description_ar": "",
        "is_required": true,
        "config_json": {
            "is_active": true,
            "fields": [
                {
                    "field_id": "countryOfStay",
                    "label": "دولة الإقامة مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "governmentOrState",
                    "label": "المحافظة أو الولاية مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "city",
                    "label": "المدينة مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "address",
                    "label": "العنوان مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "maritalStatus",
                    "label": "الحالة الاجتماعية مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "militaryStatus",
                    "label": "الموقف من التجنيد مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "militaryReason",
                    "label": "سبب الموقف من التجنيد مطلوب عند الاختيار",
                    "is_active": true,
                    "is_required": true
                }
            ]
        }
    },
    {
        "step_type": "contact_info",
        "step_key": "step_2",
        "title_ar": "القسم الثاني - بيانات الاتصال",
        "description_ar": "",
        "is_required": true,
        "config_json": {
            "is_active": true,
            "fields": [
                {
                    "field_id": "identityDocNationalId",
                    "label": "البطاقة الشخصية National ID",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "identityDocPassport",
                    "label": "جواز السفر Passport",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "nationalId",
                    "label": "رقم البطاقة الشخصية (الرقم القومي) مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "passportNumber",
                    "label": "رقم جواز السفر (اختياري)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "identityDocumentScan",
                    "label": "صورة وثيقة الهوية مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "numberOfNationalities",
                    "label": "عدد الجنسيات مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "nationality",
                    "label": "الجنسية مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "secondNationality",
                    "label": "الجنسية الثانية (اختياري)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "thirdNationality",
                    "label": "الجنسية الثالثة (اختياري)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "mobileNumber1",
                    "label": "رقم الموبايل الأول مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "mobileNumber2",
                    "label": "رقم الموبايل الثاني (اختياري)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "whatsappNumber",
                    "label": "رقم الواتساب مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "whatsappSameAsMobile",
                    "label": "هو نفس الموبايل الأول",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "monthlyAverageIncome",
                    "label": "متوسط الدخل الشهري مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "primaryEmail",
                    "label": "البريد الإلكتروني مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "secondaryEmail",
                    "label": "البريد الإلكتروني الثانوي (اختياري)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "emergencyContactsCount",
                    "label": "عدد جهات اتصال الطوارئ مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "emergencyName1",
                    "label": "جهة اتصال الطوارئ 1 - الاسم مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "emergencyPhone1",
                    "label": "جهة اتصال الطوارئ 1 - الرقم مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "emergencyAddress1",
                    "label": "جهة اتصال الطوارئ 1 - العنوان مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "emergencyId1",
                    "label": "جهة اتصال الطوارئ 1 - رقم الهوية (اختياري)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "emergencyName2",
                    "label": "جهة اتصال الطوارئ 2 - الاسم",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "emergencyPhone2",
                    "label": "جهة اتصال الطوارئ 2 - الرقم",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "emergencyAddress2",
                    "label": "جهة اتصال الطوارئ 2 - العنوان",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "emergencyId2",
                    "label": "جهة اتصال الطوارئ 2 - رقم الهوية",
                    "is_active": true,
                    "is_required": true
                }
            ]
        }
    },
    {
        "step_type": "education_bg",
        "step_key": "step_3",
        "title_ar": "المؤهلات العلمية",
        "description_ar": "",
        "is_required": true,
        "config_json": {
            "is_active": true,
            "fields": [
                {
                    "field_id": "eduHighestDegree",
                    "label": "أعلى مؤهل تعليمي تم الحصول عليهمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduDegreeCountry",
                    "label": "الدولة / Countryمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduInstitution",
                    "label": "الجامعة / المعهد / University / Instituteمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduInstituteName",
                    "label": "اسم المعهد / Institute Nameمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduSchoolName",
                    "label": "اسم المدرسة / School Nameمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduCollegeFacultySelect",
                    "label": "الكلية / الكيان (قائمة)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduCollegeFacultyText",
                    "label": "الكلية / قسم الدراسة بالمعهد / الإدارة التعليميةمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduSpeciality",
                    "label": "التخصصمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduGpa",
                    "label": "المعدل التراكمي (GPA)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduTotalScore",
                    "label": "المجموعمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduPercentage",
                    "label": "النسبة المئويةمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduGraduationDate",
                    "label": "تاريخ التخرجمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "graduationCertificateScan",
                    "label": "صورة شهادة التخرج",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduHasPostgraduate",
                    "label": "درجة علمية أعلى (دراسات عليا)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduPostgraduateDegreeType",
                    "label": "الدرجة (ماجستير - دكتوراه)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduDegreeIssuerEntity",
                    "label": "اسم الجهة المانحة للدرجةمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduMainSpecialityPg",
                    "label": "التخصص الرئيسي للدرجةمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduSecondarySpecialityPg",
                    "label": "التخصص الفرعي",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduPgStartDate",
                    "label": "تاريخ البدءمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduPgEndDate",
                    "label": "تاريخ الانتهاءمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduFunding",
                    "label": "تمويل شخصي أم جهة خارجية",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduRecommendingEntity",
                    "label": "اسم الجهة التي رشحتك",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "eduScholarshipEntity",
                    "label": "اسم جهة المنحة",
                    "is_active": true,
                    "is_required": true
                }
            ]
        }
    },
    {
        "step_type": "standardized_tests",
        "step_key": "step_4",
        "title_ar": "الاختبارات والشهادات المعيارية",
        "description_ar": "",
        "is_required": true,
        "config_json": {
            "is_active": true,
            "fields": [
                {
                    "field_id": "standardizedTestName",
                    "label": "اسم الاختبار (Test Name)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "standardizedTestScore",
                    "label": "درجة الاختبار (Test Score)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "standardizedTestAuthority",
                    "label": "جهة الإصدار (Issuing Authority)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "standardizedTestDate",
                    "label": "تاريخ الحصول (Date Obtained)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "standardizedTestDocument",
                    "label": "Attach Document",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "standardizedTestUrl",
                    "label": "رابط التحقق من الشهادة (اجبارى عند ملء هذا القسم)مطلوب",
                    "is_active": true,
                    "is_required": true
                }
            ]
        }
    },
    {
        "step_type": "work_experience",
        "step_key": "step_5",
        "title_ar": "الخبرة العملية",
        "description_ar": "",
        "is_required": true,
        "config_json": {
            "is_active": true,
            "fields": [
                {
                    "field_id": "empExperienceStatus",
                    "label": "هل لديك خبرة عملية؟مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "employmentSectionCv",
                    "label": "تحميل السيرة الذاتية مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empJobType",
                    "label": "نوع الوظيفةمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empWorkNature",
                    "label": "طبيعة الوظيفةمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empMinistry",
                    "label": "الوزارةمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empMinistrySub",
                    "label": "الجهة التابعة للوزارة",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empJoiningDate",
                    "label": "تاريخ الالتحاق بالعملمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empCurrentlyWorking",
                    "label": "ما زلت أعمل في هذه الوظيفة",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empEndDate",
                    "label": "تاريخ الانتهاء من العملمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empJobTitle",
                    "label": "المسمى الوظيفيمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empSeniority",
                    "label": "المستوى الوظيفي / الأقدمية",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empDepartment",
                    "label": "القسم / الإدارة",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empSpeciality",
                    "label": "التخصص المهني",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empJobDescription",
                    "label": "وصف الوظيفة والمسؤوليات",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empCompanyAddress",
                    "label": "عنوان جهة العمل",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empIndustryPrimary",
                    "label": "مجال العمل / طبيعة النشاط (أول)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empIndustrySecondary",
                    "label": "مجال العمل (ثانٍ — اختياري، حتى مجالين)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empRefName",
                    "label": "اسم المرجع",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empRefPhone",
                    "label": "رقم هاتف المرجع",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empRefEmail",
                    "label": "البريد الإلكتروني للمرجع",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "empRefPlaceIndex",
                    "label": "مكان العمل المشترك",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "organizationIndustry",
                    "label": "المنظمة / جهة العمل والقطاع (Organization &amp;                           Industry)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "startDate",
                    "label": "تاريخ البدء (Start Date)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "endDate",
                    "label": "تاريخ الانتهاء (End Date)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "keyResponsibilities",
                    "label": "المسؤوليات الرئيسية (Key Responsibilities)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "reasonForLeaving",
                    "label": "سبب ترك العمل (Reason for Leaving)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "currentJobTitle",
                    "label": "المسمى الوظيفي الحالي (Current Job Title)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "yearsManagementExperience",
                    "label": "سنوات الخبرة الإدارية (Years of Management                       Experience)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "organizationSize",
                    "label": "حجم المنظمة (Organization Size)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "annualBudgetManaged",
                    "label": "الميزانية السنوية المدارة (Annual Budget Managed)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "directReports",
                    "label": "عدد المرؤوسين المباشرين (Direct Reports / Team                       Size)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "globalExperience",
                    "label": "الخبرة العالمية (Global Experience - سنوات في                       الخارج)",
                    "is_active": true,
                    "is_required": true
                }
            ]
        }
    },
    {
        "step_type": "skills_languages",
        "step_key": "step_6",
        "title_ar": "المهارات واللغات والاهتمامات",
        "description_ar": "",
        "is_required": true,
        "config_json": {
            "is_active": true,
            "fields": [
                {
                    "field_id": "technicalSkillCategory",
                    "label": "المهارات التقنية (Technical Skills)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "computerSkillCategory",
                    "label": "مهارات الحاسب الآلي (Computer Skills)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "softSkillCategory",
                    "label": "المهارات الشخصية (Soft Skills)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "otherSkillsFreeText",
                    "label": "مهارات أخرى (Other Skills)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "nativeLanguage",
                    "label": "اللغة الأم (Mother Language) (اجبارى)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "englishProficiency",
                    "label": "اللغة الثانية (الإنجليزية) — مستوى الإجادة فقط (اجبارى)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "interestsDescription",
                    "label": "وصف الاهتماماتمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "usesSocialMedia",
                    "label": "هل تستخدم وسائل التواصل الاجتماعي؟مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "socialPlatformFacebook",
                    "label": "منصات التواصل (تشغيل / إيقاف لكل منصة)مطلوب",
                    "is_active": true,
                    "is_required": true
                }
            ]
        }
    },
    {
        "step_type": "awards_conferences",
        "step_key": "step_7",
        "title_ar": "الجوائز والمؤتمرات",
        "description_ar": "",
        "is_required": true,
        "config_json": {
            "is_active": true,
            "fields": [
                {
                    "field_id": "hasPrizesAwards",
                    "label": "هل حصلت على أي جوائز أو تكريمات؟مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "prizeName",
                    "label": "اسم الجائزة / التكريم",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "prizeDateAchieved",
                    "label": "تاريخ الحصول عليها",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "prizeCategory",
                    "label": "فئة الجائزة",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "prizeIssuingBody",
                    "label": "الجهة المانحة",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "prizeCertificate",
                    "label": "تحميل صورة الشهادة (PDF أو صورة)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "hasConferencesWorkshops",
                    "label": "هل شاركت في أي مؤتمرات أو ورش عمل؟مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "cwActivityType",
                    "label": "النوعمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "cwEventName",
                    "label": "اسم الفعالية",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "cwOrganizingEntity",
                    "label": "الجهة المنظمة",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "cwStartDate",
                    "label": "تاريخ البدءمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "cwEndDate",
                    "label": "تاريخ الانتهاءمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "cwParticipationLevel",
                    "label": "مستوى المشاركة",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "awardTitle",
                    "label": "عنوان الجائزة / التكريم (Award / Recognition                           Title)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "issuingBody",
                    "label": "الجهة المانحة (Issuing Body)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "keyAchievement",
                    "label": "الإنجاز الرئيسي (حتى 100 كلمة) (Key Achievement)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "communityLeadership",
                    "label": "القيادة المجتمعية / التطوع (Community / Volunteer                     Leadership)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "extracurricularRole",
                    "label": "الدور (Role)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "extracurricularDuration",
                    "label": "مدة المشروع (Project Duration)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "portfolioUrl",
                    "label": "منشورات / ملف أعمال (Publication / Portfolio)",
                    "is_active": true,
                    "is_required": true
                }
            ]
        }
    },
    {
        "step_type": "public_work_legal",
        "step_key": "step_8",
        "title_ar": "العمل العام والمشاركة السياسية والموقف القانوني",
        "description_ar": "",
        "is_required": true,
        "config_json": {
            "is_active": true,
            "fields": [
                {
                    "field_id": "hasPublicVoluntaryWork",
                    "label": "هل شاركت في أي عمل عام أو تطوعي؟مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "pvFoundationName",
                    "label": "اسم المؤسسة أو الجمعية الخيريةمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "pvPosition",
                    "label": "المنصب / الدور الوظيفيمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "pvJoinDate",
                    "label": "سنة / تاريخ الالتحاقمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "pvLeaveDate",
                    "label": "سنة / تاريخ المغادرة",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "pvScope",
                    "label": "نطاق العمل ووصف الخبرة",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "pvWorkField",
                    "label": "مجال العمل",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "pvCountry",
                    "label": "دولة العمل",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "pvState",
                    "label": "المحافظة أو الولايةمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "hasPoliticalParticipation",
                    "label": "هل شاركت في أي عمل سياسي؟مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "politicalPartyName",
                    "label": "اسم الحزب أو التنظيم السياسيمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "politicalRole",
                    "label": "الدور السياسيمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "politicalWorkDetails",
                    "label": "تفاصيل العمل السياسيمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "hasPoliticalCandidacy",
                    "label": "هل ترشحت لأي منصب سياسي؟",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "candidacyPositionName",
                    "label": "اسم المنصب السياسيمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "candidacyResult",
                    "label": "النتيجةمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "candidacyExperienceDescription",
                    "label": "وصف تجربة الترشحمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "hasPriorCriminalConvictions",
                    "label": "هل صدرت ضدك أي أحكام جنائية أو جنح سابقة؟مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "priorConvictionDescription",
                    "label": "وصف الحكم الجنائيمطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "sectionSevenCriminalRecordCertificate",
                    "label": "صحيفة الحالة الجنائية (الفيش والتشبيه) مطلوب",
                    "is_active": true,
                    "is_required": true
                }
            ]
        }
    },
    {
        "step_type": "motivations",
        "step_key": "step_9",
        "title_ar": "الدوافع والمخرجات واللوجستيات",
        "description_ar": "",
        "is_required": true,
        "config_json": {
            "is_active": true,
            "fields": [
                {
                    "field_id": "cvResume",
                    "label": "السيرة الذاتية الشاملة (CV / Resume) مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "lettersOfRecommendation",
                    "label": "خطابات التوصية (2) (اختياري)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "criminalRecord",
                    "label": "فيش جنائي / شهادة خلو سوابق مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "employerNoc",
                    "label": "خطاب اعتماد من جهة العمل (Employer Acknowledgment / NOC)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "referenceName",
                    "label": "الاسم (Name)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "referenceRelationship",
                    "label": "العلاقة / المسمى الوظيفي (Relationship / Title)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "referenceContact",
                    "label": "معلومات الاتصال (Contact Information)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "primaryLearningObjective",
                    "label": "الهدف التعليمي الرئيسي (Primary Learning Objective)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "uniqueContribution",
                    "label": "مساهمتك الفريدة للدفعة (Unique Contribution to Cohort)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "futureCareerGoal",
                    "label": "هدفـك المهني خلال 5 سنوات (Future Career Goal - 5 Years)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "fundingSource",
                    "label": "مصدر التمويل (Funding Source)مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "scholarshipEssay",
                    "label": "مقال المنحة (Scholarship Essay) - الحد الأقصى 5000 حرف",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "dietaryRestrictions",
                    "label": "قيود النظام الغذائي (Dietary Restrictions)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "accessibilityRequirements",
                    "label": "متطلبات إمكانية الوصول (Accessibility Requirements)",
                    "is_active": true,
                    "is_required": true
                }
            ]
        }
    },
    {
        "step_type": "final_verification",
        "step_key": "step_10",
        "title_ar": "القسم العاشر - التحقق والتأكيد النهائي",
        "description_ar": "",
        "is_required": true,
        "config_json": {
            "is_active": true,
            "fields": [
                {
                    "field_id": "photoFront",
                    "label": "التقاط / رفع",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "socialProfileFacebookUrl",
                    "label": "رابط حساب فيسبوك مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "socialProfileInstagramUrl",
                    "label": "رابط حساب إنستجرام مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "socialProfileXUrl",
                    "label": "رابط حساب إكس / تويتر مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "socialProfileLinkedInUrl",
                    "label": "رابط حساب لينكد إن مطلوب",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "socialProfileTikTokUrl",
                    "label": "رابط حساب تيك توك (اختياري)",
                    "is_active": true,
                    "is_required": true
                },
                {
                    "field_id": "dataAccuracyTermsConfirmed",
                    "label": "أقر بصحة جميع البيانات المدخلة وأوافق على كافة الشروط                       والأحكام الخاصة بالبرنامج",
                    "is_active": true,
                    "is_required": true
                }
            ]
        }
    }
];