import xlrd
from xlrd import open_workbook
import numpy as np
import pandas as pd
import re


def read_excel_with_formatting(file_path,
                               sheet_name,
                               skiprows=0,
                               competency_col=2):
    #  adopted from https://stackoverflow.com/a/7991458/3662899
    wb = open_workbook(file_path, formatting_info=True)
    sheet = wb.sheet_by_name(sheet_name)
    font = wb.font_list

    value_arr = ['']*sheet.nrows
    indent = [0]*sheet.nrows
    numeric = ['']*sheet.nrows
    bgcol = [0]*sheet.nrows
    weight = [0]*sheet.nrows

    tags = [""]*sheet.nrows
    #  cycle through all cells to get colors
    for idx, row in enumerate(range(sheet.nrows)):
        if idx < skiprows:
            continue

        for column in range(sheet.ncols):
            cell = sheet.cell(row, column)
            if xlrd.XL_CELL_EMPTY != cell.ctype:
                value = str(cell.value)
                tag = ''

                if column == competency_col:
                    fmt = wb.xf_list[cell.xf_index]
                    bgcol[row] = fmt.background.background_colour_index
                    weight[row] = font[fmt.font_index].weight
                    indent[row] = fmt.alignment.indent_level
                    match = re.match(r'^([\d\.]*)(.*)', value)
                    if match.lastindex >= 2:
                        value_arr[row] = match.groups()[1].strip()
                    if 0 != match.lastindex:
                        tag = match.groups()[0]
                        numeric[row] = match.groups()[0]

                prefix = ', '
                if not tags[row].strip():
                    # first tag starts with a value, not a comma
                    prefix = ''
                if not tag:
                    tag = re.match('^([\d\.]*)',
                                   value).group()
                # some times the numeric tag is repeated in another column
                # (such as the comptency column) so we do a quick check to avoid
                # repeating numeric values
                if tag.strip() and tags[row] != tag:
                    tags[row] += prefix + tag

    df = pd.DataFrame({"background": bgcol,
                       "weight": weight,
                       "indent": indent,
                       "numeric": numeric,
                       "value": value_arr,
                       "tags": tags
                       })
    df.replace('', np.nan, inplace=True)
    df.dropna(inplace=True, subset=['value'])
    return df


def induce_tags(df, include_section=True):
    '''
    Assuming top level tags we uniquely tag other columns
    by both forward filling to perserve the top level hierarchy
    and make each row unique appending the row number.

    It is possible to do hierarchical tagging by inspecting the
    weight and indent level but this is good enough for now.
    ACE might request hierarchical tagging though.
    '''
    ret = df.replace('', np.nan)
    ret.tags.fillna(method='ffill', inplace=True)

    ret.tags =\
        [', row='.join(elem) for elem in zip(ret.tags.astype(str),
                                             (ret.index+1).astype(str))]
    ret.dropna(subset=['value'], inplace=True)

    if include_section:
        ret.tags = 'section ' + ret.tags
    return ret
