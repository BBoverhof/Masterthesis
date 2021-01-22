# 5. Data
This subsection of the repository contains data in its original `.xdf` file extension. Currently, only the data of participant `bc10` is provided, for there is not enough available space on the digital drive to upload all data. Since files with `.xdf` extensions can't be directly read into Python, this subsection contains scripts to read and write the data in a usable extension.

For an extensive elaboration on the approach, please consult the research manuscript [manuscript.pdf](https://github.com/BartJanBoverhof/Masterthesis/tree/main/1.latex_manuscript).

---

![Status](https://img.shields.io/static/v1?label=Code+Status&message=Unfinished+and+Unexcecutable&color=red) 

---

This subsection of the repository contains the following objects: 
* `bc10` folder: Data of particpant `bc10` in `.xdf` format.
* `data_writer`: Script that provides a function to read and write the data in a usable extension (`.TFRecord`).

In addition to the earlier listed software, the following packages are utilized:  
- `pyxdf`: package for reading .xdf files.