# BAMKeys Automatic Documentation #

This Python3 program builds the BAMKeys documentation with information parsed from the `bio` script and user generated 
information stored in markdown files for each of the keys. The markdown files used to store the user generated
documentation for each key are stored in the `details` folder. If a key is added to bio, the file is automatically 
generated and stored in the correct directory in the `details` folder based on the first letter of the key.

There are three ways to use this program:
  * Generate markdown files for new keys
  * Generate a PDF of the documentation
  * Generate a single markdown file with all of the information that is used to generate a PDF

* generate
	- Generates new files for keys that are added to the `bio` script
	- **Optional:** Commits those new files to svn or git
* markdown
	- Creates a single markdown file of all the information for use in 
	  other applications.
* pdf
	- Generates a PDF by parsing bio, combining the given information for each
	  key and section title, and a list of all of the keys
	- **Optional:** upload document to Google Drive

# Requirements #

[Python 3](https://www.python.org/) and pip are required for the script to run.

## Linux ##
Pandoc and TexLive need to be installed to build the documentation

### Ubuntu 16.04 ###

```bash
sudo add-apt-repository ppa:jonathonf/texlive-2018
sudo apt install -y texlive texlive-xetex  texlive-math-extra fonts-roboto
```

### Ubuntu 18.04 ###

```bash
curl -LO https://github.com/jgm/pandoc/releases/download/2.2.2.1/pandoc-2.2.2.1-1-amd64.deb
sudo dpkg -i pandoc-2.2.2.1-1-amd64.deb
rm pandoc-2.2.2.1-1-amd64.deb
sudo apt install -y texlive texlive-xetex  texlive-science texlive-science-doc fonts-roboto
```

### Install roboto-mono on all platforms ###
```bash
mkdir ${HOME}/.fonts
cd ${HOME}/.fonts
curl -L -O https://www.wfonts.com/download/data/2016/05/18/roboto-mono/roboto-mono.zip
unzip roboto-mono.zip
rm roboto-mono.zip
cd ${HOME}
fc-cache -f
```

## macOS ##

To install everything needed, you should install the [homebrew](https://brew.sh/) package manager. 

```bash
brew install pandoc
brew cask install mactex
```

## Windows ##

Go to the [pandoc releases](http://pandoc.org/installing.html) page and download 
and install the latest release. Do the same for 
[TeX Live](https://tug.org/texlive/windows.html). 

## Fonts for macOS and Windows ##

These need to be installed using the built in tools in either macOS or Windows.

* [Roboto](https://fonts.google.com/specimen/Roboto)
* [Roboto Mono](https://fonts.google.com/specimen/Roboto+Mono)

# Usage #

For any of the operations in this scipt, the path for `bio` needs to be 
passed in using the `-i` or `--input` flag. Parsing `bio` for the necessary
information is required for this script to funciton. 

The `-o` or `--output` will set the location of the file that will be generated 
with this script using either the `markdown` or `pdf` command.

To set the version control system for the `generate` or `pdf` section, use the `-s`
flag for Subversion and `-g` for Git. 

## Generate files ##

If you want to generate new files for the `details` folder, you can use the `generate` sub program.

```bash
python3 generate_documentation.py generate [-h] -i INPUT [-s | -g] [-v] [--DEBUG]
```

Argument                | Description
:----                   | :----
-i INPUT, --input INPUT | The input `bio` file used for generating the new files
-s, --svn               | Optional: Add the new files in `details` to SVN repository
-g, --git               | Optional: Add the new files in `details` to git repository

## Generate Markdown File ##

If you want to generate only a markdown file for use with other programs, you can use the `markdown` subprogram.

```bash
python3 generate_documentation.py markdown [-h] -i INPUT -o OUTPUT [-v] [--DEBUG]
```

Argument                   | Description
:----                      | :----
-i INPUT, --input INPUT    | The input `bio` file used for parsing and creating markdown file
-o OUTPUT, --output OUTPUT | The output file name for the single markdown file

## Generate PDF ##

```bash
python3 generate_documentation.py pdf [-h] -i INPUT -o OUTPUT [-b BUILD] [-u] (-s | -g) [-v] [--DEBUG]
```

Argument                   | Description
:----                      | :----
-i INPUT, --input INPUT    | The input `bio` file used for parsing and creating markdown file
-o OUTPUT, --output OUTPUT | The output file name for the single markdown file
-b BUILD, --build BUILD    | The name of the build that this documentation is being built for
-u, --upload               | Flag to trigger uploading documentation to Google Drive for access on Teams
-s, --svn                  | Flag to trigger use of SVN for generation of Changes list for cover page
-g, --git                  | Flag to trigger use of git for generation of Changes list for cover page

# Resources for writing markdown #

* [Pandoc's documentation](http://pandoc.org/MANUAL.html#pandocs-markdown)
* [Markdown Guide Basic Syntax](https://www.markdownguide.org/basic-syntax)
	- Some of these features might not be supported in Pandoc
* [Sublime Text Markdown Plugin](https://packagecontrol.io/packages/Markdown%20Extended)
	- Can be installed with built in package control
	- Allows for automatic formatting when entering text