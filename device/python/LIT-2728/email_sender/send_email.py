import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os.path
import argparse


def send_email(email_sender,
               email_sender_password,
               email_recipient,
               email_subject,
               email_message,
               attachment_location=None):
    """
    Send a message with report
    """

    if attachment_location is None:
        attachment_location = []

    msg = MIMEMultipart()
    msg['From'] = email_sender
    msg['To'] = email_recipient
    msg['Subject'] = email_subject

    msg.attach(MIMEText(email_message, 'plain'))

    if attachment_location:

        for attachment in attachment_location:
            filename = os.path.basename(attachment)
            attachment = open(attachment, "rb")
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            "attachment; filename= %s" % filename)
            msg.attach(part)

    # try:
        # Log in to server using secure context and send email
    context = ssl.create_default_context()
    server = smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context)
    server.ehlo()
    server.login(email_sender, email_sender_password)
    text = msg.as_string()
    server.sendmail(email_sender, email_recipient, text)
    print('email sent')
    server.quit()
    # except:
    #     print("SMPT server connection error")
    #     return False
    return True


def read_file(filename):
    """
    Return two lists column1, column2
    read from a file specified by filename.
    """

    column1 = []
    column2 = []

    with open(filename, mode='r', encoding='utf-8') as contacts_file:
        for a_contact in contacts_file:
            column1.append(a_contact.split()[0])
            column2.append(a_contact.split()[1])

    return column1, column2


def get_credentials(filename):
    """
    Return two lists names, emails containing names and email addresses
    read from a file specified by filename.
    """
    return read_file(filename)


def get_contacts(filename):
    """
    Return two lists names, emails containing names and email addresses
    read from a file specified by filename.
    """
    return read_file(filename)


def send_email_with_attachments(credentials, contacts, attachments):
    """
    Prepare data, parse credentials and contacts
    """

    subject = "Report from SumoLogic"

    sender_email, sender_password = get_credentials(credentials)
    names, emails = get_contacts(contacts)  # read contacts
    print(sender_email, sender_password)
    print(names, emails)

    for name, email, in zip(names, emails):
        body = "Dear {} \n\nThis is an email with attached report about pumps with \"BAM I/O not ready\" " \
               "problem.\n\nBR PythonScript".format(name)
        send_email(sender_email[0], sender_password[0], email,
                   subject, body, attachments)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-cr', '--credentials', help='Credentials of sender')
    parser.add_argument('-ct', '--contacts', help='Receivers of email')
    parser.add_argument('-at', '--attachment', help='Attachment to email')
    arguments = parser.parse_args()

    credentials = arguments.credentials
    contacts = arguments.contacts
    attachment = list(arguments.attachment.split(" "))
    send_email_with_attachments(credentials, contacts, attachment)


if __name__ == '__main__':
    main()
