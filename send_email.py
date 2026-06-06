"""
send_email.py
-------------
Entry point. Ties everything together:
  1. Calls get_all_events() from scrape_events.py
  2. Calls build_html()     from format_email.py
  3. Sends the report as an HTML email via Gmail SMTP

Required environment variables (set as GitHub Secrets for automated runs):
  GMAIL_SENDER        Gmail address used to send (e.g. espi.code@gmail.com)
  GMAIL_RECIPIENT     Destination address(es), comma-separated for multiple
  GMAIL_APP_PASSWORD  16-char Gmail App Password — spaces are stripped automatically
                      Create one at: myaccount.google.com → Security → App Passwords
                      (2-Step Verification must be enabled first)

Run locally:
  export GMAIL_SENDER="sender@gmail.com"
  export GMAIL_RECIPIENT="thierry@example.com,audrey@example.com"
  export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"
  python3 send_email.py
"""

import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from scrape_events import get_all_events, TODAY, FR_MONTHS
from format_email import build_html


def get_credentials():
    missing = [v for v in ('GMAIL_SENDER', 'GMAIL_RECIPIENT', 'GMAIL_APP_PASSWORD')
               if not os.environ.get(v)]
    if missing:
        print('Erreur : variables d\'environnement manquantes :')
        for v in missing:
            print(f'  {v}')
        print('\nDéfinir avant de lancer :')
        print('  export GMAIL_SENDER="sender@gmail.com"')
        print('  export GMAIL_RECIPIENT="recipient@example.com"')
        print('  export GMAIL_APP_PASSWORD="xxxx xxxx xxxx xxxx"')
        sys.exit(1)

    sender    = os.environ['GMAIL_SENDER']
    recipient = [r.strip() for r in os.environ['GMAIL_RECIPIENT'].split(',')]
    password  = os.environ['GMAIL_APP_PASSWORD'].replace(' ', '')
    return sender, recipient, password


def build_message(sender, recipient, html):
    month = FR_MONTHS[TODAY.month].capitalize()
    subject = f"🎮 Pixel Bento — Radar Tokyo · {TODAY.day} {month} {TODAY.year}"

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = sender
    msg['To']      = ', '.join(recipient)

    plain = (
        f"Pixel Bento — Radar Tokyo · {TODAY.day} {FR_MONTHS[TODAY.month]} {TODAY.year}\n\n"
        "Ce rapport est mieux consulté dans un client mail compatible HTML.\n"
        "Ouvrez report.html dans un navigateur si seul ce texte s'affiche."
    )
    # Plain text first, HTML last — email clients render the last format they support
    msg.attach(MIMEText(plain, 'plain'))
    msg.attach(MIMEText(html,  'html'))
    return msg


def send(msg, sender, recipient, password):
    print('Connexion à smtp.gmail.com:587…')
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
    print(f'✓ Email envoyé à : {", ".join(recipient)}')


if __name__ == '__main__':
    print('Vérification des identifiants…')
    sender, recipient, password = get_credentials()
    print(f'  Expéditeur  : {sender}')
    print(f'  Destinataires : {", ".join(recipient)}')

    print('\nRécupération des événements…')
    main_events, kuji_events = get_all_events()

    print('\nConstruction de l\'email…')
    html = build_html(main_events, kuji_events)

    with open('report.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('Aperçu local sauvegardé : report.html')

    msg = build_message(sender, recipient, html)
    send(msg, sender, recipient, password)
