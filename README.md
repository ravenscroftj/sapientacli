# Sapienta CLI
[![PyPi Release](https://img.shields.io/pypi/v/sapientacli.svg)](https://pypi.org/project/sapientacli/)
[![License: GPL v3+](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT)

This repository provides a super lightweight CLI wrapper around the [SAPIENTA paper extraction API](https://sapienta.pappro.org.uk/)

![SAPIENTA CLI in action](https://raw.githubusercontent.com/ravenscroftj/sapientacli/main/assets/screenrecording.gif)

## Usage

The easiest way to use this tool is to install via pip and run at the command line

```
pip install sapientacli

sapientacli ./some/scientific/paper.pdf
```

### Supported files

Sapienta supports annotation of scientific papers in PDF format via University of Manchester's [PDFX](http://pdfx.cs.man.ac.uk/) conversion service. 
You can also upload any [JATS](http://jats.nlm.nih.gov/publishing/1.1d3/JATS-journalpublishing1.dtd) (i.e. documents from [PloS](https://plos.org/) and [Pubmed Central](https://www.ncbi.nlm.nih.gov/pmc/)) or [SciXML](https://sourceforge.net/projects/scixml/) compatible XML document.
