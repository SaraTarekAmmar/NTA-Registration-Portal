import os

steps = [
    (22, 'extracurriculars', 'Activities & Social'),
    (30, 'references', 'Legal & References'),
    (34, 'psychometric_a', 'Cognitive Assessment'),
    (35, 'psychometric_b', 'Cognitive Assessment'),
    (36, 'psychometric_c', 'Cognitive Assessment'),
    (37, 'psychometric_d', 'Cognitive Assessment'),
    (38, 'psychometric_e', 'Cognitive Assessment'),
    (39, 'visual_id', 'Final Verification'),
]

for step_num, file_suffix, phase_name in steps:
    file_path = f'components/step_{step_num}_{file_suffix}.html'
    component_html = f"""<div class="step-card">
    <h2 style="margin-bottom: 1.5rem;">{phase_name}</h2>
    <form id="stepForm">
        <div class="form-group"><label>Placeholder for {file_suffix}</label><input type="text" class="inp" name="{file_suffix}_data"></div>
        <button type="submit" class="btn btn-primary" style="width: 100%; margin-top: 1.5rem;">حفظ ومتابعة</button>
    </form>
</div>"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(component_html)

print('Filled missing steps.')
