import csv
import io
import re
import sys
import os
import pdfrw
from reportlab.pdfgen import canvas
from datetime import datetime


def get_emergency_contact(contact):
    contact = re.sub(',|;|[Ww]ife|\n|[Mm]other|[Mm]om|[Rr]oomate|\.|:|[Ss]ister|[Pp]arents', '', contact)
    # contact = re.sub('-|\(|\)|,|;|wife|\n|Mother|Roomate|\.|:|sister|parents', '', contact)
    if len(contact) >= 35:
        return ""
    return contact


def get_overlay_canvas(participants, leaders):
    data = io.BytesIO()
    pdf = canvas.Canvas(data)
    for idx, participant in enumerate(participants):
        y = y_start - y_increment * idx
        emergency_contact = get_emergency_contact(participant['EMERGENCY CONTACT'])
        pdf.drawString(x=participant_name_x, y=y, text=participant['NAME'])
        pdf.drawString(x=emergency_contact_x, y=y, text=emergency_contact)
    if leaders:
        pdf.drawString(x=leader_name_x, y=top_line_y, text=leaders[0]['NAME'])
    pdf.drawString(x=chapter_x, y=top_line_y, text="Boston")
    pdf.drawString(x=activity_x, y=top_line_y, text="Hiking")

    pdf.save()
    data.seek(0)
    return data


def merge(overlay_canvas, template_path):
    template_pdf = pdfrw.PdfReader(template_path)
    overlay_pdf = pdfrw.PdfReader(overlay_canvas)
    for page, data in zip(template_pdf.pages, overlay_pdf.pages):
        overlay = pdfrw.PageMerge().add(data)[0]
        pdfrw.PageMerge(page).add(overlay).render()
    form = io.BytesIO()
    pdfrw.PdfWriter().write(form, template_pdf)
    form.seek(0)
    return form


def save(filename, content):
    with open(filename, 'wb') as f:
        f.write(content)


def get_leaders(participants):

    leaders = [participant for participant in participants if participant['REGISTER STATUS'] in ['LEADER']]

    if leaders:
        leaders = sorted(leaders, key=lambda participant: datetime.strptime(participant['REGISTER DATE'], "%Y-%m-%d %H:%M:%S"))
    return leaders


def get_all_participants(csvfile):
    reader = csv.DictReader(csvfile)
    participants = list(reader)

    return participants


def get_approved_participants(participants):
    approved_participants = [participant for participant in participants if participant['REGISTER STATUS'] == 'APPROVED']
    approved_participants = sorted(approved_participants, key=lambda participant: participant['NAME'].lower())
    return approved_participants


def generate_pdfs_data(waiver_pdf, approved_participants, filled_waiver_base, chunk_size, leaders):
    data = {}
    for i in range(0, len(approved_participants), chunk_size):
        chunk_index = i / chunk_size + 1
        filled_waiver_pdf = filled_waiver_base + str(chunk_index) + ".pdf"
        participants = approved_participants[i:i + chunk_size]
        canvas_data = get_overlay_canvas(participants, leaders)
        form = merge(canvas_data, template_path=waiver_pdf)
        data[filled_waiver_pdf] = form.read()
    return data


def main():
    waiver_pdf = sys.argv[1]
    csv_file = sys.argv[2]
    filled_waiver_base = os.path.splitext(waiver_pdf)[0] + '_filled_'
    participants = get_all_participants(open(csv_file))
    leaders = get_leaders(participants)
    participants = get_approved_participants(participants)
    file_contents = generate_pdfs_data(waiver_pdf, participants, filled_waiver_base, chunk_size, leaders)
    for filename, content in file_contents.items():
        save(filename, content)


participant_name_x = 65
emergency_contact_x = 400
y_start = 215
y_increment = 17
chunk_size = 10

top_line_y = 709
leader_name_x = 170
chapter_x = 320
activity_x = 430

if __name__ == "__main__":
    main()
