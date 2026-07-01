from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import mysql.connector
from pathlib import Path
import os
from dotenv import load_dotenv

from core.database import get_db_connection

router = APIRouter(prefix="/api/skills", tags=["skills"])

@router.get("/tree")
async def get_skills_tree():
    """Returns the full hierarchy of categories -> subcategories -> skills"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Fetch Categories
        cursor.execute("SELECT id, name_en, name_ar FROM skill_categories")
        categories = cursor.fetchall()
        
        # Fetch Subcategories
        cursor.execute("SELECT id, category_id, name_en, name_ar FROM skill_subcategories")
        subcategories = cursor.fetchall()
        
        # Fetch Skills
        cursor.execute("SELECT id, subcategory_id, name_en, name_ar FROM skills_master")
        skills = cursor.fetchall()
        
        # Build Tree
        cat_map = {cat['id']: {**cat, 'subcategories': []} for cat in categories}
        sub_map = {sub['id']: {**sub, 'skills': []} for sub in subcategories}
        
        for sub in subcategories:
            cat_id = sub['category_id']
            if cat_id in cat_map:
                cat_map[cat_id]['subcategories'].append(sub_map[sub['id']])
        
        for skill in skills:
            sub_id = skill['subcategory_id']
            if sub_id in sub_map:
                sub_map[sub_id]['skills'].append(skill)
        
        return list(cat_map.values())
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        cursor.close()
        conn.close()

@router.get("/categories")
async def list_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM skill_categories")
        res = cursor.fetchall()
        return res
    finally:
        cursor.close()
        conn.close()

@router.get("/subcategories/{category_id}")
async def list_subcategories(category_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM skill_subcategories WHERE category_id = %s", (category_id,))
        res = cursor.fetchall()
        return res
    finally:
        cursor.close()
        conn.close()

@router.get("/list/{subcategory_id}")
async def list_skills(subcategory_id: int):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM skills_master WHERE subcategory_id = %s", (subcategory_id,))
        res = cursor.fetchall()
        return res
    finally:
        cursor.close()
        conn.close()

@router.get("/languages")
async def list_languages():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, name_en, name_ar FROM languages_master")
        res = cursor.fetchall()
        return res
    finally:
        cursor.close()
        conn.close()

@router.get("/proficiencies")
async def list_proficiencies():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, level_en, level_ar FROM language_proficiency_master")
        res = cursor.fetchall()
        return res
    finally:
        cursor.close()
        conn.close()
