import smtplib
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "YOUR EMAIL "
password = "YOUR EMAIL PASSWORD"


def sending(msg, name, receiver_email):
    subject = "Reminder!"
    message = f"Hello {name},\nThe product is within your price range.\nYou can buy the product from: {msg}."
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(sender_email, password)
    email_headers = f"Subject: {subject}\n"

    email_text = f"{email_headers}\n\n{message}"
    server.sendmail(sender_email, receiver_email, email_text)

    server.quit()


