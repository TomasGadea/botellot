from time import time
from pdfparsing import fillPDFData
import json 

config = json.load(open("./config.json"))

RAW_FILES_PATH = config["RAW_FILES_PATH"]
TICKETS_PATH = config["TICKETS_PATH"]

def downloadFile(update, context):
    timestamp = round(time()*1e6)
    isPDF = update.message.document.mime_type == "application/pdf"

    with open(RAW_FILES_PATH + f"{timestamp}.pdf", 'wb') as f:
        if isPDF:
            context.bot.get_file(update.message.document).download(out=f)
    
    return isPDF, timestamp

def getTicketsData(filename):
    import os
    import qrtools
    from pdf2image import convert_from_path

    qr = qrtools.QR()
    fullpath = RAW_FILES_PATH + f"{filename}.pdf"
    tickets = convert_from_path(fullpath)

    # Parse data from the PDF
    tickets_data = []
    fillPDFData(tickets_data, fullpath)

    for i, ticket in enumerate(tickets):
        # Step 1: Save with temporal name
        prepath = TICKETS_PATH + f"{filename}_{str(i)}.jpg"
        ticket.save(prepath, 'JPEG')
        
        # Step 2: Decode QR and get its data
        qr.decode(filename=prepath)
        tickets_data[i]["qr"] = qr.data

        # Step 3: Change name to QR data
        if tickets_data[i]['clubname'] != 'Undefined':
            postpath = TICKETS_PATH + f"{tickets_data[i]['qr']}.jpg"
            os.rename(prepath, postpath)
        else:
            return {}

    return tickets_data

def handlePDF(update, context):
    # Step 1: Download file
    correct, filename = downloadFile(update, context)
    if not correct:
        print("Not a PDF")
        return

    # Step 2: Get data from PDF
    tickets_data = getTicketsData(filename)
    if tickets_data == {}:
        print("No ticket data found")
        return

    # Step 3: Reply with data
    from messaging import compose_ticket_msg, publish_button
    for ticket_data in tickets_data:
        msg = compose_ticket_msg(ticket_data)
        button = publish_button("Publicar")
        update.message.reply_text(msg, reply_markup=button)