import re
from bs4 import BeautifulSoup
import json
import os

if not os.path.exists('components'):
    os.makedirs('components')

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

def find_group_by_name(name):
    el = soup.find(['input', 'select', 'textarea'], {'name': name})
    if el:
        return el.find_parent(class_='form-group')
    return None

def find_block_by_id(block_id):
    return soup.find(id=block_id)

to_remove = ['organizationSize', 'annualBudgetManaged', 'communityLeadership', 'employerNoc', 'criminalRecord']
for name in to_remove:
    el = soup.find(['input', 'select', 'textarea'], {'name': name})
    if el:
        group = el.find_parent(class_='form-group')
        if group:
            group.decompose()

# Step 1: Names
step1 = [find_group_by_name('fullName'), find_group_by_name('fullNameEn')]
# Step 2: Demographics
step2 = [find_group_by_name('dob'), find_group_by_name('gender')]
# Step 3: Socio-Economic
step3 = [find_group_by_name('maritalStatus'), find_group_by_name('monthlyAverageIncome')]
# Step 4: Location & Contact
step4 = [find_group_by_name('countryOfStay'), find_group_by_name('governmentOrState'), find_group_by_name('city'), find_group_by_name('address'), find_group_by_name('mobileNumber1'), find_group_by_name('mobileNumber2'), find_group_by_name('whatsappNumber')]
# Step 5: Digital Comm
step5 = [find_group_by_name('primaryEmail'), find_group_by_name('secondaryEmail')]
# Step 6: Identity Docs
step6 = [find_group_by_name('identityDocType'), find_block_by_id('nationalIdGroup'), find_block_by_id('passportNumberGroup'), find_block_by_id('identityDocScanGroup')]
# Step 7: Nationalities
step7 = [find_group_by_name('numberOfNationalities'), find_group_by_name('nationality'), find_block_by_id('secondNationalityGroup'), find_block_by_id('thirdNationalityGroup')]
# Step 8: Military
step8 = [find_group_by_name('militaryStatus'), find_block_by_id('militaryReasonGroup')]
# Step 9: Emergency
step9 = [find_group_by_name('emergencyContactsCount'), find_group_by_name('emergencyName1'), find_group_by_name('emergencyPhone1'), find_group_by_name('emergencyAddress1'), find_group_by_name('emergencyId1'), find_block_by_id('emergencyContact2Block')]
# Step 10: Main Education
step10 = [find_group_by_name('eduHighestDegree'), find_block_by_id('eduMainFieldsBlock')]
# Step 11: Postgraduate
step11 = [find_block_by_id('eduPostgraduateSection')]
# Step 12: Standardized Tests
step12 = []
test_lbl = soup.find('label', string=re.compile('الاختبارات والشهادات المعيارية'))
if test_lbl: step12.append(test_lbl.find_parent(class_='form-group'))

# Step 13: Employment Core
legacy_start = soup.find('input', {'name': 'startDate[]'})
if legacy_start:
    lg1 = legacy_start.find_parent(class_='form-group')
    if lg1: lg1.decompose()
legacy_end = soup.find('input', {'name': 'endDate[]'})
if legacy_end:
    lg2 = legacy_end.find_parent(class_='form-group')
    if lg2: lg2.decompose()
legacy_resp = soup.find('textarea', {'name': 'keyResponsibilities[]'})
if legacy_resp:
    lg3 = legacy_resp.find_parent(class_='form-group')
    if lg3: lg3.decompose()

emp_card = soup.find(class_='emp-history-card')
if emp_card:
    row = soup.new_tag('div')
    row['class'] = 'reg-form__row'
    row.append(BeautifulSoup("""
        <div class="form-group">
            <label>تاريخ البدء (Start Date) (اجبارى)</label>
            <input type="date" class="emp-start-date" name="startDate[]" required>
        </div>
        <div class="form-group">
            <label>تاريخ الانتهاء (End Date) (اجبارى إذا لم تكن تعمل حالياً)</label>
            <input type="date" class="emp-end-date" name="endDate[]">
        </div>
    """, "html.parser"))
    emp_card.append(row)
    emp_card.append(BeautifulSoup("""
        <div class="form-group">
            <label>المسؤوليات الرئيسية (Key Responsibilities) (اختياري)</label>
            <textarea name="keyResponsibilities[]" class="emp-responsibilities"></textarea>
        </div>
    """, "html.parser"))

