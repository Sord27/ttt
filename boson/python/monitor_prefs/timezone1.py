import datetime
import calendar

#def UtcNow():
now = datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S %Z %Y")
print(now)
#return int(now.strftime("%s"))



datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S %Z %Y")

todaydate = datetime.datetime.utcnow().strftime("%m/%d/%y")
print(todaydate)
dayoftheweek= datetime.datetime.utcnow().strftime("%A")
print(dayoftheweek)
dayoftheweek = dayoftheweek.lower()
print(dayoftheweek)

yesterdayDate = datetime.datetime.utcnow() - datetime.timedelta(1)
print ("today = " + str(datetime.datetime.utcnow().strftime("%a %b %d %H:%M:%S %Z %Y")) + "    Yesterday =:" + str(yesterdayDate.strftime("%a %b %d %H:%M:%S %Z %Y")))
yesterDayOfTheweek = calendar.day_name[yesterdayDate.weekday()]
yesterDayOfTheweek = yesterDayOfTheweek.lower()
yesterdayDate = yesterdayDate.strftime('%m/%d/%y')

#dayOftheweek = calendar.day_name[my_date.weekday()]
#today = datetime.utcnow("%m/%d/%y")