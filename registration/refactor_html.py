import re
from bs4 import BeautifulSoup
import json

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

# Reconstruct the form inner HTML
new_steps = []

# Step 1: Names
step1 = []
step1.append(find_group_by_name('fullName'))
step1.append(find_group_by_name('fullNameEn'))

# Step 2: Demographics
step2 = []
step2.append(find_group_by_name('dob'))
step2.append(find_group_by_name('gender'))

# Step 3: Socio-Economic
step3 = []
step3.append(find_group_by_name('maritalStatus'))
step3.append(find_group_by_name('monthlyAverageIncome'))

# Step 4: Location & Contact
step4 = []
step4.append(find_group_by_name('countryOfStay'))
step4.append(find_group_by_name('governmentOrState'))
step4.append(find_group_by_name('city'))
step4.append(find_group_by_name('address'))
step4.append(find_group_by_name('mobileNumber1'))
step4.append(find_group_by_name('mobileNumber2'))
step4.append(find_group_by_name('whatsappNumber'))

# Step 5: Digital Comm
step5 = []
step5.append(find_group_by_name('primaryEmail'))
step5.append(find_group_by_name('secondaryEmail'))

# Step 6: Identity Docs
step6 = []
step6.append(find_group_by_name('identityDocType'))
step6.append(find_block_by_id('nationalIdGroup'))
step6.append(find_block_by_id('passportNumberGroup'))
step6.append(find_block_by_id('identityDocScanGroup'))

# Step 7: Nationalities
step7 = []
step7.append(find_group_by_name('numberOfNationalities'))
step7.append(find_group_by_name('nationality'))
step7.append(find_block_by_id('secondNationalityGroup'))
step7.append(find_block_by_id('thirdNationalityGroup'))

# Step 8: Military
step8 = []
step8.append(find_group_by_name('militaryStatus'))
step8.append(find_block_by_id('militaryReasonGroup'))

# Step 9: Emergency
step9 = []
step9.append(find_group_by_name('emergencyContactsCount'))
step9.append(find_group_by_name('emergencyName1'))
step9.append(find_group_by_name('emergencyPhone1'))
step9.append(find_group_by_name('emergencyAddress1'))
step9.append(find_group_by_name('emergencyId1'))
step9.append(find_block_by_id('emergencyContact2Block'))

# Step 10: Main Education
step10 = []
step10.append(find_group_by_name('eduHighestDegree'))
step10.append(find_block_by_id('eduMainFieldsBlock'))

# Step 11: Postgraduate
step11 = []
step11.append(find_block_by_id('eduPostgraduateSection'))

# Step 12: Standardized Tests
step12 = []
test_lbl = soup.find('label', string=re.compile('الاختبارات والشهادات المعيارية'))
if test_lbl:
    test_group = test_lbl.find_parent(class_='form-group')
    step12.append(test_group)

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

step13 = []
step13.append(find_group_by_name('empExperienceStatus'))
step13.append(find_block_by_id('empHaveExperienceBlock'))

# Step 14: Role Scale
step14 = []
step14.append(find_group_by_name('currentJobTitle'))
step14.append(find_group_by_name('yearsManagementExperience'))

# Step 15: Leadership Scale
step15 = []
step15.append(find_group_by_name('directReports'))
step15.append(find_group_by_name('globalExperience'))

# Step 16: Languages
step16 = []
step16.append(find_group_by_name('nativeLanguage'))
step16.append(find_group_by_name('englishProficiency'))
step16.append(BeautifulSoup("""
    <div id="additionalLanguagesContainer"></div>
    <button type="button" class="reg-btn reg-btn--outline mt-3" id="addLanguageBtn">+ إضافة لغة أخرى (اختياري)</button>
""", "html.parser"))

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
step18 = []
step18.append(find_group_by_name('interestsDescription'))
interest_lbl = soup.find('label', string=re.compile('اختر ما يصل إلى 5 اهتمامات'))
if interest_lbl: step18.append(interest_lbl.find_parent(class_='form-group'))

