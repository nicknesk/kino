import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_email(recipient_mail, random_string):
   # Credentials to gmail
    me = "kinomonster.robot@gmail.com"
    password = '2718281828'

    # create the link to verify
    link = 'https://nesk-kino.herokuapp.com/verify?q=' + random_string
   # link = 'http://localhost:5000/verify?q=' + random_string

  # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "E-mail confirmation"
    msg['From'] = me
    msg['To'] = recipient_mail

    # Create the body of the message (a plain-text and an HTML version).
    html = """\
    <html>
      <head></head>
      <body>
        <p><h2>Hi! This is the letter from KinoMonster</h2><br>
           <strong>Don't answer on it</strong><br><br>
            <a href="{}">To finish the registration on the site or profile updates follow this link</a>
        </p>
      </body>
    </html>
    """.format(link)

    # Record the MIME types of both parts - text/plain and text/html.
    part = MIMEText(html, 'html')

    # Attach part into message container.
    msg.attach(part)

    # Send the message via gmail SSL SMTP server.
    try:
        server_ssl = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server_ssl.ehlo()  # optional, called by login()
        server_ssl.login(me, password)
        server_ssl.sendmail(me, recipient_mail, msg.as_string())
        server_ssl.quit()
        server_ssl.close()
        return True
    except Exception as e:
        print("failed to send mail", e)
        return False


