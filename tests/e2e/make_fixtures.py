"""Create sample PDF/DOCX files used by browser_test.py (writes to /tmp/fx)."""
import os

from docx import Document
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

os.makedirs("/tmp/fx", exist_ok=True)
st = getSampleStyleSheet()
SimpleDocTemplate("/tmp/fx/article.pdf", pagesize=A4, leftMargin=180, rightMargin=180).build([
    Paragraph("Protected bike lanes cut injuries by 28 percent", st["Title"]),
    Paragraph("Cities that added protected bike lanes saw cyclist injuries fall by 28 percent over three years, according to a study released this week. The research followed twelve mid-sized cities that built physical barriers between bikes and traffic, and compared them with similar cities that made no changes.", st["BodyText"]),
    Spacer(1, 8),
    Paragraph("The largest gains came near schools and transit stops, where cyclist and pedestrian traffic is heaviest. Businesses along the new lanes reported steady or higher sales, easing a common worry that removing parking would hurt trade. The authors caution that painted lines alone showed little benefit.", st["BodyText"]),
])
d = Document()
for line in ["Ngozi Adeyemi", "Senior Data Engineer", "2018 - Present  Lead Data Engineer, Finlytics",
             "- Reduced pipeline cost 35% by moving jobs to AWS", "- Led a team of 5 engineers",
             "2014 - 2018  Analyst, Kora", "- Built dashboards used by 200 staff", "B.Sc Statistics, 2014",
             "Skills: Python, SQL, AWS, Docker, leadership, teamwork"]:
    d.add_paragraph(line)
d.save("/tmp/fx/cv.docx")
open("/tmp/fx/bad.exe", "wb").write(b"x" * 100)
print("fixtures written to /tmp/fx")
