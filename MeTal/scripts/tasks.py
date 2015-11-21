#!/usr/bin/env python3

# add cmdline options to suppress emailed reports

if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        import settings

product_id = '{}, running in {}'.format(settings.PRODUCT_NAME, settings.APPLICATION_PATH)

print ('{} - Scheduled tasks script.'.format(product_id))

import smtplib, datetime
from email.mime.text import MIMEText

from core.auth import get_users_with_permission, role

admin_users = get_users_with_permission(role.SYS_ADMIN)

print ('Looking for scheduled tasks...')

from core.models import Page, page_status

scheduled_pages = Page.select().where(
    Page.publication_date <= datetime.datetime.utcnow(),
    Page.status == page_status.scheduled)

print ('{} pages scheduled'.format(scheduled_pages.count()))

scheduled_page_report = []
for n in scheduled_pages:
    scheduled_page_report.append('{} -- on {}'.format(n.title, n.publication_date))
    # push pages in question to queue
    # activate queue runner for all jobs, no timeout by default
    # do we reset publishing mode for page here, or in actual queue?

if scheduled_pages.count() > 0:

    message_text = '''
This is a report for the installation of {}.

Pages to be published:

{}
'''.format(product_id,
    scheduled_page_report)

    for n in admin_users:
        msg = MIMEText(message_text)
        msg['Subject'] = 'Scheduled activity report for {}'.format(product_id)
        msg['From'] = n.email
        msg['To'] = n.email
        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()

    print ('Reports emailed.')

    # write to event log, too

else:

    print ('No scheduled tasks found to run.')

print ('Scheduled tasks script completed.')
