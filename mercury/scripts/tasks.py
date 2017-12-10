#!/usr/bin/env python3

# TODO: add cmdline options to suppress emailed reports

if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        import settings

    from core.models.transaction import transaction
    from core.cms.queue import process_queue

    @transaction
    def run(n):
        return process_queue(n)

    import datetime

    product_id = '{}, running in {}'.format(settings.PRODUCT_NAME, settings.APPLICATION_PATH)

    print ('{}\nScheduled tasks script.'.format(product_id))

    print ('Looking for scheduled tasks...')

    from core.models import Page, page_status, Queue

    blogs_to_check = {}
    scheduled_page_report = []

    scheduled_pages = Page.select().where(
        Page.status == page_status.scheduled,
        Page.publication_date <= datetime.datetime.utcnow()).order_by(
            Page.publication_date.desc())

    total_pages = scheduled_pages.count()

    print ('{} pages scheduled'.format(total_pages))

    if total_pages > 0:
        for p in scheduled_pages.select(Page.blog).distinct():
            b = p.blog
            blogs_to_check[b.id] = b

    queue_count = Queue.select(Queue.blog).distinct()

    if queue_count.count() > 0:
        for n in queue_count:
            b = n.blog
            print ('Blog {} has existing queue items'.format(b.id))
            blogs_to_check[b.id] = b

    if blogs_to_check:
        print ("Starting run.")
        from core.cms.queue import (queue_page_actions, queue_index_actions,
            queue_ssi_actions)
        from core.models import db
        from core.log import logger
        from time import sleep

        for b in blogs_to_check:
            try:
                n = blogs_to_check[b]
                skip = None

                if Queue.is_insert_active(n):
                    skip = 'Insert in progress for blog {}. Skipping this run.'.format(n.id)
                elif Queue.control_jobs(n).count() > 0:
                    skip = 'Job already running for blog {}. Skipping this run.'.format(n.id)
                if skip:
                    print (skip)
                    scheduled_page_report.append(skip)
                    continue

                for p in scheduled_pages.where(Page.blog == b).distinct():
                    scheduled_page_report.append('Scheduled pages:')
                    try:
                        with db.atomic() as txn:
                            scheduled_page_report.append('{} -- on {}'.format(p.title, p.publication_date))
                            p.status = page_status.published
                            p.save(p.user, no_revision=True)
                            queue_page_actions((p,))
                            blogs_to_check[p.blog.id] = p.blog

                    except Exception as e:
                        problem = 'Problem with page {}: {}'.format(n.title, e)
                        print (problem)
                        scheduled_page_report.append(problem)

                queue_index_actions(n)
                queue_ssi_actions(n)

                waiting = Queue.job_counts(blog=n)
                waiting_report = '{} jobs waiting for blog {}'.format(waiting, n.id)
                print (waiting_report)
                scheduled_page_report.append(waiting_report)

                Queue.start(n)

                print ("Processing {} jobs for blog '{}'.".format(
                    waiting, n.name))

                from time import clock
                begin = clock()

                passes = 1

                while 1:
                    sleep(.1)
                    remaining = run(n)
                    print ("Pass {}: {} jobs remaining.".format(passes, remaining))
                    if remaining == 0:
                        break
                    passes += 1

                end = clock()

                total_time = end - begin

                time_elapsed = "Total elapsed time: {} seconds".format(int(total_time))
                print (time_elapsed)
                scheduled_page_report.append(time_elapsed)

            except Exception as e:
                problem = 'Problem with blog {}: {}'.format(b, e)
                print (problem)
                scheduled_page_report.append(problem)

    if scheduled_page_report:
        message_text = '''
This is a scheduled-tasks report from the installation of {}.

{}
'''.format(product_id,
        '\n'.join(scheduled_page_report))

        import smtplib
        from email.mime.text import MIMEText

        from core.auth import get_users_with_permission, role
        admin_users = get_users_with_permission(role.SYS_ADMIN)

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

