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
Paste the job description
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
from fpdf import FPDF

def make_pdf_report(file_name, results):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ✅ Use a built-in core font that supports more characters
    pdf.set_font("Helvetica", size=12)

    # Title
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 10, "Resume Screening Report", ln=True)
    pdf.ln(5)

    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, f"File: {file_name}")
    pdf.ln(5)

    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 10, "Results:", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", size=12)

    # ✅ SAFE MULTI-CELL (avoids crash)
    for k, v in results.items():
        text = f"- {k}: {v}"
        try:
            pdf.multi_cell(0, 6, text)
        except:
            # Fallback if a line is too long or has unicode
            safe_text = text.encode("ascii", "ignore").decode()
            pdf.multi_cell(0, 6, safe_text)

    # ✅ Return binary PDF bytes safely
    pdf_bytes = pdf.output(dest="S").encode("latin-1", "ignore")
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

