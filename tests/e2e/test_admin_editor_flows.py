import os
import re
import uuid

import pytest

playwright = pytest.importorskip("playwright.sync_api")
expect = playwright.expect


RUN_E2E = os.getenv("NTA_E2E", "").lower() in {"1", "true", "yes"}
ALLOW_MUTATION = os.getenv("NTA_E2E_ALLOW_MUTATION", "").lower() in {"1", "true", "yes"}

pytestmark = pytest.mark.skipif(
    not RUN_E2E,
    reason="Set NTA_E2E=1 and point the tests at running admin/editor portals.",
)


ADMIN_BASE = os.getenv("NTA_ADMIN_BASE_URL", "http://localhost:8001").rstrip("/")
EDITOR_BASE = os.getenv("NTA_EDITOR_BASE_URL", "http://localhost:8003").rstrip("/")


def env_required(name):
    value = os.getenv(name)
    if not value:
        pytest.skip(f"{name} is required for this E2E test")
    return value


def login_admin(page):
    page.goto(f"{ADMIN_BASE}/admin-login.html")
    page.locator("#adminEmail").fill(env_required("NTA_ADMIN_EMAIL"))
    page.locator("#adminNationalId").fill(env_required("NTA_ADMIN_NATIONAL_ID"))
    page.locator("#adminPassword").fill(env_required("NTA_ADMIN_PASSWORD"))
    page.locator("#adminLoginBtn").click()
    expect(page).to_have_url(re.compile(r"admin-dashboard\.html"), timeout=15000)


def login_editor(page):
    page.goto(f"{EDITOR_BASE}/editor-login.html")
    page.locator("#editorEmail").fill(env_required("NTA_EDITOR_EMAIL"))
    page.locator("#editorNationalId").fill(env_required("NTA_EDITOR_NATIONAL_ID"))
    page.locator("#editorPassword").fill(env_required("NTA_EDITOR_PASSWORD"))
    page.locator("#editorLoginBtn").click()
    expect(page).to_have_url(re.compile(r"editor-dashboard\.html"), timeout=15000)


def test_admin_login_theme_toggle_and_logout(page):
    login_admin(page)
    expect(page.locator("#themeToggle")).to_be_visible(timeout=10000)
    before = page.evaluate("document.documentElement.classList.contains('light-mode')")
    page.locator("#themeToggle").click()
    page.wait_for_function(
        "before => document.documentElement.classList.contains('light-mode') !== before",
        arg=before,
    )
    page.locator("#logoutBtn").click()
    expect(page).to_have_url(re.compile(r"admin-login\.html"), timeout=10000)


def test_editor_login_theme_toggle_and_logout(page):
    login_editor(page)
    expect(page.locator("#themeToggle")).to_be_visible(timeout=10000)
    before = page.evaluate("document.documentElement.classList.contains('light-mode')")
    page.locator("#themeToggle").click()
    page.wait_for_function(
        "before => document.documentElement.classList.contains('light-mode') !== before",
        arg=before,
    )
    page.locator("#editorLogoutBtn").click()
    expect(page).to_have_url(re.compile(r"editor-login\.html"), timeout=10000)


@pytest.mark.skipif(not ALLOW_MUTATION, reason="Set NTA_E2E_ALLOW_MUTATION=1 to run DB-mutating editor course tests.")
def test_editor_course_create_publish_material_upload_session_edit_and_delete(page, tmp_path):
    login_editor(page)

    unique = uuid.uuid4().hex[:8]
    title = f"اختبار تلقائي {unique}"
    material_path = tmp_path / "nta-e2e-material.pdf"
    material_path.write_bytes(b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF\n")

    page.goto(f"{EDITOR_BASE}/editor-course-form.html")
    page.locator("#titleAr").fill(title)
    page.locator("#titleEn").fill(f"NTA E2E {unique}")
    page.locator("#description").fill("وصف تلقائي للتحقق من مسار إنشاء الدورة ونشرها.")
    page.locator("#durationWeeks").fill("2")
    page.locator("#totalSessions").fill("1")
    page.locator("#continueBtn1").click()

    page.get_by_role("button", name=re.compile("إضافة جلسة")).click()
    page.locator('#sessionsList input[placeholder="عنوان الجلسة"]').first.fill("جلسة اختبار أولى")
    page.get_by_role("button", name=re.compile("المتابعة")).click()

    page.locator("#fileInput").set_input_files(str(material_path))
    page.get_by_role("button", name=re.compile("المتابعة")).click()
    page.get_by_role("button", name=re.compile("المتابعة")).click()

    with page.expect_response(lambda r: "/api/courses/save-with-sessions" in r.url and r.request.method == "POST") as saved:
        page.locator("#publishBtn").click()
        page.locator("#editorConfirmOk").click()
    assert saved.value.ok
    course_id = saved.value.json()["id"]

    try:
        expect(page).to_have_url(re.compile(r"editor-courses\.html"), timeout=15000)

        page.goto(f"{EDITOR_BASE}/editor-course-form.html?id={course_id}")
        expect(page.locator("#titleAr")).to_have_value(title, timeout=10000)
        page.locator("#continueBtn1").click()
        expect(page.locator('#sessionsList input[placeholder="عنوان الجلسة"]')).to_have_count(1, timeout=10000)
        page.locator('#sessionsList input[placeholder="عنوان الجلسة"]').first.fill("جلسة اختبار معدلة")
        page.get_by_role("button", name="حذف").first.click()
        page.locator("#editorConfirmOk").click()
        expect(page.locator('#sessionsList input[placeholder="عنوان الجلسة"]')).to_have_count(0, timeout=10000)
        page.get_by_role("button", name=re.compile("إضافة جلسة")).click()
        page.locator('#sessionsList input[placeholder="عنوان الجلسة"]').first.fill("جلسة اختبار بعد الحذف")
        page.get_by_role("button", name=re.compile("حفظ مسودة")).first.click()
        expect(page.locator(".editor-toast")).to_contain_text("تم حفظ", timeout=15000)
    finally:
        token = page.evaluate("localStorage.getItem('editor_token')")
        if token:
            page.request.delete(
                f"{EDITOR_BASE}/api/courses/{course_id}",
                headers={"Authorization": f"Bearer {token}"},
            )
