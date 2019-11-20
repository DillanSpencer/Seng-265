#!/usr/bin/env python3

import argparse
import os
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


def computeAggregates(dictionary):
    high = None
    low = None
    sum = 0
    count = 0
    topList = {}
    for row in dictionary:
        for index in values:
            if index.find("top") != -1:
                first, second, third = index.split("_")
            elif index.find("_") != -1:
                first, second = index.split("_")
            else:
                first = index

            # Display Fields
            if count == 0:
                sys.stdout.write(index + ", ")

            # Finds Max Value
            if first == 'max':
                current = float(row[second])
                if high is None or current > high:
                    high = current

            # Finds Min Value
            elif first == 'min':
                current = float(row[second])
                if low is None or current < low:
                    low = current
            # Find the Mean
            elif first == 'mean' or first == 'sum':
                current = float(row[second])
                sum += current
            elif first == 'top':
                current = row[third]
                if current not in topList:
                    topList[current] = 1
                else:
                    topList[current] += 1

        # Increment count
        count += 1
    # Output values
    sys.stdout.write("\n")
    for output in values:
        if output.find("top") != -1:
            first, second, third = output.split("_")
        elif output.find("_") != -1:
            first, second = output.split("_")
        else:
            first = index
        # Finds Max Value
        if first == 'max':
            sys.stdout.write(str(high) + ", ")
        elif first == 'min':
            sys.stdout.write(str(low) + ", ")
        elif first == 'mean':
            sys.stdout.write(str(sum / count))
        elif first == 'sum':
            sys.stdout.write(str(sum))
        elif first == 'count':
            sys.stdout.write(str(count) + ", ")
        elif first == 'top':
            sys.stdout.write('"')
            for val in range(0, int(second)):
                maxVal = max(topList.items(), key=lambda x: x[1])
                if val == 0:
                    sys.stdout.write(str(maxVal[0]) + ": " + str(maxVal[1]))
                else:
                    sys.stdout.write("," + str(maxVal[0]) + ": " + str(maxVal[1]))
                del topList[maxVal[0]]
            sys.stdout.write('" ')


def computeGroupBy(dictionary):
    count = {}
    high = {}
    low = {}
    sum = {}
    groups = {}
    for row in dictionary:
        # Create a new id for unique groups
        if row[group] not in groups:
            groups[row[group]] = 0

        currGroup = row[group]
        for index in values:

            if index.find("top") != -1:
                first, second, third = index.split("_")
            elif index.find("_") != -1:
                first, second = index.split("_")
            else:
                first = index

            # Finds Max Value
            if first == 'max':
                val = float(row[second])
                if currGroup not in high:
                    high[currGroup] = val
                else:
                    if val > high[currGroup]:
                        high[currGroup] = val
            if first == 'min':
                val = float(row[second])
                if currGroup not in low:
                    low[currGroup] = val
                else:
                    if val < low[currGroup]:
                        low[currGroup] = val
            if first == 'mean' or first == 'sum':
                val = float(row[second])
                if currGroup not in sum:
                    sum[currGroup] = val
                else:
                    sum[currGroup] += val

        # Increment count for each group
        if currGroup not in count:
            count[currGroup] = 1
        else:
            if count[currGroup] == 140000:
                print("WTF")
            count[currGroup] += 1
    for output in sorted(groups):
        sys.stdout.write(output + ": ")
        for val in values:
            if val.find("top") != -1:
                first, second, third = val.split("_")
            elif val.find("_") != -1:
                first, second = val.split("_")
            else:
                first = val

            # Finds Max Value
            if first == 'max':
                sys.stdout.write(str(high[output]) + ", ")
            elif first == 'min':
                sys.stdout.write(str(low[output]) + ", ")
            elif first == 'mean':
                sys.stdout.write(str(sum[output] / count[output]))
            elif first == 'sum':
                sys.stdout.write(str(sum[output]))
            elif first == 'count':
                sys.stdout.write(str(count[output]) + ", ")
        sys.stdout.write("\n")


def main():
    addArgs()
    dict_csv = fileOpen(args.file)
    # computeAggregates(dict_csv)
    computeGroupBy(dict_csv)


if __name__ == '__main__':
    main()
