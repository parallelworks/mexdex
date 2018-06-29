import argparse
import pandas as pd
import matplotlib as mpl
# Force matplotlib to not use any Xwindows backend.
mpl.use('Agg')
import matplotlib.pyplot as plt
import data_IO


def parse_inputs():
    parser = argparse.ArgumentParser(
        description='Create plots from a csv file')

    parser.add_argument("csv_file",
                        help='The address of the input csv data file')

    parser.add_argument("png_file",
                        help='The address of the output png file')

    parser.add_argument("--header_lines", default=[0], type=int, nargs='+',
                        help='The number of header lines in the <csv_file>. '
                             'Multiple numbers could also be specified, e.g, 0 1 2.'
                             'For files without headers input -1. '
                             '(default:0 which would use the first line of the csv_file '
                             'for header names)')

    parser.add_argument("--header_names", default='',
                        help='A comma delimited string that is used as the header of '
                             'the csv as columns names. For example: '
                             '"time (s), Temperature (C), Pressure (Pa)".'
                             'Even if using the option y_columns_index, the names would'
                             'correspond to all the columns.'
                             '(default:"" which would work if the csv file has a header)')

    parser.add_argument("--x_column_index", default='0', type=int,
                        help='The column that would be used as the x axis data. '
                             'If set to -1, the data would be plotted as a function of '
                             'their index (i.e., x=[1,2,...])'
                             '(default:0 which refers to the first column on the csv '
                             'file)')

    parser.add_argument("--y_column_index", default='1:',
                        help='The column(s) that would be used as the y axis data. '
                             'Multiple columns could be specified in two ways:'
                             '1) Multiple values delimited by ","' 
                             '2) Entering a range of integers by following '
                             'python slice convention for getting subsections'
                             ' of lists, e.g., ":", or "4:". ' 
                             '(default:"1:" which refers to the 2nd to the last columns '
                             'of the csv file)')

    parser.add_argument("--y_label", default='',
                        help='The y axis label' 
                             '(default:"" which would result in no labels if plotting'
                             'more than 1 column)')

    parser.add_argument("--x_label", default='',
                        help='The x axis label ' 
                        '(default:"" which would result in setting to the header of '
                        'the x column data (or "index" if using indices for x axis).')

    args = parser.parse_args()
    return args


def get_x_label(df, args):
    x_label_text = args.x_label
    if not x_label_text:
        if args.x_column_index == -1:
            x_label = "Index"
        else:
            x_label = df.columns.values[args.x_column_index]
    else:
        x_label = x_label_text
    return x_label


def plot_data(df, x_data, y_data, args):
    fig = plt.figure()
    n_lines = len(y_data.columns)
    for iline in range(n_lines):
        plt.plot(x_data, y_data.iloc[:, iline])

    if n_lines == 1:
        if not args.y_label:
            plt.ylabel(y_data.columns.values[0])
        else:
            plt.ylabel(args.y_label)

    else:    # Add column names as legend
        plt.ylabel(args.y_label)
        plt.legend(df.columns.values[get_desired_column_list(len(df.columns),
                                                             args.y_column_index)])

    plt.xlabel(get_x_label(df, args))
    plt.grid(True)
    axes = plt.gca()
    axes.set_xlim([0, max(x_data)])
    fig.savefig(args.png_file, bbox_inches='tight')


def get_header_names(given_names):
    if not given_names:
        header_names = None
    else:
        header_names = given_names.split(',')

    return header_names


def get_header_lines(header_lines_list):
    if len(header_lines_list) == 1:
        # If given a list, Pandas would assume multi line header line
        header_lines = header_lines_list[0]
        if header_lines == -1:
            header_lines = None
        return header_lines
    else:
        return header_lines_list


def read_csv_file(args):

    header_names = get_header_names(args.header_names)
    header_lines = get_header_lines(args.header_lines)

    df = pd.read_csv(args.csv_file, names=header_names, header=header_lines)
    list(df.columns.values)

    return df


def get_x_data(df, x_column_index):
    if x_column_index == -1:
        x_data = df.index.values
    else:
        x_data = df.iloc[:, x_column_index]
    return x_data


def get_desired_column_list(total_col_number, column_list_text):
    desired_columns_list = data_IO.str_2_int_list(column_list_text)
    if isinstance(desired_columns_list, slice):
        all_cols = range(total_col_number)
        desired_columns_list = all_cols[desired_columns_list]
    return desired_columns_list


def get_y_data(df, y_column_index_text):

    desired_columns_list = get_desired_column_list(len(df.columns), y_column_index_text)
    y_data = df.iloc[:, desired_columns_list]
    return y_data


def main():
    args = parse_inputs()
    df = read_csv_file(args)
    x_data = get_x_data(df, args.x_column_index)
    y_data = get_y_data(df, args.y_column_index)
    plot_data(df, x_data, y_data, args)


if __name__ == "__main__":
    main()