# Step 19: Social Hub
step19 = []
step19.append(find_group_by_name('usesSocialMedia'))
step19.append(find_block_by_id('socialMediaPlatformsBlock'))

# Step 20: Prizes & Awards
step20 = []
step20.append(find_group_by_name('hasPrizesAwards'))
step20.append(find_block_by_id('prizesAwardsBlock'))

# Step 21: Conferences
step21 = []
step21.append(find_group_by_name('hasConferencesWorkshops'))
step21.append(find_block_by_id('conferencesWorkshopsBlock'))

# Step 22: Extracurriculars
step22 = []
ea_lbl = soup.find('label', string=re.compile('الجوائز والأنشطة الأكاديمية'))
if ea_lbl: step22.append(ea_lbl.find_parent(class_='form-group'))

# Step 23: Voluntary Work
step23 = []
step23.append(find_group_by_name('hasPublicVoluntaryWork'))
step23.append(find_block_by_id('publicVoluntaryWorkBlock'))

# Step 24: Political Work
step24 = []
step24.append(find_group_by_name('hasPoliticalParticipation'))
step24.append(find_block_by_id('politicalWorkBlock'))

# Step 25: Political Candidacy
step25 = []
step25.append(find_group_by_name('hasPoliticalCandidacy'))
step25.append(find_block_by_id('politicalCandidacyBlock'))

# Step 26: Creative Assets
step26 = []
step26.append(find_group_by_name('portfolioUrl'))
step26.append(find_group_by_name('portfolioFile'))

# Step 27: Core Motivation
step27 = []
step27.append(find_group_by_name('primaryLearningObjective'))
step27.append(find_group_by_name('uniqueContribution'))
step27.append(find_group_by_name('futureCareerGoal'))

# Step 28: Funding & Scholarship
step28 = []
step28.append(find_group_by_name('fundingSource'))
step28.append(find_group_by_name('scholarshipEssay'))
step28.append(find_group_by_name('scholarshipEssayFile'))

# Step 29: Legal Status
step29 = []
step29.append(find_group_by_name('hasPriorCriminalConvictions'))
step29.append(find_block_by_id('legalStatusBlock'))

# Step 30: References
step30 = []
ref_lbl = soup.find('label', string=re.compile('المعرفون المهنيون'))
if ref_lbl: step30.append(ref_lbl.find_parent(class_='form-group'))

# Step 31: Career Docs
step31 = []
step31.append(find_group_by_name('cvResume'))
step31.append(find_group_by_name('lettersOfRecommendation'))

# Step 32: Accommodation
step32 = []
step32.append(find_group_by_name('dietaryRestrictions'))
step32.append(find_group_by_name('accessibilityRequirements'))

# Step 33: Agreements
step33 = []
step33.append(find_group_by_name('scheduleAcknowledgment'))
step33.append(find_group_by_name('dataAccuracyTermsConfirmed'))

# Step 34: Psychometric A
step34 = []
step34.append(find_group_by_name('cog1'))
step34.append(find_group_by_name('cog2'))

# Step 35: Psychometric B
step35 = []
step35.append(find_group_by_name('cog3'))
step35.append(find_group_by_name('cog4'))

# Step 36: Psychometric C
step36 = []
step36.append(find_group_by_name('cog5'))
step36.append(find_group_by_name('cog6'))

# Step 37: Psychometric D
step37 = []
step37.append(find_group_by_name('cog7'))
step37.append(find_group_by_name('cog8'))

# Step 38: Psychometric E
step38 = []
step38.append(find_group_by_name('cog9'))

# Step 39: Visual ID
step39 = []
step39.append(find_group_by_name('photoFront'))

