MEXDEX modules
==============

This repository contains the Python modules for

-   Metrics Extraction (**MEX**) via Paraview. The test files, examples and documentation is in `Metrics Extraction` repository: <https://github.com/parallelworks/MetricExtraction.git>
-   Modules for utilizing Design Explorer (**DEX**) which is an open source tool for visualizing results from multi-dimensional parametric studies (<http://tt-acm.github.io/DesignExplorer/>). The test files, examples and documentation is the `Design Explorer Modules` repository: <https://github.com/parallelworks/designExplorerModules.git>

In addition, the following python tools are included:

-   `createInputFile.py` : Creates an input file based on a given template file. The tagged values in the template file will be replaced using a list of variables and their values.
-   `data_IO.py` : A python module with functions for handling data input/output (mostly from data files)
-   `plot_csv.py` : Creates plots from a csv file
-   `prepinputs.py` : Generates a file which lists the parameter names and values for each simulation case per line by expanding the parameters in a provide `params.run` file. In addition, separate (templated) input files can also be generated if a path is provided.
-   `writeParams2xml.py` : This script creates the xml file for a PW workflow using a sample parameter file. The names of the input sections can also be specified in the parameter file.

Usage
-----

-   Details and examples for using the `extract.py` (for Metrics Extraction) is provided in [Metrics Extraction repository](https://github.com/parallelworks/MetricExtraction.git)
-   Details and examples for using the `writeDesignExplorerCsv.py` (for Design Explorer) is provided in [Design Explorer Modules Repository](https://github.com/parallelworks/designExplorerModules.git)
-   For usage of the remaining python tools listed above, please refer to the help/usage interface of each script by running under python with the option `-h`. For example,

    ``` example
    python writeParams2xml.py -h
    ```

License
-------

This project is licensed under the MIT License - see the [file:LICENSE.md](LICENSE.md) file for details
