"""
Program 1: Question 1

Author: Samson Okunola
Partner: Tyler Cummings

Description: Script that replaces integers to numeric and ordinal words
using regex matching

"""
import re
import sys


input_file = sys.argv[1]  # gets input file name from command line
output_file = sys.argv[2]  # gets output file name from command line

conversion_dictionary = {  # dictionary of all values and keys
    "0": "zero",
    "1": "one", 
    "2": "two",
    "3": "three",
    "4": "four",
    "5": "five",
    "6": "six",
    "7": "seven",
    "8": "eight",
    "9": "nine",
    "10": "ten",
    "1st": "first",
    "2nd": "second",
    "3rd": "third",
    "4th": "fourth",
    "5th": "fifth",
    "6th": "sixth",
    "7th": "seventh",
    "8th": "eigth",
    "9th": "ninth",
    "10th": "tenth"
}

pattern = re.compile(
    r'(?<!\w)(' + '|'.join(key for key in conversion_dictionary.keys()) + r')(?!\w)')

with open(input_file, "r") as input: #These next few of code takes the text and reads through it converting the numbers into words
    with open(output_file, "w") as output:
        for line in input:
            converted = pattern.sub(
                lambda key: conversion_dictionary[key.group()], line)
            output.write(converted)