#!/usr/bin/env python3
"""
Project      : rdfconvert
Description  : Converts files and whole directory trees from one RDF serialization into another.
Author       : Wim Pessemier
Contact      : w**.p********@ster.kuleuven.be (replace *)
Organization : Institute of Astronomy, KU Leuven
SPDX-FileCopyrightText: Wim Pessemier <w**.p********@ster.kuleuven.be>
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
    for inputFormat, extensions in INPUT_FORMAT_TO_EXTENSIONS.items():
        s += f" - {inputFormat.ljust(19)} : {extensions}\n"
    s += "\n"
    s += "Default extension for OUTPUT format:\n"
    for ouptutFormat, extension in OUTPUT_FORMAT_TO_EXTENSION.items():
        s += f" - {ouptutFormat.ljust(10)} : '{extension}'\n"
    return s

if __name__ == "__main__":

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
                        help="Verbosely print some debugging info.")

    args = parser.parse_args()

    # a simple function to log verbose info
    def VERBOSE(msg):
        if args.verbose:
            print(msg)

    # process each input file sequentially:
    for inputFileOrDir in args.INPUT:

        VERBOSE(f"Now processing input file or directory '{inputFileOrDir}'")

        # check if the file exists, and if it's a directory or a file
        isdir = False
        if os.path.exists(inputFileOrDir):
            if os.path.isdir(inputFileOrDir):
                VERBOSE(f" - '{inputFileOrDir}' exists and is a directory")
                inputFileOrDir = os.path.abspath(inputFileOrDir)
                isdir = True
            else:
                VERBOSE(f" - '{inputFileOrDir}' exists and is a file")
        else:
            sys.exit(f"!!! ERROR: Input file '{inputFileOrDir}' was not found !!!")

        VERBOSE(f" - Input format: {args.FROM}")
        VERBOSE(f" - Output format: {args.TO}")

        # find out which extensions we should match
        if args.FROM_EXT:
            inputExtensions = args.FROM_EXT
        else:
            inputExtensions = INPUT_FORMAT_TO_EXTENSIONS[args.FROM]

        VERBOSE(f" - Input extensions: {inputExtensions}")

        # find out which output extension we should write
        if args.TO_EXT:
            outputExtension = args.TO_EXT
        else:
            outputExtension = OUTPUT_FORMAT_TO_EXTENSION[args.TO]

        VERBOSE(f" - Output extension: '{outputExtension}'")

        inputFiles = []

        if isdir:
            VERBOSE(f" - Now walking the directory (recursive = {args.recursive}):")
            for root, dirnames, filenames in os.walk(inputFileOrDir):
                VERBOSE(f"   * Finding files in '{root}'")
                for extension in inputExtensions:
                    for filename in fnmatch.filter(filenames, f"*{extension}"):
                        VERBOSE(f"     -> found '{filename}'")
                        inputFiles.append(os.path.join(root, filename))
                if not args.recursive:
                    break

        else:
            inputFiles.append(inputFileOrDir)

        # create the graph, and parse the input files

        for inputFile in inputFiles:

            g = Graph()
            g.parse(inputFile, format=args.FROM)

            VERBOSE(" - the graph was parsed successfully")

            # if no output directory is specified, just print the output to the stdout
            if args.OUTPUTDIR is None:
                output = g.serialize(None, format=args.TO)
                VERBOSE(" - output:")
                print(output)
            # if an output directory was provided, but it doesn't exist, then exit the script
            elif not os.path.exists(args.OUTPUTDIR):
                sys.exit(f"!!! ERROR: Output dir '{args.OUTPUTDIR}' was not found !!!")
            # if the output directory was given and it exists, then figure out the output filename
            # and write the output to disk
            else:
                head, tail = os.path.split(inputFile)
                VERBOSE(f" - head, tail: {head}, {tail}")
                if args.no_tree:
                    outputAbsPath = os.path.abspath(args.OUTPUTDIR)
                else:
                    # remove the common prefix from the head and the input directory
                    # (otherwise the given input path will also be added to the output path)
                    commonPrefix = os.path.commonprefix([head, inputFileOrDir])
                    VERBOSE(f" - inputFileOrDir: {inputFileOrDir}")
                    VERBOSE(f" - common prefix: {commonPrefix}")
                    headWithoutCommonPrefix = head[len(commonPrefix)+1:]
                    VERBOSE(f" - head without common prefix: {headWithoutCommonPrefix}")
                    outputAbsPath = os.path.join(os.path.abspath(args.OUTPUTDIR),
                                                 headWithoutCommonPrefix)
                    VERBOSE(f" - output absolute path: {outputAbsPath}")
                outputFileName = os.path.splitext(tail)[0] + outputExtension
                outputAbsFileName = os.path.join(outputAbsPath, outputFileName)

                VERBOSE(f" - output filename: '{outputAbsFileName}'")

                # for safety, check that we're not overwriting the input file
                if outputAbsFileName == os.path.abspath(inputFile):
                    sys.exit(f"!!! ERROR: Input file '{outputAbsFileName}' is the same as output file !!!")
                else:
                    VERBOSE(" - this file is different from the input filename")


                # if the output file exists already and the "force" flag is not set,
                # then ask for permission to overwrite the file
                skipThisFile = False
                if not args.force and os.path.exists(outputAbsFileName):
                    yesOrNo = raw_input(f"Overwrite {outputAbsFileName}? (y/n): ")
                    if yesOrNo.lower() not in ["y", "yes"]:
                        skipThisFile = True

                if skipThisFile:
                    VERBOSE(" - this file will be skipped")
                else:
                    dirName = os.path.dirname(outputAbsFileName)
                    if not os.path.exists(dirName):
                        if args.simulate:
                            print(f"Simulation: this directory tree would be written: {dirName}")
                        else:
                            VERBOSE(f" - Now creating {dirName} since it does not exist yet")
                            os.makedirs(dirName)

                    if args.simulate:
                        print(f"Simulation: this file would be written: {outputAbsFileName}")
                    else:
                        g.serialize(outputAbsFileName, format=args.TO)
                        VERBOSE(f" - file '{outputAbsFileName}' has been written")
