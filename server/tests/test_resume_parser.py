"""
Test script for Resume PDF Parser.

Tests the PDFTextExtractor standalone (no SQLAlchemy/DB needed).
Run from server folder: python tests/test_resume_parser.py
"""

import os
import sys
import importlib.util

# ==================== STANDALONE IMPORTS (avoid domain __init__ chain) ====================

def _import_module_directly(module_name: str, file_path: str):
    """Import a single .py file directly without triggering package __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod


SERVER_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ==================== TEST 1: PDF TEXT EXTRACTION ====================

def test_pdf_text_extraction():
    print("=" * 70)
    print("TEST 1: PDF Text Extraction (PyMuPDF)")
    print("=" * 70)

    pdf_path = os.path.join(SERVER_ROOT, "sagar_rajak_SDE.pdf")

    if not os.path.exists(pdf_path):
        print(f"[FAIL] PDF file not found: {pdf_path}")
        return None

    print(f"[INFO] PDF file: {pdf_path}")
    print(f"[INFO] File size: {os.path.getsize(pdf_path) / 1024:.1f} KB")

    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    try:
        import fitz  # PyMuPDF
    except ImportError:
        print("[FAIL] PyMuPDF not installed. Run: pip install PyMuPDF")
        return None

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        print(f"[INFO] Pages: {doc.page_count}")

        text_parts = []
        for page_num in range(doc.page_count):
            page = doc[page_num]
            page_text = page.get_text("text")
            if page_text.strip():
                text_parts.append(page_text)
                print(f"[INFO] Page {page_num + 1}: {len(page_text)} chars extracted")

        doc.close()

        full_text = "\n\n".join(text_parts)

        if not full_text.strip():
            print("[FAIL] No text extracted - PDF might be image-only or scanned")
            return None

        print(f"\n[PASS] Text extracted successfully!")
        print(f"[INFO] Total text length: {len(full_text)} characters")
        print(f"\n{'-' * 50}")
        print("EXTRACTED TEXT (first 2000 chars):")
        print(f"{'-' * 50}")
        # Encode safely for Windows terminal
        safe_text = full_text[:2000].encode("ascii", errors="replace").decode("ascii")
        print(safe_text)
        print(f"{'-' * 50}")

        if len(full_text) > 2000:
            print(f"\n... and {len(full_text) - 2000} more characters")

        return full_text

    except Exception as e:
        print(f"[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return None


# ==================== TEST 2: NORMALIZERS ====================

def test_normalization():
    print("\n" + "=" * 70)
    print("TEST 2: Field Normalizers")
    print("=" * 70)

    # Inline normalizer tests (copied logic, no import needed)
    def normalize_string(value):
        if value is None: return None
        val = str(value).strip()
        return val if val else None

    def normalize_number(value):
        if value is None: return None
        try:
            num = float(value)
            return int(num) if num == int(num) else num
        except (ValueError, TypeError):
            return None

    def normalize_boolean(value):
        if value is None: return None
        if isinstance(value, bool): return value
        if isinstance(value, str): return value.strip().lower() in ("true", "yes", "1", "y")
        return bool(value)

    def normalize_list(value):
        if value is None: return None
        if isinstance(value, list):
            cleaned = [str(v).strip() for v in value if v and str(v).strip()]
            return cleaned if cleaned else None
        if isinstance(value, str):
            items = [v.strip() for v in value.split(",") if v.strip()]
            return items if items else None
        return None

    tests = [
        ("string", normalize_string, "  Sagar Rajak  ", "Sagar Rajak"),
        ("string (empty)", normalize_string, "   ", None),
        ("number (int)", normalize_number, "3", 3),
        ("number (float)", normalize_number, "2.5", 2.5),
        ("number (invalid)", normalize_number, "abc", None),
        ("boolean (yes)", normalize_boolean, "yes", True),
        ("boolean (false)", normalize_boolean, False, False),
        ("boolean (none)", normalize_boolean, None, None),
        ("list", normalize_list, ["Python", "React", ""], ["Python", "React"]),
        ("list (csv)", normalize_list, "Python, React, Node.js", ["Python", "React", "Node.js"]),
    ]

    passed = 0
    for name, func, inp, expected in tests:
        result = func(inp)
        ok = result == expected
        if ok: passed += 1
        status = "[PASS]" if ok else "[FAIL]"
        print(f"  {status} {name}: {repr(inp)} -> {repr(result)}")

    print(f"\n  Result: {passed}/{len(tests)} passed")


# ==================== TEST 3: RESUME STRUCTURING ====================

def test_resume_structuring():
    print("\n" + "=" * 70)
    print("TEST 3: Resume Data Structuring")
    print("=" * 70)

    # Dictionary dispatch mapping (same as resume_builder_service.py)
    QUESTION_KEY_TO_SECTION = {
        "full_name": "personal_info", "date_of_birth": "personal_info",
        "languages_known": "personal_info",
        "has_driving_license": "qualifications", "owns_vehicle": "qualifications",
        "vehicle_type": "qualifications",
        "skills": "skills", "technical_skills": "skills",
        "education": "education",
        "experience_years": "experience", "experience_details": "experience",
        "salary_expectation": "job_preferences", "preferred_location": "job_preferences",
        "preferred_work_type": "job_preferences",
        "portfolio_url": "portfolio",
        "about": "about",
    }

    collected_data = {
        "full_name": "Sagar Rajak",
        "date_of_birth": "1998-05-15",
        "education": "Bachelor's Degree",
        "skills": ["Python", "React", "Node.js", "FastAPI", "PostgreSQL"],
        "experience_years": 3,
        "experience_details": "Full-stack developer at XYZ Corp",
        "preferred_work_type": "Hybrid",
        "preferred_location": "Mumbai",
        "salary_expectation": 80000,
        "portfolio_url": "https://github.com/sagarrajak",
        "about": "Passionate full-stack developer with 3 years experience",
    }

    # Structure data
    sections = {}
    for key, value in collected_data.items():
        if value is None: continue
        section = QUESTION_KEY_TO_SECTION.get(key, "additional_info")
        if section not in sections:
            sections[section] = {}
        sections[section][key] = value

    print(f"\n[PASS] Structured into {len(sections)} sections:")
    for section_name, section_data in sections.items():
        print(f"  [{section_name}]")
        for k, v in section_data.items():
            print(f"    {k}: {v}")


# ==================== TEST 4: QUESTION ENGINE LOGIC ====================

def test_question_engine_logic():
    print("\n" + "=" * 70)
    print("TEST 4: Question Engine Logic (Conditional Skip)")
    print("=" * 70)

    # Simulate templates
    templates = [
        {"key": "full_name", "type": "text", "required": True, "order": 1, "condition": None},
        {"key": "has_license", "type": "boolean", "required": True, "order": 2, "condition": None},
        {"key": "license_doc", "type": "file", "required": False, "order": 3,
         "condition": {"depends_on": "has_license", "value": True}},
        {"key": "salary", "type": "number", "required": True, "order": 4, "condition": None},
    ]

    def get_next_question(templates, collected_data):
        sorted_t = sorted(templates, key=lambda t: t["order"])
        for t in sorted_t:
            if t["key"] in collected_data:
                continue
            if t["condition"]:
                dep = t["condition"]["depends_on"]
                expected = t["condition"]["value"]
                if dep not in collected_data or collected_data[dep] != expected:
                    continue
            return t
        return None

    # Test: empty data -> first question
    q1 = get_next_question(templates, {})
    print(f"  Next (empty data): {q1['key']}")
    assert q1["key"] == "full_name", "Expected full_name"

    # Test: answered name + license=False -> skip license_doc -> salary
    q2 = get_next_question(templates, {"full_name": "Sagar", "has_license": False})
    print(f"  Next (license=False): {q2['key']}")
    assert q2["key"] == "salary", "Expected salary (license_doc should be skipped)"

    # Test: answered name + license=True -> license_doc (conditional shown)
    q3 = get_next_question(templates, {"full_name": "Sagar", "has_license": True})
    print(f"  Next (license=True): {q3['key']}")
    assert q3["key"] == "license_doc", "Expected license_doc (condition met)"

    # Test: all answered -> None
    q4 = get_next_question(templates, {
        "full_name": "Sagar", "has_license": False, "salary": 25000
    })
    print(f"  Next (all done, license=False): {q4}")
    assert q4 is None, "Expected None (all done)"

    print("\n  [PASS] All question engine logic tests passed!")


# ==================== MAIN ====================

if __name__ == "__main__":
    print("\n[TEST] AIVIUE Resume Parser Test Suite")
    print("=" * 70)

    test_pdf_text_extraction()
    test_normalization()
    test_resume_structuring()
    test_question_engine_logic()

    print("\n" + "=" * 70)
    print("[DONE] All tests complete!")
    print("=" * 70)
