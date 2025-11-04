import streamlit as st
import re
import os
from fpdf import FPDF

st.set_page_config(page_title="Resume Screener", layout="centered")

st.markdown("""
<style>
    .big-title {font-size:42px; font-weight:800; text-align:center;}
    .sub {font-size:18px; text-align:center; color:#6c6c6c;}
    .card {background:#f2f2f2; padding:15px; border-radius:10px; margin:10px 0;}
</style>
""", unsafe_allow_html=True)

st.markdown("<div class='big-title'>🔍 Resume Screener</div>", unsafe_allow_html=True)
st.markdown("<div class='sub'>AI-powered resume analyzer for job match screening</div><br>", unsafe_allow_html=True)


# -----------------------
# Job description & keywords
# -----------------------
jd = st.text_area("📝 Paste Job Description",
"""
We are hiring a Python Backend Developer with hands-on experience in:

• Python
• Django / Flask
• APIs
• SQL
• Data Structures
• Git
• Problem Solving
""")

skills_required = ["python", "django", "flask", "api", "sql", "data structures", "git", "problem solving", "machine learning"]


uploaded_file = st.file_uploader("📁 Upload Resume (PDF/TXT)", type=["pdf", "txt"])


# ----------------------------------------------------
# Simple text extraction (just for demo level)
# ----------------------------------------------------
def extract_text_from_resume(file):
    ext = file.name.split('.')[-1].lower()

    if ext == "txt":
        return file.read().decode("utf-8", errors="ignore")

    if ext == "pdf":
        text = ""

        # 1) Try PyPDF2 first
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        except:
            pass

        # 2) If still blank, try pdfplumber
        if len(text.strip()) < 10:
            try:
                import pdfplumber
                file.seek(0)
                with pdfplumber.open(file) as pdf:
                    for page in pdf.pages:
                        text += page.extract_text() or ""
            except:
                pass

        return text

    return ""



# ----------------------------------------------------
# Generate PDF report (Unicode-safe)
# ----------------------------------------------------
def make_pdf_report(name, results):
    from fpdf import FPDF

    def ascii_clean(text):
        if isinstance(text, list):
            return [ascii_clean(x) for x in text]
        if isinstance(text, dict):
            return {ascii_clean(k): ascii_clean(v) for k, v in text.items()}
        try:
            return str(text).encode("ascii", "ignore").decode("ascii")
        except:
            return str(text)

    # sanitize everything
    name = ascii_clean(name)
    clean = {
        "match_score": ascii_clean(results.get("match_score", "")),
        "weighted_score": ascii_clean(results.get("weighted_score", "")),
        "matched": ascii_clean(results.get("matched", [])),
        "missing": ascii_clean(results.get("missing", [])),
        "ats": ascii_clean(results.get("ats", {}))
    }

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", size=16)
    pdf.cell(0, 8, f"Resume Screening Report - {name}", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 6, f"Match Score: {clean['match_score']}%", ln=True)
    pdf.cell(0, 6, f"Weighted Score: {clean['weighted_score']}%", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "Matched Skills:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, ", ".join(clean["matched"]) or "None")

    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "Missing Skills:", ln=True)
    pdf.set_font("Arial", size=11)
    pdf.multi_cell(0, 6, ", ".join(clean["missing"]) or "None")

    pdf.ln(2)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 6, "ATS Checks:", ln=True)
    pdf.set_font("Arial", size=11)
    for k, v in clean["ats"].items():
        pdf.multi_cell(0, 6, f"- {k}: {v}")

    # output PDF as bytes
    pdf_bytes = pdf.output(dest="S").encode("latin-1", "replace")
    return pdf_bytes

# ----------------------------------------------------
# PROCESS BUTTON
# ----------------------------------------------------
if uploaded_file:
    if st.button("✅ Analyze Resume"):
        text = extract_text_from_resume(uploaded_file).lower()

        if not text.strip():
            st.error("Could not extract text. Upload a readable file.")
        else:
            # keyword match
            matched = [s for s in skills_required if s.lower() in text]
            missing = [s for s in skills_required if s.lower() not in text]

            match_score = int((len(matched) / len(skills_required)) * 100)
            weighted_score = match_score + (10 if "projects" in text or "experience" in text else 0)

            ats_checks = {
                "Has Contact Info": "Yes ✅" if re.search(r'\d{10}|@[a-z]', text) else "Missing ❌",
                "Contains Education Section": "Yes ✅" if "education" in text else "Not Found ❌",
                "Contains Work Experience": "Yes ✅" if "experience" in text or "intern" in text else "Not Found ❌",
                "Has Projects": "Yes ✅" if "project" in text else "Not Found ❌",
            }

            # Display Results
            st.subheader("📊 Screening Result")

            st.write("**Match Score**")
            st.progress(match_score / 100)
            st.write(f"{match_score}%")

            st.write("**Weighted Score**")
            st.progress(weighted_score / 100)
            st.write(f"{weighted_score}%")

            st.markdown("<div class='card'><b>Matched Skills:</b><br>" + ", ".join(matched) + "</div>", unsafe_allow_html=True)
            st.markdown("<div class='card'><b>Missing Skills:</b><br>" + (", ".join(missing) if missing else "None ✅") + "</div>", unsafe_allow_html=True)

            st.markdown("<div class='card'><b>ATS Checks:</b></div>", unsafe_allow_html=True)
            for k, v in ats_checks.items():
                st.write(f"- **{k}:** {v}")

            results = {
                "match_score": match_score,
                "weighted_score": weighted_score,
                "matched": matched,
                "missing": missing,
                "ats": ats_checks
            }

            pdf_bytes = make_pdf_report(uploaded_file.name, results)
            st.download_button(
                label="📥 Download PDF Report",
                data=pdf_bytes,
                file_name=f"report_{uploaded_file.name}.pdf",
                mime="application/pdf"
            )