step13 = [find_group_by_name('empExperienceStatus'), find_block_by_id('empHaveExperienceBlock')]
# Step 14: Role Scale
step14 = [find_group_by_name('currentJobTitle'), find_group_by_name('yearsManagementExperience')]
# Step 15: Leadership Scale
step15 = [find_group_by_name('directReports'), find_group_by_name('globalExperience')]
# Step 16: Languages
step16 = [find_group_by_name('nativeLanguage'), find_group_by_name('englishProficiency'), BeautifulSoup("""<div id="additionalLanguagesContainer"></div><button type="button" class="reg-btn reg-btn--outline mt-3" id="addLanguageBtn">+ إضافة لغة أخرى (اختياري)</button>""", "html.parser")]
# Step 17: Skills Matrix
step17 = []
tech_container = soup.find(id='technicalSkillsContainer')
comp_container = soup.find(id='computerSkillsContainer')
soft_container = soup.find(id='softSkillsContainer')
if tech_container: step17.append(tech_container.find_parent())
if comp_container: step17.append(comp_container.find_parent())
if soft_container: step17.append(soft_container.find_parent())
step17.append(find_group_by_name('otherSkillsFreeText'))

# Step 18: Interests
step18 = [find_group_by_name('interestsDescription')]
interest_lbl = soup.find('label', string=re.compile('اختر ما يصل إلى 5 اهتمامات'))
if interest_lbl: step18.append(interest_lbl.find_parent(class_='form-group'))

# Step 19: Social Hub
step19 = [find_group_by_name('usesSocialMedia'), find_block_by_id('socialMediaPlatformsBlock')]
# Step 20: Prizes & Awards
step20 = [find_group_by_name('hasPrizesAwards'), find_block_by_id('prizesAwardsBlock')]
# Step 21: Conferences
step21 = [find_group_by_name('hasConferencesWorkshops'), find_block_by_id('conferencesWorkshopsBlock')]
# Step 22: Extracurriculars
step22 = []
ea_lbl = soup.find('label', string=re.compile('الجوائز والأنشطة الأكاديمية'))
if ea_lbl: step22.append(ea_lbl.find_parent(class_='form-group'))

# Step 23: Voluntary Work
step23 = [find_group_by_name('hasPublicVoluntaryWork'), find_block_by_id('publicVoluntaryWorkBlock')]
# Step 24: Political Work
step24 = [find_group_by_name('hasPoliticalParticipation'), find_block_by_id('politicalWorkBlock')]
# Step 25: Political Candidacy
step25 = [find_group_by_name('hasPoliticalCandidacy'), find_block_by_id('politicalCandidacyBlock')]
# Step 26: Creative Assets
step26 = [find_group_by_name('portfolioUrl'), find_group_by_name('portfolioFile')]
# Step 27: Core Motivation
step27 = [find_group_by_name('primaryLearningObjective'), find_group_by_name('uniqueContribution'), find_group_by_name('futureCareerGoal')]
# Step 28: Funding & Scholarship
step28 = [find_group_by_name('fundingSource'), find_group_by_name('scholarshipEssay'), find_group_by_name('scholarshipEssayFile')]
# Step 29: Legal Status
step29 = [find_group_by_name('hasPriorCriminalConvictions'), find_block_by_id('legalStatusBlock')]
# Step 30: References
step30 = []
ref_lbl = soup.find('label', string=re.compile('المعرفون المهنيون'))
if ref_lbl: step30.append(ref_lbl.find_parent(class_='form-group'))

