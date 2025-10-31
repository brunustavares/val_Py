<p align="center">
  <img src="pix/_d6566782-1609-49d4-ab85-789322da7399.jpg" alt="val.Py Logo" width="300">
</p>

# val.Py
`val.Py` is a powerful validation tool for Moodle, designed to ensure that courses adhere to a specific, complex set of pedagogical and structural standards. It operates as a Python script that can be executed from the command line or seamlessly integrated into the Moodle interface via a companion block.

It was originally developed for [Universidade Aberta (UAb)](https://portal.uab.pt/).

### Premise
The development of a bot, with the purpose of assisting instructional designers in verifying a specific set of requirements within a Moodle course, in accordance with [Universidade Aberta](https://portal.uab.pt/)'s Virtual Pedagogical Model.
It combines web scraping (to analyze the rendered course page) with direct database queries (for precise configuration checks), providing a comprehensive audit of a course's structure.

The script performs a wide range of checks, including:
- **Course Typology**: Adapts its validation logic based on the course type (e.g., 1st cycle vs. 2nd/3rd cycle).
- **General Course Settings**: Verifies `shortname` vs `idnumber`, visibility, group mode, and other course-level configurations.
- **User Enrollment & Profiles**: Checks assigned roles like teachers and tutors, and validates their group associations to prevent misconfigurations.
- **Standard Blocks & Resources**: Validates the presence and correct setup of key elements like the 'Campus Virtual' block, News Forum, and the Course Plan (PUC/CdA).
- **Assessment Activities**: A deep validation of assignments (`e-folio`, `p-folio`, `exame`), checking dozens of parameters like `idnumber`, grading method, group settings, visibility, plagiarism tool integration (Turnitin), feedback types, and submission date logic.
- **Gradebook**: Validates the final grade calculation formula against a dynamically generated correct formula and verifies the sum of weights for assessment components.
- **Content Integrity**: Scans the course page for broken links, invalid images, and problematic iframes. It also checks images for potential transparency/watermarks.

## Project Components

The project consists of two main parts:

1.  **`val.Py` (Python Script)**: The core engine that contains all the validation logic. It connects to the Moodle database, scrapes the course page, and generates a detailed report.
2.  **`block_val_py` (Moodle Block)**: A Moodle block that provides a user-friendly interface within a course. It triggers the Python script, displays a summary score, and provides a link to the full, color-coded validation report.

## Used Python libraries
- requests
- re
- sys
- mysql.connector
- time
- validators
- cgi
- os
- hashlib
- urlparse (from urllib.parse)
- SSLError (from requests.exceptions)
- BytesIO (from io)
- BeautifulSoup (from bs4)
- Image (from PIL)
- tabulate (from tabulate)
- colored (from termcolor)
- datetime (from datetime)
- tqdm (from tqdm)

## Preconf (operating system level)
    1. sudo yum groupinstall "Development Tools" -y

    2. sudo yum install openssl-devel libffi-devel bzip2-devel -y

    3. wget https://www.python.org/ftp/python/3.9.18/Python-3.9.18.tgz
       tar xvf Python-*.tgz
       cd Python-3.9*/

    4. sudo vi Modules/Setup

       search "_socket socketmodule.c" and after:

            # Socket module helper for SSL support; you must comment out the other
            # socket line above, and possibly edit the SSL variable:
            #SSL=/usr/local/ssl

       , uncomment: 

            _ssl _ssl.c \
            -DUSE_SSL -I$(SSL)/include -I$(SSL)/include/openssl \
            -L$(SSL)/lib -lssl -lcrypto

       and exit vi saving

    5. ./configure --enable-optimizations --prefix=/usr/local --enable-shared LDFLAGS="-Wl,-rpath /usr/local/lib"

    6. sudo make altinstall

    7. python3.9 -m pip install --upgrade pip

    8. pip3.9 install urllib3==1.26.6

    9. pip3.9 install {used libraries}

    10. httpd.conf: "AddHandler cgi-script .cgi .py"

    11. .htaccess: "Options +ExecCGI"

## Usage
### CLI
_<path_to_python3.9> <path_to_val.Py> <Moodle_courseID>_

    $ /usr/local/bin/python3.9 {your/moodle/dirroot}/admin/cli/val.Py 12345

### via Moodle (using the val.Py companion block)
#### 1. Install
The plugin can be installed via the Moodle UI or manually on the server.

1. Log in to your Moodle site as an admin and go to _Site administration > Plugins > Install plugins_.
2. Upload the ZIP file with the plugin code. You should only be prompted to add extra details if your plugin type is not automatically detected.
3. Check the plugin validation report and finish the installation.
<hr style="width: 90%;">

##### manually

The plugin can be also installed by putting all the contents of the block to:

    {your/moodle/dirroot}/blocks/val_py

Afterwards, log in to your Moodle site as an admin and go to _Site administration > Notifications_ to complete the installation.

Alternatively, you can run

    $ php admin/cli/upgrade.php

to complete the installation from the command line.

**File Structure for `blocks/val_py/`:**
```
val_py/
├── block_val_py.php
├── function.js
├── style.css
└── val.Py
```
<hr style="width: 90%;">

#### 2. Add the block to any course
1. Turn Editing On
2. Select 'Add a block' from the drop-down menu
3. Pick "val.Py"
<hr style="width: 90%;">

#### 3. Use
Upon entering a course where the block has been added, it automatically triggers the `val.Py` script for the current course. The block shows a loading animation while the validation is in progress.

Once complete, the block displays a **"val.Py score"**. The score is color-coded for quick assessment:
- **Green (100%)**: All checks passed.
- **Yellow (70-99%)**: Minor alerts or non-critical issues were found.
- **Red (< 70%)**: Critical errors were detected.

Clicking on the score opens a new browser tab containing a detailed, color-coded HTML report with the results of every check performed.

## Packed Files
### val.Py
The core Python bot that performs all validation logic. It can be run via CLI or triggered by the Moodle block. It connects to the database, authenticates to Moodle to scrape course content, and prints a detailed HTML report to standard output.
<hr style="width: 90%;">

### block_val_py.php
The Moodle block entry point. It handles user permissions (restricting visibility to users with `moodle/site:approvecourse` capability), renders the block's initial HTML, generates a security token, and calls the JavaScript to execute the Python script.
<hr style="width: 90%;">

### function.js
Contains the client-side logic. It uses an AJAX call to execute `val.Py` on the server, passing the course ID and security token. It processes the returned HTML report, calculates and displays the final score in the block, and handles the opening of the detailed report in a new window.
<hr style="width: 90%;">

### style.css
Contains the CSS for styling the Moodle block, including the loading animation, the final score display, and color-coding for different validation statuses (OK, alert, error) in the final report.
<hr style="width: 90%;">

## Software used
- [Visual Studio Code](https://code.visualstudio.com/) (VSCode)
- [Image Creator from ©Microsoft Designer](https://www.bing.com/images/create?FORM=IRPGEN)
- [Ideogram](https://ideogram.ai/t/explore)
- [Prezi](https://prezi.com/)
- [Stephen Hawking Voice Generator](https://lingojam.com/StephenHawkingVoiceGenerator)
- [OBS Studio](https://obsproject.com/)
- [Microsoft Clipchamp](https://app.clipchamp.com/)

## Licenses

**Author**: Bruno Tavares  
**Contact**: [brunustavares@gmail.com](mailto:brunustavares@gmail.com)  
**LinkedIn**: [https://www.linkedin.com/in/brunomastavares/](https://www.linkedin.com/in/brunomastavares/)  
**Copyright**: 2023-present Bruno Tavares  
**License**: GNU GPL v3 or later  

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see <https://www.gnu.org/licenses/>.

### Assets

- **Source code**: GNU GPL v3 or later (© Bruno Tavares)  
- **Images**: created using [Image Creator from ©Microsoft Designer](https://www.bing.com/images/create?FORM=IRPGEN) and [Ideogram](https://ideogram.ai/t/explore)
