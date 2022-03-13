
startinghours = "00"
while True:
    print ("\nYou can enter c/C to contiuew with defualt value for the")
    startinghours = input("Starting from hour in the format 00 to 24:")
    if  startinghours == "c" or  startinghours=="C":
        break
    print(startinghours)
    if startinghours < "00" or startinghours >= "24":
        print("incorrect format for time, please enter value between 00 to 24 : ")

    else:
        break
if startinghours >= "00" and startinghours <= "09":
    morningSerachStart = startinghours[1]
    print ("\n morning time = ",morningSerachStart)
elif startinghours >= "10" and startinghours <= "19":
    noonSearchStart = startinghours[1]
    print("\n morning time = ", noonSearchStart)
elif startinghours >= "20" and startinghours <= "23":
    nighSerachStart = startinghours[1]
    print("\n morning time = ", nighSerachStart)

print(type(startinghours ))
print(startinghours)
print("\n")
print(startinghours[0])
print("\n")
print(startinghours[1])

morningSerachStart = startinghours[1]
noonSearchStart    = startinghours[1]
nighSerachStart    = startinghours[1]

'''
if start <= 9:
    timelimit = r'(?:(0[' + str(start) + r'-9]|1[0-9]|2[0-3]))'
if start = > 10:
    timelimit = '(?:(1[0-9]|2[0-3]))'
if start = > 20:
    timelimit = '(?:(2[0-3]))'
'''