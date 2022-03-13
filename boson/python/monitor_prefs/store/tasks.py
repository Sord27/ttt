import logging


def findFFT(MAC, row,outPutSheet,child,intiate):
    if intiate[0] == "true":
        outPutSheet.title = "FFT"
        outPutSheet['A1'] = "MAC"
        outPutSheet['B1'] = "Status"
        intiate[0] = "false"
    child.sendline("cd /tmp")
    child.expect(":/tmp#")
    logging.debug(child.after)
    logging.debug(child.before)
    logging.debug(child.buffer)

    child.sendline("ls -asl")
    child.expect(":/tmp#")
    logging.debug(child.after)
    logging.debug(child.before)
    logging.debug(child.buffer)

    # gpio.lock


    str1 = child.before
    test = str1.decode()
    find_staus = test.find("gpio.lock")
    if find_staus != -1:
        print(type(test))
        print(test)
        print("\nFoooooooooooooouuuuuuuuuuuuuuuunnnnnnnnnnnnnnndddddddddddddddddddddddddd\n")
        outPutSheet['A' + str(row)].value = MAC
        outPutSheet['B' + str(row)].value = "found"
        print(find_staus)

    child.sendline("logout")
    child.expect("closed.")
    logging.debug(child.before)
    logging.debug(child.after)
    logging.debug(child.buffer)
     return



def FNDStatus(MAC, row,outPutSheet,child,intiate):
    child.sendline("bio plgg; bio mfvr; baml")
    child.expect(":~#")
    logging.debug(child.after)
    logging.debug(child.before)
    logging.debug(child.buffer)
    '''
    child.sendline("ls -asl")
    child.expect(":/tmp#")
    logging.debug(child.after)
    logging.debug(child.before)
    logging.debug(child.buffer)

    # gpio.lock


    str1 = child.before
    test = str1.decode()
    find_staus = test.find("gpio.lock")
    if find_staus != -1:
        print(type(test))
        print(test)
        print("\nFoooooooooooooouuuuuuuuuuuuuuuunnnnnnnnnnnnnnndddddddddddddddddddddddddd\n")
        outPutSheet['A' + str(row)].value = MAC
        outPutSheet['B' + str(row)].value = "found"
        print(find_staus)

    child.sendline("logout")
    child.expect("closed.")
    logging.debug(child.before)
    logging.debug(child.after)
    logging.debug(child.buffer)
    '''
    intiate[0] = "false"
    child.sendline("logout")
    child.expect("closed.")
    return