MEXDEX modules
==============

This repository contains the Python modules for

-   Metrics Extraction (**MEX**) via Paraview. The test files, examples and documentation is in `MetricsExtraction` repository: <https://github.com/parallelworks/MetricExtraction.git>
-   Modules for utilizing Design Explorer (**DEX**) which is an open source tool for visualizing results from multi-dimensional parametric studies (<http://tt-acm.github.io/DesignExplorer/>). The test files, examples and documentation is the `MetricsExtraction` repository: <https://github.com/parallelworks/designExplorerModules.git>

Usage
-----

-   To add this repository as a git submodule run:

    ``` example
    git submodule add https://github.com/parallelworks/mexdex.git  
    ```

-   To clone your repository that has the `mexdex` repository as a submodule, run:

    ``` example
    git clone --recursive <project url>
    ```
## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
