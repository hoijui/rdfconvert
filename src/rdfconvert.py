#!/usr/bin/env python3
"""
Project      : rdfconvert
Description  : Converts files and whole directory trees from one RDF serialization into another.
Author       : Wim Pessemier
Contact      : w**.p********@ster.kuleuven.be (replace *)
Organization : Institute of Astronomy, KU Leuven
SPDX-FileCopyrightText: 2013 Wim Pessemier <w**.p********@ster.kuleuven.be>
SPDX-FileCopyrightText: 2024 Robin Vobruba <hoijui.quaero@gmail.com>
SPDX-License-Identifier: BSD-3-Clause
"""

import argparse
import fnmatch
import os
import sys

from rdflib import Graph, plugin
from rdflib.parser import Parser
from rdflib.serializer import Serializer

plugin.register("rdf-json", Parser    , "rdflib_rdfjson.rdfjson_parser"    , "RdfJsonParser")
plugin.register("rdf-json", Serializer, "rdflib_rdfjson.rdfjson_serializer", "RdfJsonSerializer")

INPUT_FORMAT_TO_EXTENSIONS = {
    "application/rdf+xml" : [".xml", ".rdf", ".owl"],
    "text/html"           : [".html"],
    "xml"                 : [".xml", ".rdf", ".owl"],
    "rdf-json"            : [".json"],
    "json-ld"             : [".jsonld", ".json-ld"],
    "ttl"                 : [".ttl"],
    "nt"                  : [".nt"],
    "nquads"              : [".nq"],
    "trix"                : [".xml", ".trix"],
    "rdfa"                : [".xhtml", ".html"],
    "n3"                  : [".n3"]
    }
OUTPUT_FORMAT_TO_EXTENSION = {
    "xml"        : ".xml",
    "pretty-xml" : ".xml",
    "rdf-json"   : ".json",
    "json-ld"    : ".jsonld",
    "nt"         : ".nt",
    "nquads"     : ".nq",
    "trix"       : ".xml",
    "ttl"        : ".ttl",
    "n3"         : ".n3"
    }

# a function that returns the script description as a string
def description():
    return """
Convert one RDF serialization into another.

This script allows you to convert several files at once. It can
convert individual files or even whole directory trees at once
(with or without preserving the directory tree structure).
    """

# a function that returns additional help as a string
def epilog():
    s = "Default extensions for INPUT format:\n"
    for input_format, extensions in INPUT_FORMAT_TO_EXTENSIONS.items():
        s += f" - {input_format.ljust(19)} : {extensions}\n"
    s += "\n"
    s += "Default extension for OUTPUT format:\n"
    for ouptut_format, extension in OUTPUT_FORMAT_TO_EXTENSION.items():
        s += f" - {ouptut_format.ljust(10)} : '{extension}'\n"
    return s

