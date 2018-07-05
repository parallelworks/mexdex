import argparse
import data_IO
from string import Template


def parse_inputs():
    parser = argparse.ArgumentParser(
        description='Create an input file based on a given template file. '
                    'The tagged values in the template file will be replaced '
                    'using a list of variables and their values.')

    parser.add_argument("templateFile",
                        help='The path for a template file for writing separate '
                             'parameter files for each case. The case parameters will be '
                             'substituted in the template file with the paramter values '
                             'for each case.'
                             'The substitutions can be specified by using the '
                             'parameter names as identifiers. Identifiers must match the '
                             'parameter names in the <sweepRunFile>. For example '
                             'to substitute param1 with its value use "$param1" or '
                             '"${param1} in the template file where "$" is the '
                             'delimiter for substitution. ')

    parser.add_argument("inputFile",
                        help='The path for writing input file.')

    parser.add_argument("paramValueList",
                        help='List of parameter names and their values. '
                             'For example "a=1,b=3.0"')

    args = parser.parse_args()
    template_file = args.templateFile
    input_file = args.inputFile
    param_value_list = args.paramValueList
    return template_file, input_file, param_value_list


def main():
    template_file, input_file, param_value_list = parse_inputs()
    # create a dictionary from parameter names and their values
    case_dict = dict(item.split("=") for item in param_value_list.split(","))

    # read the template file
    ftemp = data_IO.open_file(template_file)
    template_output = Template(ftemp.read())
    ftemp.close()

    # write the input file
    fsimParm = data_IO.open_file(input_file, 'w')
    fsimParm.write(template_output.substitute(case_dict))
    fsimParm.close()


if __name__ == "__main__":
    main()
