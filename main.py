import io
import os
import qrcode
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from pymongo import MongoClient
from twilio.rest import Client


# MongoDB connection
client = MongoClient("mongodb+srv://sahapriyanshu88:ezyCplrNUtcKPuiH@cluster0.4qyhzir.mongodb.net/")
db = client.neuraldb
people = db.people

# Twilio credentials
TWILIO_ACCOUNT_SID = 'ACa2e66151cc11afa4f6dec066095cc942'
TWILIO_AUTH_TOKEN = '3ea48330230b5e6cde3bc05b54ec1257'
TWILIO_PHONE_NUMBER = '+13345184638'

# Set up Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Function to generate QR code
def generate_qr_code(ticket_id, qr_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(ticket_id)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img.save(qr_path)

# Define the function to overlay data onto the template
def generate_ticket(template_path, output_path, name, mobile, amount, payment_mode, transaction_id, booking_date_time, ticket_id):
    try:
        # Create a PDF with reportlab to overlay the data
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # Add text to specific positions in the PDF
        can.setFont("Helvetica", 12)
        can.drawString(100, 700, f"Name: {name}")
        can.drawString(100, 680, f"Mobile: {mobile}")
        can.drawString(100, 660, f"Amount: {amount}")
        can.drawString(100, 640, f"Payment Mode: {payment_mode}")
        can.drawString(100, 620, f"Transaction ID: {transaction_id}")
        can.drawString(100, 600, f"Booking Date & Time: {booking_date_time}")

        # Generate and add QR code
        qr_path = os.path.join(output_dir, f"{ticket_id}_qr.png")
        generate_qr_code(ticket_id, qr_path)
        can.drawImage(qr_path, 400, 600, width=100, height=100)

        # Save the overlay
        can.save()

        # Move to the beginning of the StringIO buffer
        packet.seek(0)

        # Read the existing PDF template
        template_pdf = PdfReader(r"C:\Users\SWAPANIL\OneDrive\Documents\Fast Prabesh\Fastticket.pdf")  # Use raw string
        overlay_pdf = PdfReader(packet)

        # Create a PdfWriter object to combine the two PDFs
        output_pdf = PdfWriter()

        # Get the first page of the template
        template_page = template_pdf.pages[0]

        # Merge the overlay onto the template page
        template_page.merge_page(overlay_pdf.pages[0])

        # Add the merged page to the output
        output_pdf.add_page(template_page)

        # Write the output to a file
        with open(output_path, "wb") as outputStream:
            output_pdf.write(outputStream)

        print(f"Ticket generated: {output_path}")

        # Clean up QR code image file
        os.remove(qr_path)

    except Exception as e:
        print(f"An error occurred: {e}")

# Function to send SMS with the generated ticket
# Function to send SMS with the generated ticket and individual's data
def send_sms_with_ticket(mobile_number, pdf_path, name, amount, payment_mode, transaction_id, booking_date_time):
    try:
        # Convert the mobile number to a string
        mobile_number = str(mobile_number)

        # Validate and format mobile number
        if not mobile_number.startswith('+'):
            mobile_number = '+91' + mobile_number  # Assuming Indian numbers, replace with correct country code if different

        # Construct the message body with the individual's data and the link to the ticket
        message_body = (
            f"Dear {name},\n"
            f"Your ticket has been generated.\n"
            f"Amount: {amount}\n"
            f"Payment Mode: {payment_mode}\n"
            f"Transaction ID: {transaction_id}\n"
            f"Booking Date & Time: {booking_date_time}\n"
            f"Download your ticket from the following link:\n{pdf_path}"
        )

        # Send the SMS
        message = twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=mobile_number
        )
        print(f"SMS sent to {mobile_number}")

    except Exception as e:
        print(f"Failed to send SMS to {mobile_number}: {e}")


# Fetch data and generate tickets
def fetch_data_and_generate_tickets():
    global output_dir
    output_dir = r"C:\Users\SWAPANIL\OneDrive\Documents\Fast Prabesh\Generated Tickets"
    os.makedirs(output_dir, exist_ok=True)
    try:
        # Fetch data from the collection
        data = people.find()

        # Iterate over each record and generate tickets
        for record in data:
            name = record.get('name')
            mobile = record.get('Mobile')
            amount = record.get('Amount')
            payment_mode = record.get('Payment_Mode')
            transaction_id = record.get('Transaction_id')
            booking_date_time = record.get('Booking_Date_Time')
            ticket_id = str(record.get('_id'))  # Unique ID for each ticket

            if name and mobile and amount and payment_mode and transaction_id and booking_date_time:
                # Generate a unique filename for each ticket
                safe_name = name.replace(' ', '').replace('/', '')  # Replace spaces and slashes in name for safety
                output_filename = os.path.join(output_dir, f"{safe_name}_{ticket_id}_Ticket.pdf")
                generate_ticket(r"C:\Users\SWAPANIL\OneDrive\Documents\Fast Prabesh\Fastticket.pdf", output_filename, name, mobile, amount, payment_mode, transaction_id, booking_date_time, ticket_id)

                # After generating the ticket, send an SMS with the link and data
                send_sms_with_ticket(mobile, output_filename, name, amount, payment_mode, transaction_id, booking_date_time)

    except Exception as e:
        print(f"An error occurred while fetching data or generating tickets: {e}")

# Call the function to generate tickets
fetch_data_and_generate_tickets()