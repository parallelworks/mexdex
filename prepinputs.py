import paramUtils
import argparse
import data_IO
from string import Template

parser = argparse.ArgumentParser(
    description='Generate the caseList file which lists the parameter names and values '
                'for each simulation case per line by expanding the parameters in the'
                'sweep.run file. In addition, separate (templated) input files can also '
                'be generated if a path is provided.')

parser.add_argument("sweepRunFile",
                    help="The sweepRunFile file contains parameter names and their values.")

parser.add_argument("caseListFile",
                    help="The output file of this function. The address of the file listing "
                         "the parameter names and values for each simulation case per line.")

parser.add_argument("--SR_valueDelimiter", default='_',
                    help='The delimiter to separate multiple values in a list in '
                         '<sweepRunFile> (default:"_")')

parser.add_argument("--SR_paramValueDelimiter", default=';',
                    help='The delimiter between a parameter name and its value in '
                         '<sweepRunFile> (default:";")')

parser.add_argument("--SR_paramsDelimiter", default='|',
                    help='The delimiter to separate parameter/value pairs from each other in '
                         '<sweepRunFile> (default:"|")')

parser.add_argument("--withParamTag", dest='withParamTag', action='store_true',
                    help='If set, a tag can be specified between the parameter name and '
                         'its value (delimited by SR_namesDelimiter). This is the default.')

parser.add_argument("--noParamTag", dest='withParamTag', action='store_false',
                    help='If set, no tag is expected between the parameter name and its value.')

parser.add_argument("--CL_paramValueDelimiter", default=',',
                    help='The delimiter between a parameter name and its value in '
                         '<casesListFile> (default:",")')


parser.add_argument("--separateParamFilesPath", default="",
                    help='The path for writing separate parameter files for each case.'
                         'For example, if set to "paramFiles/case_{:d}.in", in addition '
                         'to <casesListFile>, inputs for each case would be written into'
                         'single files of "paramFiles/case_0.in", "paramFiles/case_1.in"'
                         'and ... (default is empty :""/no separate input file would be'
                         'generated).')

parser.add_argument("--separateParamFileTemplate", default="",
                    help='The path for a template file for writing separate parameter '
                         'files for each case. The case parameters will be substituted '
                         'in the template file with the paramter values for each case.'
                         'The substitutions can be specified by using the '
                         'parameter names as identifiers. Identifiers must match the '
                         'parameter names in the <sweepRunFile>. For example'
                         'to substitute param1 with its value use "$param1" or '
                         '"${param1} in the template file where "$" is the '
                         'delimiter for substitution. '
                         '(default is empty :"" in which case the separate '
                         'input files would be simply written based on the '
                         'given/default delimiters.)')

parser.add_argument("--SepFile_paramValueDelimiter", default='\n',
                    help='The delimiter between a parameter name and its value in '
                         '<seperateParamFiles> (default:"\n")')
parser.add_argument("--SepFile_paramsDelimiter", default='\n',
                    help='The delimiter to separate parameter/value pairs from each '
                         'other in <seperateParamFiles> (default:"\n")')

parser.set_defaults(withParamTag=True)


args = parser.parse_args()
casesListFile = args.caseListFile
paramsFile = args.sweepRunFile
SR_valsdelimiter = data_IO.correctDelimiterInputStrs(args.SR_valueDelimiter)
SR_paramsDelimiter = data_IO.correctDelimiterInputStrs(args.SR_paramsDelimiter)
SR_withParamTag = args.withParamTag
SR_paramValueDelimiter = data_IO.correctDelimiterInputStrs(args.SR_paramValueDelimiter)
CL_paramValueDelimiter = data_IO.correctDelimiterInputStrs(args.CL_paramValueDelimiter)
SepFile_paramValueDelimiter = data_IO.correctDelimiterInputStrs(
    args.SepFile_paramValueDelimiter)
SepFile_paramsDelimiter = data_IO.correctDelimiterInputStrs(
    args.SepFile_paramsDelimiter)
separateParamFilesPath = args.separateParamFilesPath
separateParamFileTemplate = args.separateParamFileTemplate

cases = paramUtils.readCases(paramsFile,
                             valsdelimiter=SR_valsdelimiter,
                             paramsdelimiter=SR_paramsDelimiter,
                             withParamType=SR_withParamTag,
                             namesdelimiter=SR_paramValueDelimiter)[0]

print("Generated "+str(len(cases))+" Cases")

caselist = paramUtils.generate_caselist(cases, pnameValDelimiter=CL_paramValueDelimiter)

casel = "\n".join(caselist)

f = data_IO.open_file(casesListFile, "w")
f.write(casel)
f.close()

# Write input paramters into separate files:
if separateParamFilesPath:

    # Use a template for generating the separate files
    if separateParamFileTemplate:
        ftemp = data_IO.open_file(separateParamFileTemplate)
        template_output = Template(ftemp.read())
        ftemp.close()

        for i, case in enumerate(cases):
            caseDict = paramUtils.convertListOfDicts2Dict(case)
            fsimParm = data_IO.open_file(separateParamFilesPath.format(i), 'w')
            fsimParm.write(template_output.substitute(caseDict))
            fsimParm.close()
    else:
        caseslist = paramUtils.generate_caselist(
            cases,
            pnameValDelimiter=SepFile_paramValueDelimiter,
            paramValPairDelimiter=SepFile_paramsDelimiter)

        for i, case in enumerate(caseslist):
            fsimParm = data_IO.open_file(separateParamFilesPath.format(i),'w')
            fsimParm.write(case)
            fsimParm.close()
