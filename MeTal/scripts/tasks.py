#!/usr/bin/env python3

# add cmdline options to suppress emailed reports

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
        Page.blog, Page.publication_date.desc())

total_pages = scheduled_pages.count()

print ('{} pages scheduled'.format(total_pages))

if total_pages > 0:

    from core.cms import (queue_page_actions, queue_index_actions, process_queue,
        build_pages_fileinfos, build_archives_fileinfos, push_to_queue, job_type)
    from core.models import db, queue_jobs_waiting
    from core.log import logger

    scheduled_page_report = []
    blogs = set()

    for n in scheduled_pages:

        try:
            with db.atomic() as txn:
                scheduled_page_report.append('{} -- on {}'.format(n.title, n.publication_date))
                n.status = page_status.published
                build_pages_fileinfos((n,))
                build_archives_fileinfos((n,))
                queue_page_actions(n)
                queue_index_actions(n.blog)
                blogs.add(n.blog)
                n.save(n.user, no_revision=True)

        except Exception as e:
            problem = 'Problem with page {}: {}'.format(n.title, e)
            print (problem)
            scheduled_page_report.append(problem)

    # TODO: where to put txn in this area?

    # TODO: push control job should be its own function
    # TODO: elsewhere, use queue_jobs_waiting function instead of
    # the ad hoc stuff

    for n in blogs:
        waiting = queue_jobs_waiting(blog=n)
        push_to_queue(blog=n,
                site=n.site,
                job_type=job_type.control,
                is_control=True,
                data_integer=waiting
                )
        print ("Processing {} jobs for blog '{}'.".format(
            waiting, n.name))
        while 1:
            remaining = process_queue(n)
            print ("{} jobs remaining.".format(remaining))
            if remaining == 0:
                break

    message_text = '''
This is a scheduled-tasks report from the installation of {}.

Pages published:

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

    logger.info("Scheduled job run, processed {} pages.".format(total_pages))

else:

    print ('No scheduled tasks found to run.')

print ('Scheduled tasks script completed.')
