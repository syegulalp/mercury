#!/usr/bin/env python3

# TODO: add cmdline options to suppress emailed reports

if __name__ == '__main__':
    if __package__ is None:
        import sys
        from os import path
        sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
        import settings

    DB = settings.DB
    from core.libs.playhouse.dataset import DataSet

    print("Beginning import process.")

    print("Cleaning DB.")

    DB.clean_database()

    xdb = DataSet(DB.dataset_connection())

    try:
        with xdb.transaction():
            for table_name in xdb.tables:
                print("Loading table " + table_name)
                # yield "<p>" + n
                try:
                    table = xdb[table_name]
                except:
                    print("<p>Sorry, couldn't create table ", table_name)
                else:
                    filename = (settings.APPLICATION_PATH + settings.EXPORT_FILE_PATH +
                        '/dump-' + table_name + '.json')
                    if path.exists(filename):
                        try:
                            table.thaw(format='json',
                                filename=filename,
                                strict=True)
                        except Exception as e:
                            print("<p>Sorry, error:{}".format(e))

                    else:
                        print("No data for table " + table_name)
                        # yield "<p>" + n
    except Exception as e:
        print('Ooops: {}'.e)
    else:
        xdb.query(DB.post_import())
        xdb.close()
        DB.recreate_indexes()
        print("Import process ended.")
