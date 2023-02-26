import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders


class Messenger:
    def __init__(self, send_from, subject,
                 server='smtp.gmail.com', port=587,
                 use_tls=True):
        self.send_from = send_from
        self.subject = subject
        self.password = input('Enter the app password')
        self.server = server
        self.port = port
        self.use_tls = use_tls

    def __call__(self, send_to, message, files):
        msg = MIMEMultipart()
        msg['From'] = self.send_from
        msg['To'] = COMMASPACE.join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = self.subject

        msg.attach(MIMEText(message))

        for path in files:
            part = MIMEBase('application', "octet-stream")
            with open(path, 'rb') as file:
                part.set_payload(file.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition',
                            'attachment; filename={}'.format(Path(path).name))
            msg.attach(part)

        smtp = smtplib.SMTP(self.server, self.port)

        if self.use_tls:
            smtp.starttls()
        smtp.login(self.send_from, self.password)

        smtp.sendmail(self.send_from, send_to, msg.as_string())
        smtp.quit()


# def send_mail(send_from, send_to, subject, message, files=[],
#               server='smtp.gmail.com', port=587, username='',
#               use_tls=True):
#     """Compose and send email with provided info and attachments.
#
#     Args:
#         send_from (str): from name
#         send_to (list[str]): to name(s)
#         subject (str): message title
#         message (str): message body
#         files (list[str]): list of file paths to be attached to email
#         server (str): mail server host name
#         port (int): port number
#         username (str): server auth username
#         use_tls (bool): use TLS mode
#     """
#     msg = MIMEMultipart()
#     msg['From'] = send_from
#     msg['To'] = COMMASPACE.join(send_to)
#     msg['Date'] = formatdate(localtime=True)
#     msg['Subject'] = subject
#
#     msg.attach(MIMEText(message))
#
#     for path in files:
#         part = MIMEBase('application', "octet-stream")
#         with open(path, 'rb') as file:
#             part.set_payload(file.read())
#         encoders.encode_base64(part)
#         part.add_header('Content-Disposition',
#                         'attachment; filename={}'.format(Path(path).name))
#         msg.attach(part)
#
#     smtp = smtplib.SMTP(server, port)
#
#     if use_tls:
#         smtp.starttls()
#     password = input('Enter the app password')
#     smtp.login(username, password)
#     smtp.sendmail(send_from, send_to, msg.as_string())
#     smtp.quit()


if __name__ == '__main__':
    send_mail(send_from='nshan.potikyan@gmail.com',
              send_to=['nshan.potikyan@gmail.com', 'n.potikyan@ysu.am'],
              subject='Test',
              message='Կից կարող եք գտնել ձեր աշխատանքը։',
              files=['../sample_homeworks/new/HW1_Numpy_AramAramyan.ipynb'],
              username='nshan.potikyan@gmail.com')
