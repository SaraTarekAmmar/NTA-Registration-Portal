from pydantic import BaseModel, EmailStr, validator, Field
from typing import List, Any, Optional
import re
from datetime import datetime

class TraineeRegistration(BaseModel):
    # Core Identity
    fullName: str
    fullNameEn: str
    dob: str
    nationalId: str
    gender: str
    maritalStatus: str
    email: EmailStr
    secondaryEmail: Optional[EmailStr] = None
    phoneNumbers: List[str] = Field(..., max_items=5)
    
    # Emergency & Address
    emergencyName: str
    emergencyPhone: str
    currentAddress: str
    permanentAddress: str
    countryOfStay: str
    governmentOrState: str
    city: str
    
    # Demographics & Background
    nationality: str
    nativeLanguage: Optional[str] = None
    englishProficiency: Optional[str] = None
    militaryStatus: str
    militaryReason: Optional[str] = None
    monthlyAverageIncome: str
    numberOfNationalities: int
    identityDocType: Optional[Any] = None  # Accepts str or List[str] from frontend
    
    # Education & Experience (List items to be inserted into child tables)
    academicHistory: List[Any] = Field([], max_items=10)
    professionalHistory: List[Any] = Field([], max_items=15)
    technicalSkills: List[Any] = Field([], max_items=30)
    softSkills: List[Any] = Field([], max_items=30)
    computerSkills: List[Any] = Field([], max_items=30)
    
    # Professional Summary
    yearsExperience: Optional[int] = None
    objective: Optional[str] = None
    
    # Interests & Social
    portfolioUrl: Optional[str] = None
    learningObjectives: str
    dietaryRestrictions: Optional[str] = None
    accessibilityRequirements: Optional[str] = None
    interests: Optional[List[str]] = None
    interestsDescription: Optional[str] = None
    usesSocialMedia: Optional[str] = None
    dataAccuracyTermsConfirmed: bool = False

    # Missing incoming fields
    educationalBackground: Optional[Any] = None
    socialMediaPlatforms: Optional[Any] = None
    socialMediaProfileUrls: Optional[Any] = None
    
    # Missing File Fields
    identityDocumentScan: Optional[str] = None
    identityDocumentScanFiles: Optional[List[str]] = None
    employmentSectionCv: Optional[str] = None
    lettersOfRecommendation: Optional[List[str]] = None
    sectionSevenCriminalRecordCertificate: Optional[str] = None
    identityPhotos: Optional[Any] = None
    organizationalChartFiles: Optional[List[str]] = None
    idScanFiles: Optional[List[str]] = None
    employerNocFiles: Optional[List[str]] = None

    # Extra lists & indicators
    employmentHistory: Optional[List[Any]] = Field([], max_items=20)
    employmentReferences: Optional[List[Any]] = Field([], max_items=20)
    hasPrizesAwards: Optional[str] = None
    hasConferencesWorkshops: Optional[str] = None
    hasPublicVoluntaryWork: Optional[str] = None
    additionalLanguages: Optional[List[Any]] = Field([], max_items=5)
    otherSkillsFreeText: Optional[str] = None
    references: Optional[List[Any]] = Field([], max_items=10)
    
    # Misc Activities
    standardizedTestsEntries: List[Any] = Field([], max_items=20)
    prizesAwardsEntries: List[Any] = Field([], max_items=20)
    conferencesWorkshopsEntries: List[Any] = Field([], max_items=20)
    publicVoluntaryWorkEntries: List[Any] = Field([], max_items=20)
    
    # Political & Legal
    hasPoliticalParticipation: Optional[str] = None
    politicalPartyName: Optional[str] = None
    politicalRole: Optional[str] = None
    politicalWorkDetails: Optional[str] = None
    hasPoliticalCandidacy: Optional[str] = None
    candidacyPositionName: Optional[str] = None
    candidacyResult: Optional[str] = None
    candidacyExperienceDescription: Optional[str] = None
    hasPriorCriminalConvictions: Optional[str] = None
    priorConvictionDescription: Optional[str] = None
    
    # Quiz Data
    quizResults: Any
    
    # Document Paths (Incoming as strings after upload)
    photoFront: Optional[str] = None
    idScan: Optional[str] = None
    cvResume: Optional[str] = None
    organizationalChart: Optional[str] = None
    criminalRecord: Optional[str] = None
    employerNoc: Optional[str] = None
    scholarshipEssayFile: Optional[str] = None
    graduationCertificate: Optional[str] = None
    
    # Role
    role: str = "trainee"

    class Config:
        extra = "allow"

    @validator('fullName', 'fullNameEn', pre=True)
    def validate_names(cls, v):
        if not v: return v
        # Allow Arabic/English letters, spaces, hyphens, apostrophes, dots (common in compound names)
        if not re.match(r"^[\u0600-\u06FFa-zA-Z\s\-'.]+$", v):
            raise ValueError("الاسم يجب أن يحتوي على حروف عربية أو إنجليزية ومسافات فقط")
        return v

    @validator('nationalId')
    def validate_nid(cls, v):
        if not v or not v.strip():
            return v  # Allow empty for passport-only registrations
        if not re.match(r'^[A-Za-z0-9\-]{5,20}$', v.strip()):
            raise ValueError("رقم الهوية غير صالح")
        return v.strip()

    @validator('gender')
    def validate_gender_with_nid(cls, v, values):
        nid = values.get('nationalId')
        if nid and len(nid) == 14 and nid.isdigit():
            expected = 'female' if int(nid[12]) % 2 == 0 else 'male'
            if v != expected:
                raise ValueError("النوع لا يتطابق مع الرقم القومي المدخل")
        return v

    @validator('maritalStatus')
    def validate_marital_status(cls, v, values):
        dob = values.get('dob')
        if dob and v == 'married':
            try:
                dob_date = datetime.strptime(dob, "%Y-%m-%d")
                from datetime import date
                age = (date.today() - dob_date.date()).days // 365
                if age < 18:
                    raise ValueError("لا يمكن اختيار حالة متزوج لسن أقل من 18 عاماً")
            except Exception as e:
                if isinstance(e, ValueError) and "لا يمكن" in str(e):
                    raise e
        return v

    @validator('secondaryEmail')
    def validate_secondary_email(cls, v, values):
        email = values.get('email')
        if v and email and v.strip().lower() == email.strip().lower():
            raise ValueError("لا يمكن استخدام نفس البريد الإلكتروني كبريد أساسي وثانوي")
        return v

    @validator('phoneNumbers')
    def validate_phones(cls, v):
        pattern = re.compile(r"^(\+|00)[1-9]\d{6,13}$")
        for p in v:
            if p and not pattern.match(p.strip()):
                raise ValueError(f"رقم الهاتف '{p}' غير صحيح")
        return [p.strip() for p in v if p and p.strip()]
