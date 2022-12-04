import os
import argparse
import itertools
from collections import OrderedDict
from multiprocessing import Pool
from PyPDF2 import PdfFileReader, PdfFileWriter


class Logger(object):
    """logger to print at certain line"""

    def __init__(self, num: int):
        """init logger
        @param num: number of lines
        """
        self.num = num
        print("\033[K\n" * num, end="")
        print("\033[?25l", end="", flush=True)

    def log(self, line: int, msg: str):
        """log message
        @param line: line number to print
        @param msg: message
        """
        line = self.num - line
        print(f"\033[{line}F", end="")
        print("\033[2K", end="")
        print(msg, end="")
        print(f"\033[{line}E", end="", flush=True)

    def __del__(self):
        """destructor"""
        print("\033[?25h", end="", flush=True)


def parse_args():
    """parse arguments
    @return: arguments
    """
    parser = argparse.ArgumentParser(description="Organize your files")
    # directory to organize
    parser.add_argument("-d", "--directory", type=str, required=True, help="Directory to organize")
    # output directory
    parser.add_argument("-o", "--output", type=str, required=True, help="Output directory")
    args = parser.parse_args()
    # if directory does not exist, exit
    if not os.path.exists(args.directory):
        exit("Directory does not exist")
    # if output directory does not exist, create it
    if not os.path.exists(args.output):
        os.makedirs(args.output)
        print(f"Created output directory: {args.output}")
    return args


def get_real_page_num(pdf: PdfFileReader, page_num: int) -> str:
    """get real page number
    @param pdf: pdf file reader
    @param page_num: page number
    @return: real page number
    """
    page = pdf.getPage(page_num)
    text = page.extractText()
    page_num = text.splitlines()[-1].split("/")[0]
    return page_num


def organize_file(args: tuple):
    """organize file
    @param args: arguments (line, file, directory, output)
    """
    line, file_name, directory, output = args
    file_path = os.path.join(directory, file_name)
    spinner = itertools.cycle("\u280b\u2819\u2839\u2838\u283c\u2834\u2836\u2837\u2827\u280f")  # spinner
    with open(file_path, "rb") as f:
        pdf = PdfFileReader(f)
        writer = PdfFileWriter()
        num_pages = pdf.getNumPages()
        pages: OrderedDict[str, int] = OrderedDict()
        for i in range(num_pages):  # loop through pages
            logger.log(line, f"{next(spinner)} {file_name}: {i + 1}/{num_pages}")
            page_num = get_real_page_num(pdf, i)  # get real page number
            pages[page_num] = i  # update page at real page number
        for page_num, i in pages.items():
            writer.addPage(pdf.getPage(i))  # add page to writer
        output_file_name = os.path.join(output, file_name)
        with open(output_file_name, "wb") as f:
            writer.write(f)  # write to file
        new_num_pages = writer.getNumPages()
        logger.log(line, f"\u2713 {file_name}: {num_pages} -> {new_num_pages} pages (\u2193 {(num_pages - new_num_pages) / num_pages * 100:.2f}%)")


def init_pool(_logger: Logger):
    """init pool
    @param _logger: logger
    """
    global logger
    logger = _logger


if __name__ == "__main__":
    args = parse_args()
    # find all pdf files in directory
    files = [f for f in os.listdir(args.directory) if os.path.isfile(os.path.join(args.directory, f)) and f.endswith(".pdf")]
    files_num = len(files)
    logger = Logger(files_num)  # init logger
    with Pool(files_num, initializer=init_pool, initargs=(logger,)) as p:  # init pool to run in parallel
        p.map(organize_file, [(i, f, args.directory, args.output) for i, f in enumerate(sorted(files))])
