import csv
import io
import os
import re
import sys

import pdfrw
from reportlab.pdfgen import canvas


def get_emergency_contact(contact):
    # remove relationship
    contact = re.sub(
        r'[Ww]ife|[Mm]other|[Mm]om|[Ff]ather|[Dd]ad|[Rr]oomate|[Ss]ister|[Bb]rother|[Pp]arents|[Cc]ousin|[Cc]ell|[Pp]hone',
        '', contact)
    #  remove misc
    contact = re.sub(r',|;|\n|\.|:|\(\)', '', contact)
    # Reduce extra space
    contact = re.sub(r'\s+', ' ', contact).strip()
    if len(contact) >= 35:
        return ""
    return contact


def draw_leaders(pdf, leaders, fontSize, initX, initY, diffY):
    for leader in leaders:
        text = "{} ({})".format(leader['NAME'], leader['REGISTER STATUS'])
        pdf.setFontSize(fontSize)
        pdf.drawString(x=initX, y=initY, text=text)
        initY += diffY


def add_leaders(pdf, leaders):
    if not leaders:
        return
    if len(leaders) > 6:
        return
    fontSize, initX, initY, diffY = coordinates.get(len(leaders), two_columns)
    draw_leaders(pdf, leaders[0:3], fontSize, initX, initY, diffY)
    draw_leaders(pdf, leaders[3:], fontSize, initX + two_columns_x_diff, initY, diffY)


def get_overlay_canvas(participants, leaders, date, endDate, chapter, activity):
    data = io.BytesIO()
    pdf = canvas.Canvas(data)
    for idx, participant in enumerate(participants):
        y = y_start - y_increment * idx
        # emergency_contact = get_emergency_contact(participant['EMERGENCY CONTACT'])
        pdf.drawString(x=participant_name_x, y=y, text=participant['NAME'])
        # pdf.drawString(x=emergency_contact_x, y=y, text=emergency_contact)
    # add_leaders(pdf, leaders)
    # pdf.setFont('Helvetica-Bold', 12)
    # pdf.drawString(x=chapter_x, y=top_line_y, text=chapter or "Boston")
    # pdf.drawString(x=activity_x, y=top_line_y, text=activity or "Hiking")
    # if date:
    #     if endDate:
    #         pdf.drawString(x=date_x, y=top_line_y + 5, text=date + " -")
    #         pdf.drawString(x=date_x, y=top_line_y - 5, text=endDate)
    #     else:
    #         pdf.drawString(x=date_x, y=top_line_y, text=date)

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
    participants = sorted(participants, key=lambda participant: participant['REGISTER STATUS'], reverse=True)
    leaders = []
    for participant in participants:
        if participant['REGISTER STATUS'] == 'LEADER':
            participant['REGISTER STATUS'] = 'L'
            leaders.append(participant)
        if participant['REGISTER STATUS'] == 'CO-LEADER':
            participant['REGISTER STATUS'] = 'CL'
            leaders.append(participant)
    return leaders


def get_all_participants(csvfile):
    reader = csv.DictReader(csvfile)
    participants = list(reader)

    return participants


def get_approved_participants(participants):
    approved_participants = [
        participant for participant in participants if participant['REGISTER STATUS'] == 'APPROVED'
    ]
    approved_participants = sorted(approved_participants, key=lambda participant: participant['NAME'].lower())
    return approved_participants


def generate_pdfs_data(waiver_pdf, approved_participants, filled_waiver_base, chunk_size, leaders, date, endDate, chapter, activity):
    data = {}
    for i in range(0, len(approved_participants), chunk_size):
        chunk_index = i / chunk_size + 1
        filled_waiver_pdf = filled_waiver_base + str(chunk_index) + ".pdf"
        participants = approved_participants[i:i + chunk_size]
        canvas_data = get_overlay_canvas(participants, leaders, date, endDate, chapter, activity)
        form = merge(canvas_data, template_path=waiver_pdf)
        data[filled_waiver_pdf] = form.read()
    return data


def main():
    waiver_pdf = sys.argv[1]
    csv_file = sys.argv[2]
    date = sys.argv[3] if len(sys.argv) >= 4 else None
    endDate = sys.argv[4] if len(sys.argv) >= 5 else None
    chapter = sys.argv[4] if len(sys.argv) >= 6 else None
    activity = sys.argv[4] if len(sys.argv) >= 7 else None
    filled_waiver_base = os.path.splitext(waiver_pdf)[0] + '_filled_'
    participants = get_all_participants(open(csv_file))
    leaders = get_leaders(participants)
    participants = get_approved_participants(participants)
    file_contents = generate_pdfs_data(waiver_pdf, participants, filled_waiver_base, init_chunk_size, leaders, date,
                                       endDate, chapter, activity)
    for filename, content in file_contents.items():
        save(filename, content)


participant_name_x = 160
emergency_contact_x = 400
y_start = 568
y_increment = 60
init_chunk_size = 9

top_line_y = 709
leader_name_x = 170
chapter_x = 320
activity_x = 430
date_x = 50
coordinates = {1: [12, 170, 709, 0], 2: [10, 170, 715, -10], 3: [9, 170, 720, -8]}
two_columns = [6, 165, 720, -8]
two_columns_x_diff = 50

if __name__ == "__main__":
    main()