# Step 40: Social Verification URLs
step40 = []
sv = soup.find(id='socialVerificationContainer')
if sv: step40.append(sv.find_parent(class_='form-group') or sv)
else:
    sv1 = find_group_by_name('socialProfileFacebookUrl')
    if sv1:
        step40.append(sv1.find_parent()) # Or just append all of them

steps = [
    (1, "Personal Information", step1),
    (2, "Personal Information", step2),
    (3, "Personal Information", step3),
    (4, "Contact Details", step4),
    (5, "Contact Details", step5),
    (6, "Identity & Military", step6),
    (7, "Identity & Military", step7),
    (8, "Identity & Military", step8),
    (9, "Emergency Contacts", step9),
    (10, "Educational Background", step10),
    (11, "Educational Background", step11),
    (12, "Educational Background", step12),
    (13, "Employment History", step13),
    (14, "Employment History", step14),
    (15, "Employment History", step15),
    (16, "Skills & Languages", step16),
    (17, "Skills & Languages", step17),
    (18, "Skills & Languages", step18),
    (19, "Activities & Social", step19),
    (20, "Activities & Social", step20),
    (21, "Activities & Social", step21),
    (22, "Activities & Social", step22),
    (23, "Activities & Social", step23),
    (24, "Activities & Social", step24),
    (25, "Activities & Social", step25),
    (26, "Activities & Social", step26),
    (27, "Motivation & Goals", step27),
    (28, "Motivation & Goals", step28),
    (29, "Legal & References", step29),
    (30, "Legal & References", step30),
    (31, "Legal & References", step31),
    (32, "Logistics & Needs", step32),
    (33, "Logistics & Needs", step33),
    (34, "Cognitive Assessment", step34),
    (35, "Cognitive Assessment", step35),
    (36, "Cognitive Assessment", step36),
    (37, "Cognitive Assessment", step37),
    (38, "Cognitive Assessment", step38),
    (39, "Final Verification", step39),
    (40, "Final Verification", step40),
]

form_inner = ""
for step_num, phase_name, elements in steps:
    content = ""
    for el in elements:
        if el:
            # We need to wrap it correctly if it's already a group.
            # But the parent might have multiple children if we grab `sv1.find_parent()`. 
            # Let's just stringify.
            if isinstance(el, list):
                for e in el: content += str(e)
            else:
                content += str(el)
    
    if content.strip():
        step_class = "reg-step active" if step_num == 1 else "reg-step"
        form_inner += f"""
<div class="{step_class}" data-step="{step_num}" data-phase="{phase_name}">
    <h2 class="reg-step__title">{phase_name}</h2>
    {content}
</div>
"""

form = soup.find('form', id='regForm')
if form:
    banner = form.find(id='roleAlertBanner')
    banner_html = str(banner) if banner else ""
    
    # We must keep buttons. They are actually right after reg-card or inside regForm?
    # Let's check where the buttons are.
    btn_prev = soup.find(id='btnPrev')
    btn_next = soup.find(id='btnNext')
    btn_sub = soup.find(id='btnSubmit')
    
    # Actually, we shouldn't wipe out the whole form if buttons are there, we just replace the steps.
    for step in form.find_all('div', class_='reg-step'):
        step.decompose()
    
    # Insert new steps after the alert banner
    if banner:
        banner.insert_after(BeautifulSoup(form_inner, "html.parser"))
    else:
        form.insert(0, BeautifulSoup(form_inner, "html.parser"))

stepper = soup.find(class_='reg-stepper')
if stepper:
    stepper.clear()
    stepper.append(BeautifulSoup("""
<div class="reg-stepper__bar-wrap">
    <div class="reg-stepper__bar" id="progressBar" style="--progress: 2.5%"></div>
</div>
<h3 id="currentPhaseLabel" style="margin-top:10px;text-align:center;color:#fff;">Personal Information</h3>
    """, "html.parser"))

with open('index_new.html', 'w', encoding='utf-8') as f:
    f.write(str(soup))

print("HTML Refactoring Complete")
