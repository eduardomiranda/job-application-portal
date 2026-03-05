import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def enviar_plain_text_email(subject, body, sender, recipients, password):
	msg = MIMEText(body)
	msg['Subject'] = subject
	msg['From'] = sender
	msg['To'] = ', '.join(recipients)

	with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
		smtp_server.login(sender, password)
		smtp_server.sendmail(sender, recipients, msg.as_string())



def enviar_html_email(subject, text_body_message, html_body_message, sender, password, recipients, bcc_recipients=None, file_path_attach=None):

    if bcc_recipients is None:
        bcc_recipients = []

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    # NÃO colocar Bcc aqui se quiser manter totalmente oculto

    part1 = MIMEText(text_body_message, 'plain')
    part2 = MIMEText(html_body_message, 'html')

    msg.attach(part1)
    msg.attach(part2)

    if file_path_attach:
        part = MIMEBase('application', "octet-stream")
        with open(file_path_attach, "rb") as f:
            part.set_payload(f.read())

        encoders.encode_base64(part)
        basename = os.path.basename(file_path_attach)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{basename}"'
        )
        msg.attach(part)

    # Para enviar e-mails com BCC (Cópia Oculta) usando server.sendmail no Python, inclua os destinatários ocultos na lista de 
    # destinatários (to_addrs) do método, mas não os adicione ao cabeçalho "Bcc" da mensagem MIME, pois isso os tornaria visíveis. 
    all_recipients = recipients + bcc_recipients 

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.ehlo()
        smtp_server.login(sender, password)
        smtp_server.sendmail(sender, all_recipients, msg.as_string())




# Example usage
if __name__ == "__main__":

	subject = 'Teste'


	text_body_message = '' 

	html_body_message = """
		<html>
			<body>
				<h1>Teste</h1>
				<p>teste</p>
			</body>
		</html>
	"""


	enviar_html_email(subject, text_body_message, html_body_message, sender, password, ['eduardo.dpm@gmail.com'], '/home/eduardo/Pictures/Impacta1.jpg')
	# enviar_html_email(subject, text_body_message, html_body_message, sender, password, ['eduardo.dpm@gmail.com'], None)