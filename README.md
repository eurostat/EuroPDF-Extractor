# EuroPDF-Extractor README

## Disclaimer
This software is experimental and provided as-is, without any express or implied warranties. Use it at your own risk. The authors and contributors assume no responsibility for any issues, damages, or losses that may arise from its use. By using this software, you agree that no liability will be held against the developers under any circumstances. Always test thoroughly before deploying in production environments.

## Overview
This Python Knowledge Extraction project allows you to extract and process text from PDF documents using a configuration file for text cleanup and organization. The output is saved as structured JSON files.


## Getting Started

### Step 1: Set Up the Environment

1. Clone the repository to your local machine.
2. Navigate to the project directory.
3. Create a Python virtual environment:
   ```bash
   python -m venv env
   ```
4. Activate the virtual environment:
   - On Windows:
     ```bash
     .\env\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source env/bin/activate
     ```
5. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Step 2: Organize Your Files
1. **Store PDF Documents**:
   Place your PDF documents in a designated folder, e.g., `data/documents`.

2. **Create a Configuration File**:
   Prepare a JSON configuration file for text cleanup and processing. Store it in the appropriate directory, e.g., `utils/text_cleanup_config.json`.

   Example structure of the configuration file:
   ```json
   {
      "special_characters": [
         "•", "▪", "●", "■", "◆", "◦", "*", "-", "–", "—", "→", "﻿"
      ],
      "expressions": [
         "\\n", "\\t", "\\r", "(next page)"
      ],
      "texts_to_remove": [
         "Inferring job vacancies from online job advertisements",
         "Distributional national account estimates for household income and consumption: methodological issues…",
         "An introduction to Large Language Models and their relevance for statistical offices"
      ]
   }
   ```

3. **Choose an Output Folder**:
   Specify an output folder where the processed JSON files will be saved. If the folder does not exist, it will be created automatically.

---

### Step 3: Run the Script
Run the script from the command line using the following command format:

```bash
python extract_pdfs.py --folder_path <path_to_pdf_folder> --output_folder <path_to_output_folder> --config_path <path_to_config_file>
```

## Example Command
```bash
python extract_pdfs.py --folder_path data/documents --output_folder data/outputs --config_path utils/text_cleanup_config.json
```

This will:
1. Process all PDF files in the `data/documents` folder.
2. Use the configuration file located at `utils/text_cleanup_config.json`.
3. Save the output JSON files to the `data/outputs` folder.

---

## Output
The script generates structured JSON files for each PDF document in the specified output folder. Each JSON file contains:
1. Metadata about the PDF
2. Leveled text: Hierarchical structuring of text sections
3. Processed Text: Text sections only
4. Cleaned text: full plain text cleaned

Note: if 2. or 4. failed, only 1. and 4. will be processed.

---

## Notes
- Ensure that all necessary dependencies are installed via `requirements.txt`.
- Verify the correctness of the configuration file to achieve the desired processing and cleanup.

---

## Troubleshooting
- **Environment Issues**: If the virtual environment is not working, ensure you are using the correct Python version.
- **Missing Folders**: Ensure the input folder with PDFs exists. The output folder will be created automatically.
- **Errors in JSON**: Verify the syntax and structure of the configuration file.
```

You can copy and paste this directly into your README file. It is formatted in Markdown and ready to use.
