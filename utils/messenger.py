import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders


class Messenger:
    """
    :param str send_from: email address "from"
    :param str subject: email subject
    :param str server: server of the mailing system
    :param int port:
    :param bool use_tls:
    """

    def __init__(self, send_from, subject, send_from_name,
                 server='smtp.gmail.com', port=587,
                 use_tls=True):
        self.send_from = send_from
        self.send_from_name = send_from_name
        self.subject = subject
        self.password = input('Enter the app password')
        self.server = server
        self.port = port
        self.use_tls = use_tls

    def __call__(self, send_to, message, files):
        """
        Sends an email with an attachment.

        :param str or list[str] send_to: email address of the recipient
        :param str message: content of the email
        :param str or list[str] files: list of attachments
        """
        msg = MIMEMultipart()
        msg['From'] = self.send_from_name
        if isinstance(send_to, str):
            send_to = [send_to]

        if isinstance(files, str):
            files = [files]
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


if __name__ == '__main__':
    messenger = Messenger(send_from='nshan.potikyan@gmail.com',
                          subject='Test2',
                          send_from_name='Nshan Potikyan')
    messenger(send_to='nshan.potikyan@gmail.com',
              message='Some text',
              files=['../sample_homeworks/with_assertions/HW6-AramAramyan.ipynb'])