# Step 31: Career Docs
step31 = [find_group_by_name('cvResume'), find_group_by_name('lettersOfRecommendation')]
# Step 32: Accommodation
step32 = [find_group_by_name('dietaryRestrictions'), find_group_by_name('accessibilityRequirements')]
# Step 33: Agreements
step33 = [find_group_by_name('scheduleAcknowledgment'), find_group_by_name('dataAccuracyTermsConfirmed')]
# Step 34: Psychometric A
step34 = [find_group_by_name('cog1'), find_group_by_name('cog2')]
# Step 35: Psychometric B
step35 = [find_group_by_name('cog3'), find_group_by_name('cog4')]
# Step 36: Psychometric C
step36 = [find_group_by_name('cog5'), find_group_by_name('cog6')]
# Step 37: Psychometric D
step37 = [find_group_by_name('cog7'), find_group_by_name('cog8')]
# Step 38: Psychometric E
step38 = [find_group_by_name('cog9')]
# Step 39: Visual ID
step39 = [find_group_by_name('photoFront')]
# Step 40: Social Verification URLs
step40 = []
sv = soup.find(id='socialVerificationContainer')
if sv: step40.append(sv.find_parent(class_='form-group') or sv)
else:
    sv1 = find_group_by_name('socialProfileFacebookUrl')
    if sv1:
        step40.append(sv1.find_parent())

steps = [
    (1, "names", "Personal Information", step1),
    (2, "demographics", "Personal Information", step2),
    (3, "socio_economic", "Personal Information", step3),
    (4, "location_contact", "Contact Details", step4),
    (5, "digital_comm", "Contact Details", step5),
    (6, "identity_docs", "Identity & Military", step6),
    (7, "nationalities", "Identity & Military", step7),
    (8, "military", "Identity & Military", step8),
    (9, "emergency", "Emergency Contacts", step9),
    (10, "main_education", "Educational Background", step10),
    (11, "postgraduate", "Educational Background", step11),
    (12, "standardized_tests", "Educational Background", step12),
    (13, "employment_core", "Employment History", step13),
    (14, "role_scale", "Employment History", step14),
    (15, "leadership_scale", "Employment History", step15),
    (16, "languages", "Skills & Languages", step16),
    (17, "skills_matrix", "Skills & Languages", step17),
    (18, "interests", "Skills & Languages", step18),
    (19, "social_hub", "Activities & Social", step19),
    (20, "prizes_awards", "Activities & Social", step20),
    (21, "conferences", "Activities & Social", step21),
    (22, "extracurriculars", "Activities & Social", step22),
    (23, "voluntary_work", "Activities & Social", step23),
    (24, "political_work", "Activities & Social", step24),
    (25, "political_candidacy", "Activities & Social", step25),
    (26, "creative_assets", "Activities & Social", step26),
    (27, "core_motivation", "Motivation & Goals", step27),
    (28, "funding_scholarship", "Motivation & Goals", step28),
    (29, "legal_status", "Legal & References", step29),
    (30, "references", "Legal & References", step30),
    (31, "career_docs", "Legal & References", step31),
    (32, "accommodation", "Logistics & Needs", step32),
    (33, "agreements", "Logistics & Needs", step33),
    (34, "psychometric_a", "Cognitive Assessment", step34),
    (35, "psychometric_b", "Cognitive Assessment", step35),
    (36, "psychometric_c", "Cognitive Assessment", step36),
    (37, "psychometric_d", "Cognitive Assessment", step37),
    (38, "psychometric_e", "Cognitive Assessment", step38),
    (39, "visual_id", "Final Verification", step39),
    (40, "social_urls", "Final Verification", step40),
]

for step_num, file_suffix, phase_name, elements in steps:
    content = ""
    for el in elements:
        if el:
            if isinstance(el, list):
                for e in el: content += str(e)
            else:
                content += str(el)
    
    if content.strip():
        file_path = f"components/step_{step_num}_{file_suffix}.html"
        component_html = f'''<div class="step-card">
    <h2 style="margin-bottom: 1.5rem;">{phase_name}</h2>
    <form id="stepForm">
        {content}
        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 1.5rem;">حفظ ومتابعة</button>
    </form>
</div>'''
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(component_html)

print("Created 40 component files successfully")
