import sys
import re
import os
import tarfile
import math


def xstr(s):
    return '' if s is None else str(s)


def upperfirst(x):
    return x[0].upper() + x[1:]


def str2num(s):
    try:
        return int(s)
    except ValueError:
        return float(s)


def removeLeadSpacesFromStrList(strList):
    for iLine, line in enumerate(strList):
        strList[iLine] = strList[iLine].lstrip()
    return strList


def removeTrailingCharFromStrList(strList, char2strip):
    for iLine, line in enumerate(strList):
        strList[iLine] = strList[iLine].rstrip().rstrip(char2strip) + '\n'
    return strList


def difflists(first, second):
    second = set(second)
    return [item for item in first if item not in second]


def textStartsWithExactMath(text, flag_str, delimiter):
    if delimiter is None:
        delimiter = '\\b'
    if flag_str:
        if text.startswith(flag_str + delimiter):
            return True
        else:
            return False
    else:
        return True


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")


def str2slice(text):
    return slice(
        *map(lambda x: int(x.strip()) if x.strip() else None, text.split(':')))


def str_2_int_list(text):
    """
    This function parses a string and returns a list of integers or an slice object
    :param text: Examples: "1" -> [1], "1,2" -> [1,2], "1:4:2" -> slice(1,4,2)
    :return: returns a list of integers or a slice object
    """
    if ":" in text:
        int_list = str2slice(text)
    elif "," in text:
        int_list = read_ints_from_string(text, ",")
    else:
        int_list = [int(text)]
    return int_list


def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


def frange_old(a, b, inc):
    if isInt(a) and isInt(b) and isInt(inc):
        a = int(a)
        b = int(b)
        inc = int(inc)
    else:
        a = float(a)
        b = float(b)
        inc = float(inc)
    x = [a]
    for i in range(1, int(math.ceil(((b + inc) - a) / inc))):
        x.append(a + i * inc)
    return (str(e) for e in x)


def frange(a, b, inc):
    if isInt(a) and isInt(b) and isInt(inc):
        a=int(a)
        b=int(b)
        inc=int(inc)
    else:
        a=float(a)
        b=float(b)
        inc=float(inc)
    x = [a]
    if inc > 0:
        while x[-1]+inc-b < 1e-15:
            x.append(x[-1] + inc)
    else:
        while x[-1]+inc-b > -1e-15:
            x.append(x[-1] + inc)
    return (str(e) for e in x)


def expandVars(v, RangeDelimiter = ':'):
    min = v.split(RangeDelimiter)[0]
    max = v.split(RangeDelimiter)[1]
    step = v.split(RangeDelimiter)[2]
    v = ','.join(frange(min, max, step))
    return v


def parse_pval(pval, valsdelimiter="_"):
    # First remove redundant (multiple/leading/trailing) delimiters in pval
    pval = ' '.join(pval.replace(valsdelimiter, ' ').split())
    pval = pval.split(" ")
    values = []
    for value in pval:
        if ":" in value:
            values.extend(expandVars(value).split(","))
        else:
            values.extend([value])
    return values


def str2numList(pval, valsdelimiter=','):
    if valsdelimiter in pval:
        pval = pval.split(valsdelimiter)
    elif ":" in pval:
        pval = expandVars(pval).split(",")
    else:
        pval = [pval]
    numList = [str2num(x) for x in pval]
    return numList


def read_ints_from_file_pointer(file_pointer, flag_str, num_data,
                                delimiter=None, startIndex=0):
    data = []
    num_words_in_flag = len(flag_str.split())
    file_pointer.seek(0)
    for line in file_pointer:
        if textStartsWithExactMath(line, flag_str, delimiter):
            line = line[len(flag_str + xstr(delimiter)):]  # Remove flag from the beginning of line
            for i_data in range(num_data):
                data.append(int(line.split(delimiter)[i_data+startIndex]))
    if len(data) < num_data:
        print("Error: cannot read ", flag_str, " from input file")
        sys.exit(1)
    return data


