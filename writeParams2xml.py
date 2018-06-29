import argparse
import json
import paramUtils


def parse_args():
    parser = argparse.ArgumentParser(
        description='''This script creates the xml file for PW a workflow using a 
        sample parameter file. The names of the input sections can also be specified 
        in the parameter file. For example, 
        "param1;;0|param2;sec1;0|param3;sec1;2|" 
        would create an xml file with two sections ("sec1" and "sec2")           
        ''')

    parser.add_argument("parameter_file",
                        help='Path of the input parameter file')

    parser.add_argument("xml_file",
                        help='Path of the output xml file')

    parser.add_argument("--withParamTag", dest='withParamTag', action='store_true',
                        help='If set, a tag can be specified between the parameter name '
                             'and its value (delimited by paramValueDelimiter). '
                             'This is the default. The tag will be used to add '
                             'parameters under sections with the same tag. parameters '
                             'without any tags would be added directly under the "inputs"'
                             'element of the xml. '
                             'For example, '
                             '"timestep;runtimeParameters;0.1" adds an input parameter '
                             'with the name "timestep", under the section of '
                             '"Runtime Parameters" and sets the default value to 0.1. '
                             'To add a parameter directly under the "inputs" element of '
                             'the xml form (i.e., without adding it under a section) '
                             'the section can be left empty for some parameters. ')

    parser.add_argument("--noParamTag", dest='withParamTag', action='store_false',
                        help='If set, no tag is expected between a parameter '
                             'name and its value. All the parameters will be added '
                             'directly under the "inputs" element of '
                             'the xml form (i.e., without adding them under sections). ')

    parser.add_argument("--paramValueDelimiter", default=';',
                        help='The delimiter between a parameter name, its '
                             'section/type name and its value in '
                             '<parameter_file>. For example, '
                             '"timestep;runtimeParameters;0.1" adds an input parameter '
                             'with the name "timestep", under the section of '
                             '"Runtime Parameters" and sets the default value to 0.1. '
                             'To add a parameter directly under the "inputs" element of '
                             'the xml form (i.e., without adding it under a section) '
                             'the section can be left empty (e.g., "timestep;;0.1"). '
                             'To set '
                             'delimiters that have a backslash ("\\") in them '
                             '(e.g., "\\n"), '
                             'set the delimiter with $\'xx\' format. For example, '
                             'to set the delimiter to "\\n", '
                             'enter it as $\'\\n\' when calling via bash '
                             '(default:";")')

    parser.add_argument("--paramsDelimiter", default='\n',
                        help='The delimiter to separate parameter/value pairs from each '
                             'other in <parameter_file>. For example, '
                             '"paramA;section1;0|paramB;section1;A B C|" adds two '
                             'parameters ("paramA" and "paramB") to the input form '
                             'under the section "section1". To set '
                             'delimiters that have a backslash ("\\") in them '
                             '(e.g., "\\n"), '
                             'set the delimiter with $\'xx\' format. For example, '
                             'to set the delimiter to "\\n", '
                             'enter it as $\'\\n\' when calling via bash '
                             '(default:"|")')

    parser.set_defaults(withParamTag=True)
    args = parser.parse_args()
    return args


def main():

    args = parse_args()
    params_file = args.parameter_file
    xml_file = args.xml_file

    cases, _, param_types = paramUtils.readCases(params_file,
                                                 withParamType=args.withParamTag,
                                                 namesdelimiter=args.paramValueDelimiter,
                                                 paramsdelimiter=args.paramsDelimiter)

    print("Parameters/Sections:")
    print(json.dumps(param_types, indent=4))
    print("")

    paramUtils.writeXMLPWfile(cases[0], param_types, xml_file)


if __name__ == '__main__':
    main()
