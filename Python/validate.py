"""
Program 1: Question 2

Author: Samson Okunola
Partner: Tyler Cummings

Description: Script that validates the data entered
into a database table

"""


from asyncio.windows_events import NULL
import re
import sys

input_file = sys.argv[1]
output_file = sys.argv[2]


# Function that validates the data on each line. Returns bools coupled with their respective data vals
def validate(line):

    data = line.split("\t")  # splits the line by its tabs
    if len(data) >= 4:
        customer_id = bool(re.match(r'[0-9]{3}[A-Z]{3}', data[0]))
        name = bool(
            re.match(r'[a-zA-Z]+\s*([a-zA-Z]+)?(,\s*(Jr\.|Sr\.|I|II|III|IV|V))?$', data[1]))
        zip_code = bool(re.match(r'\d{5}(-\d{4})?$', data[2]))
        number_purchased = bool(re.match(r'^[1-9]\d*$', data[3]))
        purchase_amount = bool(re.match(r'^\$\d+\.\d{2}', data[4]))
        return customer_id, data[0], name, data[1], zip_code, data[2], number_purchased, data[3], purchase_amount, data[4]
    else:
        return NULL


record_number = 1

with open(input_file, "r") as input:
    with open(output_file, "w") as output:
        # Actually handles the logic. Assesses the piece of data and its validation result
        # Concatenates error messages to be written to the output file
        for line in input:
            error_msg = ""
            validation_results = validate(line)
            if validation_results != NULL:
                if validation_results[0] == False:
                    error_msg += "Error in ID field of record " + \
                        str(record_number) + ": " + \
                        validation_results[1] + "\n"
                if validation_results[2] == False:
                    error_msg += "Error in Name field of record " + \
                        str(record_number) + ": " + \
                        validation_results[3] + "\n"
                if validation_results[4] == False:
                    error_msg += "Error in Zip code field of record " + \
                        str(record_number) + ": " + \
                        validation_results[5] + "\n"
                if validation_results[6] == False:
                    error_msg += "Error in Number purchased field of record " + \
                        str(record_number) + ": " + \
                        validation_results[7] + "\n"
                if validation_results[8] == False:
                    error_msg += "Error in Purchase amount field of record " + \
                        str(record_number) + ": " + validation_results[9]
                record_number += 1
                output.write(error_msg)
            else:
                print("Error, list does not have enough elements")
                break