def list2string(inputList):
    return '[%s]' % ', '.join(map(str, inputList))


def string2list(input_string, delimiter=','):
    return [x.strip() for x in input_string.split(delimiter)]


def read_floats_from_file_pointer(file_pointer, flag_str, num_data,
                                  delimiter=None, startIndex=0):
    data = []
    num_words_in_flag = len(flag_str.split())
    file_pointer.seek(0)
    for line in file_pointer:
        if textStartsWithExactMath(line, flag_str, delimiter):
            line = line[len(flag_str + xstr(delimiter)):]  # Remove flag from the beginning of line
            for i_data in range(num_data):
                data.append(float(line.split(delimiter)[i_data + startIndex]))
    if len(data) < num_data:
        print("Error: cannot read ", flag_str, " from input file")
        sys.exit(1)
    return data


def read_string_from_file_pointer(file_pointer, flag_str, delimiter=None,
                                  start_index=0):
    data = None
    file_pointer.seek(0)
    lines = file_pointer.readlines()
    for i, line in enumerate(lines):
        if textStartsWithExactMath(line, flag_str, delimiter):
            if len(flag_str) > 0:
                # Remove flag from the beginning of line
                line = line[len(flag_str + xstr(delimiter)):]
            if delimiter != "\n":
                data = line.split(delimiter)[start_index]
            else:
                data = lines[i + 1 + start_index]

            break
    if not data:
        print("Error: cannot read ", flag_str, " from file ", file_pointer.name)
        raise ValueError
    return data


def read_float_from_file_pointer(file_pointer, flag_str, delimiter=None,
                                 start_index=0):
    try:
        data = read_string_from_file_pointer(file_pointer, flag_str, delimiter,
                                             start_index)
        float_number = float(data)
    except ValueError:
        print('Error reading float {} from file {}'.format(flag_str, file_pointer.name))
        raise ValueError
    return float_number


def read_int_from_file_pointer(file_pointer, flag_str, delimiter=None, start_index=0):
    try:
        data = read_string_from_file_pointer(file_pointer, flag_str, delimiter,
                                             start_index)
        int_number = int(data)
    except ValueError:
        print('Error reading int {} from file {}'.format(flag_str, file_pointer.name))
        raise ValueError
    return int_number


def read_int_from_strList(strList, flag_str, delimiter=None, startIndexInLine=0,
                          startLine=0):
    data = []
    for line in strList[startLine:]:
        if textStartsWithExactMath(line, flag_str, delimiter):
            line = line[len(flag_str + xstr(delimiter)):]  # Remove flag from the beginning of line
            data = int(line.split(delimiter)[startIndexInLine])
            break
    if not isinstance(data, int):
        print("Error: cannot read ", flag_str, " from input file")
        sys.exit(1)
    return data


def get_line_number_in_file(file_pointer, flag_str, match_first=True):
    line_num = None
    file_pointer.seek(0)
    for i, line in enumerate(file_pointer,1):
        if flag_str in line:
            line_num = i
            if match_first:
                return line_num
    return line_num


def get_index_in_str_list(str_list, flag_str, match_first=True, start_from=0):
    line_num = None
    for i, line in enumerate(str_list[start_from:], start_from):
        if flag_str in line:
            line_num = i
            if match_first:
                return line_num
    return line_num


def read_int_from_file_line_offset(file_pointer, flag_str, offset=0):
    file_pointer.seek(0)
    lines = file_pointer.readlines()
    int_line = get_index_in_str_list(lines, flag_str) + offset + 1
    data = int(lines[int_line])
    return data


def read_ints_from_file_line_offset(file_pointer, flag_str, delimiter=None, offset=0,
                                    end_line=None, end_flag=None):
    """Read integers from a file. First, find a string. Then read all the integers in
    the lines starting from the line at the matched string + offset up to
    line at the matched staring + end_line. By default, start reading from the line
    following the matched string up to the end of the file.
    """
    file_pointer.seek(0)
    lines = file_pointer.readlines()
    start_index = get_index_in_str_list(lines, flag_str) + offset + 1

    if end_line:
        end_line = start_index + end_line

    data = []
    for line in lines[start_index:end_line]:
        if end_flag:
            if end_flag in line:
                break
        data.extend(read_ints_from_string(line, delimiter))

    return data