def parse_args():
    parser = argparse.ArgumentParser(formatter_class = argparse.RawDescriptionHelpFormatter,
                                     description     = description(),
                                     epilog          = epilog())

    parser.add_argument("INPUT",
                        metavar="INPUT",
                        type=str,
                        nargs="+",
                        help="A list of input files or input directories. When *files* are " \
                             "specified, they will be parsed and converted regardless of their " \
                             "extension. But when *directories* are specified, the script will " \
                             "try to find files inside these directories that match certain " \
                             "extensions (either all default extensions for the input format as " \
                             "specified by the --from flag, or the custom extension(s) as " \
                             " specified directly by the --from-ext flag). Input directories may " \
                             " be searched recursively via the -R flag.")

    parser.add_argument("--from",
                        dest="FROM",
                        action="store",
                        required = True,
                        choices = INPUT_FORMAT_TO_EXTENSIONS.keys(),
                        help="The serialization format of the input files to convert.")

    parser.add_argument("--from-ext",
                        dest="FROM_EXT",
                        action="store",
                        nargs="+",
                        default=None,
                        help="The file extensions to match when browsing input directories " \
                             "(could be .owl, .xml, .n3, .jsonld, .rdf, ...). You only have to " \
                             "provide this flag if you're unhappy with the default extensions " \
                             "for the given input format. You can view these default extensions " \
                             "at the end of this help.")

    parser.add_argument("-R", "--recursive",
                        dest="recursive",
                        action="store_const",
                        const=True,
                        default=False,
                        help="When input directories are given, browse them recursively to find " \
                             "and convert files.")

    parser.add_argument("-o",
                        dest="OUTPUTDIR",
                        action="store",
                        nargs="?",
                        default=None,
                        help="The directory to write the output files " \
                             "(omit this flag to print the output to the stdout).")

    parser.add_argument("--to",
                        dest="TO",
                        action="store",
                        required = True,
                        choices = OUTPUT_FORMAT_TO_EXTENSION.keys(),
                        help="The serialization format of the output.")

    parser.add_argument("--to-ext",
                        dest="TO_EXT",
                        action="store",
                        default=None,
                        help="The file extension of the output files that will be created " \
                             "(could be .owl, .xml, .n3, .jsonld, .rdf, ...). You only have to " \
                             "provide this flag if you're unhappy with the default extension for " \
                             "the given output format. You can view these default extensions " \
                             "at the end of this help. When the -o flag is not " \
                             "specified, the output will be written the the stdout instead of " \
                             "files, so the --to-ext flag will have no effect. Don't forget to " \
                             "add a dot (.) in front of the extension name (so provide .foo " \
                             "instead of foo).")

    parser.add_argument("-f", "--force",
                        dest="force",
                        action="store_const",
                        const=True,
                        default=False,
                        help="Always overwrite existing output files, instead of prompting.")

    parser.add_argument("-n", "--no-tree",
                        dest="no_tree",
                        action="store_const",
                        const=True,
                        default=False,
                        help="When given in combination with -R (recursive input file matching), " \
                             "all output files will be written in the same \"flat\" directory. " \
                             "Without this -n flag, the same directory structure of the input " \
                             "directory will be created (if necessary) and the output files will " \
                             "be written to the corresponding directories of where they were " \
                             "found in the input directories. Only those output directories will " \
                             "be created for the input directories that contain at least one " \
                             "matching input file. If you specify this flag, all output files " \
                             "will be stored in the same directory and you may run into filename " \
                             "collisions!")

    parser.add_argument("-s", "--simulate",
                        dest="simulate",
                        action="store_const",
                        const=True,
                        default=False,
                        help="Do not write any output files, but just print a message for each "
                             "file that they *would* be written without the -s flag.")

    parser.add_argument("-v", "--verbose",
                        dest="verbose",
                        action="store_const",
                        const=True,
                        default=False,
                        help="verbosely print some debugging info.")

    args = parser.parse_args()

    return args

def get_output_abs_path(verbose, args, input_file_or_dir, head):
    if args.no_tree:
        output_abs_path = os.path.abspath(args.OUTPUTDIR)
    else:
        # remove the common prefix from the head and the input directory
        # (otherwise the given input path will also be added to the output path)
        common_prefix = os.path.commonprefix([head, input_file_or_dir])
        verbose(f" - input file or dir: {input_file_or_dir}")
        verbose(f" - common prefix: {common_prefix}")
        head_without_common_prefix = head[len(common_prefix)+1:]
        verbose(f" - head without common prefix: {head_without_common_prefix}")
        output_abs_path = os.path.join(os.path.abspath(args.OUTPUTDIR),
                                        head_without_common_prefix)
        verbose(f" - output absolute path: {output_abs_path}")

    return output_abs_path

