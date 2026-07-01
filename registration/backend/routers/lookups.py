from fastapi import APIRouter, Depends, HTTPException
from typing import List
from core.database import get_db_connection

router = APIRouter(prefix="/api/registration/lookups", tags=["Lookups"])

@router.get("/interests")
def get_interests():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar FROM interests_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/languages")
def get_languages():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar FROM languages_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/countries")
def get_countries():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar, code FROM countries_master ORDER BY name_en ASC")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/universities/{country_id}")
def get_universities(country_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        if not country_id.isdigit():
            cursor.execute("SELECT id FROM countries_master WHERE code = %s", (country_id,))
            row = cursor.fetchone()
            if row:
                country_id = row['id']
            else:
                return []
        cursor.execute("SELECT id, name_en, name_ar FROM universities_master WHERE country_id = %s ORDER BY name_en ASC", (country_id,))
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/states/{country_id}")
def get_states(country_id: str):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        if not country_id.isdigit():
            cursor.execute("SELECT id FROM countries_master WHERE code = %s", (country_id,))
            row = cursor.fetchone()
            if row:
                country_id = row['id']
            else:
                return []
        cursor.execute("SELECT id, name_en, name_ar, code FROM states_master WHERE country_id = %s ORDER BY name_en ASC", (country_id,))
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/skills")
def get_skills():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        # Fetch all categories
        cursor.execute("SELECT id, name_en, name_ar FROM skill_categories")
        categories = cursor.fetchall()
        # Fetch all subcategories
        cursor.execute("SELECT id, category_id, name_en, name_ar FROM skill_subcategories")
        subcats = cursor.fetchall()
        # Fetch all skills
        cursor.execute("SELECT id, subcategory_id, name_en, name_ar FROM skills_master")
        skills = cursor.fetchall()
        
        # Build hierarchy
        result = []
        for cat in categories:
            cat_data = {**cat, "subcategories": []}
            for sub in subcats:
                if sub['category_id'] == cat['id']:
                    sub_data = {**sub, "skills": []}
                    for sk in skills:
                        if sk['subcategory_id'] == sub['id']:
                            sub_data['skills'].append(sk)
                    cat_data['subcategories'].append(sub_data)
            result.append(cat_data)
        return result
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/military-status")
def get_military_status():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar, code FROM military_status_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/identity-doc-types")
def get_identity_doc_types():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar, code FROM identity_doc_types_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/degree-levels")
def get_degree_levels():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar, type, code FROM degree_levels_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/grades")
def get_grades():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar, min_percentage, code FROM grades_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/ministries")
def get_ministries():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar FROM ministries_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/job-titles")
def get_job_titles():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar FROM job_titles_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/marital-status")
def get_marital_status():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar, code FROM marital_status_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/monthly-income")
def get_monthly_income():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar, code FROM monthly_income_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/ministries/{ministry_id}/authorities")
def get_ministry_authorities(ministry_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name FROM ministry_authorities WHERE ministry_id = %s ORDER BY name ASC", (ministry_id,))
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/universities/{university_id}/colleges")
def get_university_colleges(university_id: int):
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar FROM university_colleges WHERE university_id = %s ORDER BY name_en ASC", (university_id,))
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()

@router.get("/proficiencies")
def get_proficiencies():
    conn = get_db_connection()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, level_en, level_ar FROM language_proficiency_master")
        data = cursor.fetchall()
        return data
    finally:
        if 'cursor' in locals(): cursor.close()
        conn.close()
