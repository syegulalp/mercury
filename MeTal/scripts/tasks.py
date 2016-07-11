#!/usr/bin/env python3

# TODO: add cmdline options to suppress emailed reports

if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        import settings

product_id = '{}, running in {}'.format(settings.PRODUCT_NAME, settings.APPLICATION_PATH)

print ('{}\nScheduled tasks script.'.format(product_id))

import smtplib, datetime
from email.mime.text import MIMEText

from core.auth import get_users_with_permission, role

admin_users = get_users_with_permission(role.SYS_ADMIN)

print ('Admins: {}'.format(admin_users.count()))

print ('Looking for scheduled tasks...')

from core.models import Page, page_status

# TODO: we may want to move this into some systemwide schema?

scheduled_pages = Page.select().where(
    Page.status == page_status.scheduled,
    Page.publication_date <= datetime.datetime.utcnow()).order_by(
        Page.publication_date.desc())

total_pages = scheduled_pages.count()

print ('{} pages scheduled'.format(total_pages))

if total_pages > 0:

    from core.cms import (queue_page_actions, queue_index_actions, process_queue,
        build_pages_fileinfos, build_archives_fileinfos, start_queue, Blog)
    from core.models import db, Queue
    from core.log import logger

    scheduled_page_report = []
    blogs = set()

    # TODO rework this to use proper loop since many functions take list not single page
    for n in scheduled_pages:

        try:
            with db.atomic() as txn:
                scheduled_page_report.append('{} -- on {}'.format(n.title, n.publication_date))
                n.status = page_status.published
                build_pages_fileinfos((n,))
                build_archives_fileinfos((n,))
                queue_page_actions((n,))
                queue_index_actions(n.blog)
                blogs.add(n.blog.id)
                n.save(n.user, no_revision=True)

        except Exception as e:
            problem = 'Problem with page {}: {}'.format(n.title, e)
            print (problem)
            scheduled_page_report.append(problem)

    for n in blogs:
        blog = Blog.load(n)
        # waiting = queue_jobs_waiting(blog=blog)
        waiting = Queue.job_counts(blog=blog)
        start_queue(blog)

        print ("Processing {} jobs for blog '{}'.".format(
            waiting, blog.name))
        while 1:
            remaining = process_queue(blog)
            print ("{} jobs remaining.".format(remaining))
            if remaining == 0:
                break

    message_text = '''
This is a scheduled-tasks report from the installation of {}.

Pages published:

{}
'''.format(product_id,
    scheduled_page_report)

    admins = []

    for n in admin_users:
        msg = MIMEText(message_text)
        msg['Subject'] = 'Scheduled activity report for {}'.format(product_id)
        msg['From'] = n.email
        msg['To'] = n.email
        admins.append(n.email)
        s = smtplib.SMTP('localhost')
        s.send_message(msg)
        s.quit()

    print ('Reports emailed to {}.'.format(','.join(admins)))

    logger.info("Scheduled job run, processed {} pages.".format(total_pages))

else:

    print ('No scheduled tasks found to run.')

print ('Scheduled tasks script completed.')
