#!/usr/bin/env python3

import argparse
import sys
import csv


def addArgs():
    global args
    global argsList
    global parsers
    global functions
    global values
    global group
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', dest='file', required=True)
    parser.add_argument('--top', dest='top', action='append', nargs=2)
    parser.add_argument('--min', dest='min', type=str)
    parser.add_argument('--max', dest='max', type=str)
    parser.add_argument('--mean', dest='mean', type=str)
    parser.add_argument('--sum', dest='sum', type=str)
    parser.add_argument('--count', action='store_true', dest='count')
    parser.add_argument('--group-by', dest='group', type=str)
    args = parser.parse_args()

    argsList = []
    values = {}
    parsers = ['min', 'max', 'mean', 'sum']
    functions = ['count']
    group = None

    for i in sys.argv[3:]:
        argsList.append(i.strip('--'))
    for index, field in enumerate(argsList):
        if field in parsers:
            values[field + "_" + argsList[index + 1]] = 0.0
        elif field in functions:
            values[field] = 0.0
        elif field == 'top':
            values[field + "_" + argsList[index + 1] + "_" + argsList[index + 2]] = 0.0
        elif field == 'group-by':
            group = argsList[index + 1]


def fileOpen(file):
    global f
    try:
        f = open(file, 'r', encoding='UTF-8-SIG', newline='')
        reader = csv.DictReader(f)
        return reader

    except FileNotFoundError:
        sys.stderr.write('Error: File not found.')


def computeAggregates(dictionary, should_group):
    count = {}
    high = {}
    low = {}
    sum_num = {}
    groups = {}
    top_list = {}
    total_count = 0
    for row in dictionary:
        # Create a new id for unique groups
        if should_group:
            if row[group] not in groups:
                groups[row[group]] = 0

        for index in values:
            if should_group:
                if index.find("top") != -1:
                    first, second, third = index.split("_")
                    currGroup = (row[group] + "_" + row[third])
                elif index.find("_") != -1:
                    first, second = index.split("_")
                    currGroup = (second + "_" + row[group])
                else:
                    first = index
                    currGroup = (first + "_" + row[group])
            else:
                if index.find("top") != -1:
                    first, second, third = index.split("_")
                    currGroup = row[third]
                elif index.find("_") != -1:
                    first, second = index.split("_")
                    currGroup = second
                else:
                    first = index
                    currGroup = first

            # Finds Max Value
            if first == 'max':
                val = float(row[second])
                if currGroup not in high:
                    high[currGroup] = val
                else:
                    if val > high[currGroup]:
                        high[currGroup] = val
            elif first == 'min':
                val = float(row[second])
                if currGroup not in low:
                    low[currGroup] = val
                else:
                    if val < low[currGroup]:
                        low[currGroup] = val
            elif first == 'mean' or first == 'sum':
                val = float(row[second])
                if currGroup not in sum_num:
                    sum_num[currGroup] = val
                else:
                    sum_num[currGroup] += val
            elif first == 'top':
                if currGroup not in top_list:
                    top_list[currGroup] = 1
                else:
                    top_list[currGroup] += 1

            # Increment count for each group
            if first == 'count':
                if currGroup not in count:
                    count[currGroup] = 1
                else:
                    if count[currGroup] == 140000:
                        print("WTF")
                    count[currGroup] += 1
            total_count += 1

    # OUTPUT ##################################
    if should_group:
        outputGroup(groups, top_list, high, low, count, sum_num)
    else:
        outputAggregates(top_list, high, low, total_count, sum_num)


def outputAggregates(top_list, high, low, count, sum_num):
    for i in values:
        sys.stdout.write(i.lower() + ",")
    sys.stdout.write("\n")

    for val in values:

        if val.find("top") != -1:
            first, second, third = val.split("_")
        elif val.find("_") != -1:
            first, second = val.split("_")
        else:
            first = val

        if first == 'max':
            sys.stdout.write('"' + str(high[second]) + '"')
        elif first == 'min':
            sys.stdout.write(str(low[second]) + ",")
        elif first == 'mean':
            sys.stdout.write(str('"' + str(sum_num[second] / count)) + '"')
        elif first == 'sum':
            sys.stdout.write('"' + str(sum_num[second]) + '"')
        elif first == 'count':
            sys.stdout.write(str(count[first]) + ",")
        elif first == 'top':
            sys.stdout.write('"')
            for i in range(0, int(second)):
                maxVal = max(top_list.items(), key=lambda x: x[1])
                if val == 0:
                    sys.stdout.write(str(maxVal[0]) + ": " + str(maxVal[1]))
                else:
                    sys.stdout.write(str(maxVal[0]) + ": " + str(maxVal[1]) + ",")
                del top_list[maxVal[0]]
            sys.stdout.write('" ')


def outputGroup(groups, top_list, high, low, count, sum):
    sys.stdout.write(group + ",")
    for i in values:
        sys.stdout.write(i.lower() + ",")
    sys.stdout.write("\n")
    for output in sorted(groups):
        sys.stdout.write(output + ",")

        for val in values:

            if val.find("top") != -1:
                first, second, third = val.split("_")
            elif val.find("_") != -1:
                first, second = val.split("_")
            else:
                first = val

            if first == 'max':
                sys.stdout.write(str(high[second + "_" + output]) + ",")
            elif first == 'min':
                sys.stdout.write(str(low[second + "_" + output]) + ",")
            elif first == 'mean':
                sys.stdout.write(str(sum[second + "_" + output] / count["count" + "_" + output]))
            elif first == 'sum':
                sys.stdout.write(str(sum[second + "_" + output]))
            elif first == 'count':
                sys.stdout.write(str(count[first + "_" + output]) + ",")
            elif first == 'top':
                sys.stdout.write('"')
                for i in range(0, int(second)):
                    maxVal = max(top_list.items(), key=lambda x: x[1])
                    if val == 0:
                        sys.stdout.write(str(maxVal[0]) + ": " + str(maxVal[1]))
                    else:
                        sys.stdout.write(str(maxVal[0]) + ": " + str(maxVal[1]) + ",")
                    del top_list[maxVal[0]]
                sys.stdout.write('" ')
        sys.stdout.write("\n")


def main():
    addArgs()
    dict_csv = fileOpen(args.file)
    # Group by
    if group is not None:
        computeAggregates(dict_csv, True)
    else:
        computeAggregates(dict_csv, False)


if __name__ == '__main__':
    main()
