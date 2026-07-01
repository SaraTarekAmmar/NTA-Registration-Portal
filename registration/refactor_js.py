import re

with open('registration.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Replace TOTAL_STEPS
js = js.replace('const TOTAL_STEPS = 10;', 'const TOTAL_STEPS = 40;')

# Re-mapping step numbers in validateCurrentStep:

# 2. Dates/Age Check (DOB between 16 and 60)
js = re.sub(r'if \((currentStep === 1)( && dobInput && dobInput\.value)\)', r'if (currentStep === 2\2)', js)

# 3. National ID match check
js = re.sub(r'if \((currentStep === 1)( && nidInput && nidInput\.value\.trim\(\)\.length === 14)', r'if (currentStep === 6\2)', js)

# 4. Professional History Timeline
js = re.sub(r'if \(currentStep === 4\) {([\s\S]*?)const starts = stepEl\.querySelectorAll', r'if (currentStep === 13) {\1const starts = stepEl.querySelectorAll', js)

# 5. Academic Grad Year Check
js = re.sub(r'if \((currentStep === 3)( && dobInput && dobInput\.value)\)', r'if (currentStep === 10\2)', js)

# 6. Step 10 — URL format
js = re.sub(r'if \(currentStep === 10\) {([\s\S]*?)stepEl\.querySelectorAll\(\'\.social-verify-row\'\)', r'if (currentStep === 40) {\1stepEl.querySelectorAll(\'.social-verify-row\')', js)

# 6b. URL Verification Check
js = re.sub(r'if \(currentStep === 6\) {([\s\S]*?)const urlInputs = stepEl\.querySelectorAll', r'if (currentStep === 26) {\1const urlInputs = stepEl.querySelectorAll', js)

# 6b. Step 2 – Emergency contact
js = re.sub(r'if \(currentStep === 2\) {([\s\S]*?)const contactCount = stepEl\.querySelector', r'if (currentStep === 9) {\1const contactCount = stepEl.querySelector', js)

# Email check logic
js = js.replace('const primaryEmail = stepEl.querySelector(\'input[name="primaryEmail"]\');', 
'''if (currentStep === 5) {
            const primaryEmail = stepEl.querySelector('input[name="primaryEmail"]');
            const secondaryEmail = stepEl.querySelector('input[name="secondaryEmail"]');
            if (primaryEmail && secondaryEmail && primaryEmail.value.trim() && secondaryEmail.value.trim()) {
                if (primaryEmail.value.trim().toLowerCase() === secondaryEmail.value.trim().toLowerCase()) {
                    primaryEmail.classList.add('error');
                    secondaryEmail.classList.add('error');
                    isValid = false;
                    if (!silent) window.showDropdownMessage("لا يمكن استخدام نفس البريد الإلكتروني كبريد أساسي وثانوي.", true);
                }
            }
        }
        const _dummyPrimaryEmail = null;''')
js = re.sub(r'const secondaryEmail = stepEl\.querySelector\(\'input\[name="secondaryEmail"\]\'\);\s*if \(primaryEmail && secondaryEmail[\s\S]*?\}\s*\}', '', js)

# 7. References Check
js = re.sub(r'if \(currentStep === 8\) {([\s\S]*?)const contacts = stepEl\.querySelectorAll\(\'input\[name="referenceContact\[\]"\]\'\)', r'if (currentStep === 30) {\1const contacts = stepEl.querySelectorAll(\'input[name="referenceContact[]"]\')', js)

# 8. Mandatory document uploads (removing the old one)
js = re.sub(r'// 8\. Mandatory document uploads — section 8[\s\S]*?// 9\. Step 3', '// 9. Step 3', js)

# 9. Step 3 — Education
js = re.sub(r'if \(currentStep === 3\) {([\s\S]*?)const degreeSel = document\.getElementById\(\'eduHighestDegree\'\)', r'if (currentStep === 10 || currentStep === 11 || currentStep === 12) {\1const degreeSel = document.getElementById(\'eduHighestDegree\')', js)

# 10. Step 4 — Employment
js = re.sub(r'if \(currentStep === 4\) {([\s\S]*?)const empStatus = document\.querySelector\(\'select\[name="empExperienceStatus"\]\'\)', r'if (currentStep === 13) {\1const empStatus = document.querySelector(\'select[name="empExperienceStatus"]\')', js)

# 11. Step 5 — Skills mandatory
js = re.sub(r'if \(currentStep === 5\) {', r'if (currentStep === 17 || currentStep === 18) {', js)
js = js.replace('const stepEl5 = document.querySelector(\'.reg-step[data-step="5"]\');', 'const stepEl5 = stepEl;')

# 12. Step 7 — Conditional
js = re.sub(r'if \(currentStep === 7\) {', r'if (currentStep >= 23 && currentStep <= 29) {', js)
js = js.replace('const stepEl7 = document.querySelector(\'.reg-step[data-step="7"]\');', 'const stepEl7 = stepEl;')

# 13. Section 1 conditional checks
js = re.sub(r'if \(currentStep === 1\) {', r'if (currentStep >= 6 && currentStep <= 8) {', js)

# Fix stepper update logic
js = js.replace('const progressPercent = ((currentStep - 1) / (TOTAL_STEPS - 1)) * 100;', 
'''const progressPercent = ((currentStep - 1) / (TOTAL_STEPS - 1)) * 100;
        const phaseLabel = stepEl ? stepEl.getAttribute('data-phase') : '';
        const phaseEl = document.getElementById('currentPhaseLabel');
        if (phaseEl && phaseLabel) phaseEl.innerText = phaseLabel;''')

with open('registration_new.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("JS Refactoring Complete")
