#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 25 14:15:09 2023

This script is for creating histograms that allow us to determine thresholds for length and quality
and to see the effects of filtering

@author: harshitarupani
"""
# Parsing through the fastQ file generated by Guppy to get attributes like read id, length, overall read quality
from Bio import SeqIO
import matplotlib.pyplot as plt
import os
import io
import argparse

total_quality = 0
total_bases = 0
qual_filtered_count = 0
len_filtered_count = 0
records_total = 0
skipped_invalid_records = 0  # Counter for skipped invalid records

all_read_lengths = []
all_quality_scores = []
retained_read_lengths = []
retained_quality_scores = []

parser = argparse.ArgumentParser(description='Length and Quality Filter')
parser.add_argument('-i', '--input', type=str, required=True, help='Input fastq file')
parser.add_argument('-o', '--output', type=str, required=True, help='Output fastq filtered file')
parser.add_argument('-g', '--graph', type=str, required=True, help='Output svg graph file')
parser.add_argument('-lmin', '--length-min', type=int, required=True, help='Filter length min')
parser.add_argument('-lmax', '--length-max', type=int, required=True, help='Filter length max')
parser.add_argument('-q', '--quality-threshold', type=float, required=True, help='Filter quality threshold')
parser.add_argument('-d', action='store_true', required=False, help='Display Graph')
args = parser.parse_args()

input_filename = args.input # e.g. "Unique_Molecular_Identifier/bc3_final.fastq"
output_filename = args.output # e.g. "filtered/blah.fastq"

output_file = open(output_filename, "w")

first_record_written = False

with open(input_filename, "r") as file:
    record_lines = []
    for line in file:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        record_lines.append(line)

        # Check if the record_lines list has exactly 4 lines
        if len(record_lines) == 4:
            # Check if the record starts with '@'
            if not record_lines[0].startswith('@'):
                print(f"Warning: Skipping invalid record starting with: {record_lines[0]}")
                skipped_invalid_records += 1
                record_lines = []
                continue

            # Check lengths of sequence and quality lines
            seq_length = len(record_lines[1])
            qual_length = len(record_lines[3])
            if seq_length != qual_length:
                print(
                    f"Warning: Skipping record {record_lines[0]} due to mismatched lengths of sequence and quality values."
                )
                record_lines = []
                continue

            # Process the record as before
            record = SeqIO.read(io.StringIO("\n".join(record_lines)), "fastq")

            qualities = record.letter_annotations["phred_quality"]
            total_quality += sum(qualities)
            total_bases += len(qualities)
            qual_score = sum(qualities) / len(record.seq)
            records_total += 1
            all_read_lengths.append(len(record.seq))
            all_quality_scores.append(qual_score)

            # print(qualities)
            print(
                "index %i, ID = %s, length %i, with %i features, qual = %.2f"
                % (
                    records_total - 1,
                    record.id,
                    len(record.seq),
                    len(record.features),
                    qual_score,
                )
            )

            is_record_filtered = False

            # reject based on quality first
            # then later reject based on length
            if qual_score <= args.quality_threshold:
                qual_filtered_count += 1
                is_record_filtered = True
            else:
                record_length = len(record.seq)
                if record_length >=args.length_min and record_length <= args.length_max: 
                    retained_quality_scores.append(qual_score)
                    retained_read_lengths.append(record_length)
                else:
                    len_filtered_count += 1
                    is_record_filtered = True

            if not is_record_filtered:

                if first_record_written:
                    output_file.write("\n")

                # write the entry to the fastq file
                output_file.write("@" + record.id + "\n")
                output_file.write(str(record.seq) + "\n")
                output_file.write("+\n")
                qual_lookup_ascii = "!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\\]^_`abcdefghijklmnopqrstuvwxyz{|}~"
                qual_string = ""
                for qual in qualities:
                    qual_string += qual_lookup_ascii[qual]
                output_file.write(qual_string)
                first_record_written = True

            record_lines = []

output_file.close()

if total_bases > 0:
    print("overall_qual = %.2f" % (total_quality / total_bases))

print("records total = ", records_total)
print("skipped invalid records = ", skipped_invalid_records)

print("records rejected due to low quality = ", qual_filtered_count)
print("records rejected due to outside of expected length = ", len_filtered_count)

total_outputted = records_total - skipped_invalid_records - qual_filtered_count - len_filtered_count
print("records retained, i.e. total records outputted = ", total_outputted)


# Create the read lengths histogram
plt.figure(figsize=(10, 8))
plt.subplot(2, 2, 1)
plt.hist(all_read_lengths, bins=50, edgecolor="k")
plt.title("All Read Lengths Histogram")
plt.xlabel("Read Length (bp)")
plt.ylabel("Frequency")

# Create the quality scores histogram
plt.subplot(2, 2, 2)
plt.hist(all_quality_scores, bins=50, edgecolor="k")
plt.title("All Quality Scores Histogram")
plt.xlabel("Quality Score")
plt.ylabel("Frequency")
# plt.tight_layout()

# Create the filtered read lengths histogram
plt.subplot(2, 2, 3)
plt.hist(retained_read_lengths, bins=50, edgecolor="k")
plt.title("Retained Read Lengths Histogram")
plt.xlabel("Read Length (bp)")
plt.ylabel("Frequency")

# Create the filtered quality scores histogram
plt.subplot(2, 2, 4)
plt.hist(retained_quality_scores, bins=50, edgecolor="k")
plt.title("Retained Quality Scores Histogram")
plt.xlabel("Quality Score")
plt.ylabel("Frequency")
plt.tight_layout()
plt.savefig(args.graph, format='svg') # 'filtered_graph.svg'
if args.d:
    plt.show()

# had to manually concatenate barcode 3 trimmed files otherwise data from only first file is read 
# and the other files is discarded "skipped invalid records"
# when automatically concatenated 3 files: got 2 lines less than expected 