def process_input_files(verbose, args, input_file_or_dir, output_extension, input_files):
    """
    Creates the graph, and parse the input files
    """

    for input_file in input_files:

        g = Graph()
        g.parse(input_file, format=args.FROM)

        verbose(" - the graph was parsed successfully")

        # if no output directory is specified, just print the output to the stdout
        if args.OUTPUTDIR is None:
            output = g.serialize(None, format=args.TO)
            verbose(" - output:")
            print(output)
        # if an output directory was provided, but it doesn't exist, then exit the script
        elif not os.path.exists(args.OUTPUTDIR):
            sys.exit(f"ERROR: Output dir '{args.OUTPUTDIR}' was not found!")
        # if the output directory was given and it exists, then figure out the output filename
        # and write the output to disk
        else:
            head, tail = os.path.split(input_file)
            verbose(f" - head, tail: {head}, {tail}")
            output_abs_path = get_output_abs_path(verbose, args, input_file_or_dir, head)
            output_file_name = os.path.splitext(tail)[0] + output_extension
            output_abs_file_name = os.path.join(output_abs_path, output_file_name)

            verbose(f" - output filename: '{output_abs_file_name}'")

            # for safety, check that we're not overwriting the input file
            if output_abs_file_name == os.path.abspath(input_file):
                sys.exit(f"ERROR: Input file '{output_abs_file_name}' is the same as output file!")
            else:
                verbose(" - this file is different from the input filename")

            # if the output file exists already and the "force" flag is not set,
            # then ask for permission to overwrite the file
            skip_this_file = False
            if not args.force and os.path.exists(output_abs_file_name):
                yes_or_no = input(f"Overwrite {output_abs_file_name}? (y/n): ")
                if yes_or_no.lower() not in ["y", "yes"]:
                    skip_this_file = True

            if skip_this_file:
                verbose(" - this file will be skipped")
            else:
                dir_name = os.path.dirname(output_abs_file_name)
                if not os.path.exists(dir_name):
                    if args.simulate:
                        print(f"Simulation: this directory tree would be written: {dir_name}")
                    else:
                        verbose(f" - Now creating {dir_name} since it does not exist yet")
                        os.makedirs(dir_name)

                if args.simulate:
                    print(f"Simulation: this file would be written: {output_abs_file_name}")
                else:
                    g.serialize(output_abs_file_name, format=args.TO)
                    verbose(f" - file '{output_abs_file_name}' has been written")

def main():
    args = parse_args()

    # a simple function to log verbose info
    def verbose(msg):
        if args.verbose:
            print(msg)

    verbose(f" - Input format: {args.FROM}")
    verbose(f" - Output format: {args.TO}")

    # find out which extensions we should match
    if args.FROM_EXT:
        input_extensions = args.FROM_EXT
    else:
        input_extensions = INPUT_FORMAT_TO_EXTENSIONS[args.FROM]

    verbose(f" - Input extensions: {input_extensions}")

    # find out which output extension we should write
    if args.TO_EXT:
        output_extension = args.TO_EXT
    else:
        output_extension = OUTPUT_FORMAT_TO_EXTENSION[args.TO]

    verbose(f" - Output extension: '{output_extension}'")

    # process each input file sequentially:
    for input_file_or_dir in args.INPUT:

        verbose(f"Now processing input file or directory '{input_file_or_dir}'")

        # check if the file exists, and if it's a directory or a file
        is_dir = False
        if os.path.exists(input_file_or_dir):
            if os.path.isdir(input_file_or_dir):
                verbose(f" - '{input_file_or_dir}' exists and is a directory")
                input_file_or_dir = os.path.abspath(input_file_or_dir)
                is_dir = True
            else:
                verbose(f" - '{input_file_or_dir}' exists and is a file")
        else:
            sys.exit(f"ERROR: Input file '{input_file_or_dir}' was not found!")

        input_files = []

        if is_dir:
            verbose(f" - Now walking the directory (recursive = {args.recursive}):")
            for root, dirnames, filenames in os.walk(input_file_or_dir):
                verbose(f"   * Finding files in '{root}'")
                for extension in input_extensions:
                    for filename in fnmatch.filter(filenames, f"*{extension}"):
                        verbose(f"     -> found '{filename}'")
                        input_files.append(os.path.join(root, filename))
                if not args.recursive:
                    break

        else:
            input_files.append(input_file_or_dir)

        process_input_files(verbose, args, input_file_or_dir, output_extension, input_files)

if __name__ == "__main__":
    main()
