import os, json, datetime
from core.libs import pytz
utc = pytz.utc
eastern = pytz.timezone('US/Eastern')
# from core.utils import DATE_FORMAT
DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f'
DATE_FORMAT_2 = '%Y-%m-%d %H:%M:%S'

path = r'D:\Users\Genji\git\MeTal\data\saved'

os.mkdir(path + '\\converted')

for f in os.listdir(path):
    f_path = os.path.join(path, f)
    if os.path.isfile(f_path):
        with open(f_path, 'r') as my_file:
            data = my_file.read()

        data_obj = json.loads(data)

        for n in data_obj:
            for m in n:
                if m[-5:] == '_date':
                    print ("Old", n[m])
                    if n[m] == '' or n[m] is None:
                        pass
                    else:
                        try:
                            old_time = datetime.datetime.strptime(n[m], DATE_FORMAT)
                        except ValueError:
                            old_time = datetime.datetime.strptime(n[m], DATE_FORMAT_2)
                        except:
                            raise
                        print ('New', old_time)

                        new_time = old_time.replace(tzinfo=eastern)
                        print ('With TZ', new_time)
                        utc_time = new_time.astimezone(utc)
                        print ('As UTC', utc_time)
                        fmt_time = utc_time.strftime(DATE_FORMAT_2)
                        print ('Formatted', fmt_time)

                        n[m] = fmt_time

        with open(path + '\\converted\\' + f, 'w') as output:
            output.write(json.dumps(data_obj))