def read_floats_from_file_line_offset(file_pointer, flag_str, delimiter=None, offset=0):
    file_pointer.seek(0)
    lines = file_pointer.readlines()
    data_line_num = get_index_in_str_list(lines, flag_str) + offset
    data = read_floats_from_string(lines[data_line_num + 1], delimiter)
    return data


def read_str_from_strList(strList, flag_str, delimiter=None,
                          startIndex=0, index2start=0):
    data = []
    for line in strList[index2start:]:
        if textStartsWithExactMath(line, flag_str, delimiter):
            line = line[len(flag_str + xstr(delimiter)):]  # Remove flag from the beginning of line
            data = line.split(delimiter)[startIndex]
            data = data.rstrip()
            break
    if not isinstance(data, str):
        print("Error: cannot read ", flag_str, " from input file")
        sys.exit(1)
    return data


def read_floats_from_string(str2read, delimiter=None):
    strList = str2read.split(delimiter)
    floatList = [float(i) for i in strList]
    return floatList


def read_ints_from_string(str2read, delimiter=None):
    if delimiter != '\n':
        str2read = str2read.rstrip('\n')
    if delimiter is not None:
        str2read = str2read.replace(' ', '')
    strList = str2read.split(delimiter)
    strList = list(filter(None,strList))
    intList = [int(i) for i in strList]
    return intList


def open_file(file_name, open_mode="r"):
    if open_mode == "w":
        if not os.path.exists(os.path.dirname(file_name)):
            if os.path.dirname(file_name):
                os.makedirs(os.path.dirname(file_name))
    try:
        file_pointer = open(file_name, open_mode)
        return file_pointer
    except IOError:
        print("Error: cannot open file", file_name)
        raise IOError


def tarDirectory(output_filename, source_dir, compressMode="w"):
    with tarfile.open(output_filename, compressMode) as tar:
        tar.add(source_dir, arcname=os.path.basename(source_dir))


def setOptionalSysArgs(args, paramDefaultValue, argNumber):
    if len(args) >= (argNumber+1):
        param = args[argNumber]
    else:
        param = paramDefaultValue
    return param


def remove_non_ascii_string(text, replace_char=' '):
    """remove non-ascii characters from file"""
    non_ascii_text = ''.join([i if ord(i) < 128 else replace_char for i in text])
    return non_ascii_text


def remove_non_ascii_list(string_list, replace_char=' '):
    non_ascii_list = []
    for text in string_list:
        non_ascii_list.append(remove_non_ascii_string(text, replace_char))
    return non_ascii_list


def byteify(input):
    """
    Got this function from https://stackoverflow.com/questions/2357230/what-is-the-proper-way-to-comment-functions-in-python
    "This short and simple recursive function will convert any decoded JSON object from using unicode strings to
    UTF-8-encoded byte strings"
    This is not the most efficient solution. See the code provided by Mirec Miskuf to see how to use an object_hook to
    do this more efficiently.
    """
    if isinstance(input, dict):
        try:
            inputItems = input.iteritems()
        except:
            inputItems = input.items()
        return {byteify(key): byteify(value)
                for key, value in inputItems}
    elif isinstance(input, list):
        return [byteify(element) for element in input]
    elif (sys.version_info[0] < 3):
        if isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input
    else:
        if isinstance(input, bytes):
            return input.encode('utf-8')
        else:
            return input


def correctDelimiterInputStrs(inputDelimiter):

    if sys.version_info[0] < 3:
        correctedDelimiter = str(inputDelimiter.decode('unicode-escape'))
    else:
        correctedDelimiter = bytes(inputDelimiter,'utf-8').decode('unicode_escape')

    return correctedDelimiter
