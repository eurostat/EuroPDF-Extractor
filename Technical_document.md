# **Technical Documentation for `PDFExtractor` Class and `extract_all` Method**

## **Overview**

The `PDFExtractor` class is a utility for analyzing PDF files. It performs text extraction, metadata retrieval, and hierarchical organization of content. The `extract_all` method serves as the primary interface for users, processing a PDF end-to-end and outputting structured and cleaned data.

---

## **Class: `PDFExtractor`**

### **Purpose**

The class is designed to handle PDF files by:
1. **Extracting metadata**: Retrieves essential document information (e.g., title, author, creation date).
2. **Processing text**: Extracts, cleans, and structures text content based on the Table of Contents (TOC).
3. **Organizing content**: Hierarchically organizes text into sections based on TOC numbering.
4. **Customizable cleaning rules**: Uses an external JSON configuration file to define specific cleaning patterns.

---

### **Key Attributes**

| **Attribute**          | **Description**                                                                                          |
|-------------------------|----------------------------------------------------------------------------------------------------------|
| `pdf_path`             | Path to the PDF file being processed.                                                                   |
| `doc_output_folder`    | Directory for saving processed data (default: `outputs/`).                                               |
| `doc`                  | PDF document object opened using PyMuPDF.                                                               |
| `formatted_toc`        | Extracted TOC entries, cleaned and formatted.                                                           |
| `no_numbering_flag`    | Boolean indicating if TOC titles lack numbering (e.g., `Introduction` vs. `1. Introduction`).            |
| `processed_text`       | Dictionary storing text organized into sections.                                                        |
| `config`               | Configuration dictionary loaded from a JSON file, defining cleaning rules and unwanted text markers.     |

---

## **Method: `extract_all`**

### **Purpose**

The `extract_all` method implements a multi-step pipeline that:
1. Extracts metadata and TOC from the PDF.
2. Extracts raw text and structures it into sections.
3. Cleans, normalizes, and organizes the text hierarchically.
4. Outputs structured results as a dictionary and saves them to a JSON file.

---

### **Inputs and Outputs**

#### **Inputs**
- No direct arguments are passed to the method.
- Utilizes class attributes initialized during the creation of the `PDFExtractor` instance.

#### **Outputs**
- **Returns**:
  A dictionary with the following structure:
  ```json
  {
      "metadata": {...},       // Metadata from the PDF (e.g., title, author).
      "leveled_text": {...},   // Text organized into hierarchical levels.
      "processed_text": {...}, // TOC-based structured text.
      "cleaned_text": "..."    // Raw cleaned text extracted from the entire PDF.
  }


### **Algorithm and Workflow**

#### **Step-by-Step Breakdown**

1. **Extract Table of Contents (TOC)**

    - **Method**: `extract_toc`
    - **Details**:
        - Retrieves TOC entries using PyMuPDF.
        - Identifies if TOC titles are numbered (e.g., `1. Introduction`) or unnumbered (`Introduction`).
        - Outputs `self.formatted_toc` for use in later steps.
    - **Error Handling**:
        - Logs errors if TOC is absent or malformed.

    **Pseudocode**:
    ```plaintext
    formatted_toc = extract_toc()
    no_numbering_flag = check_if_toc_is_numbered(formatted_toc)
    ```

2. **Structure Raw Text Based on TOC**

    - **Method**: `structure_raw_text_by_toc` or `structure_raw_text_by_toc_no_numbering`
    - **Details**:
        - Splits the PDF into sections based on TOC entries.
        - For numbered TOCs, uses title boundaries (e.g., `1. Introduction` to `2. Overview`).
        - For unnumbered TOCs, searches for approximate title matches in the text.
    - **Error Handling**:
        - Logs errors for failed extraction but continues execution.

    **Pseudocode**:
    ```plaintext
    if no_numbering_flag:
        structured_processed_text = structure_raw_text_by_toc_no_numbering()
    else:
        structured_processed_text = structure_raw_text_by_toc()
    ```

3. **Refine Sections**

    - **Methods**:
        - `extract_sections_from_processed_text`: Extracts subsections using TOC title boundaries.
        - `process_titles`: Normalizes titles for unnumbered TOC entries.
        - `refine_extracted_sections`: Cleans and validates section content.
    - **Details**:
        - Ensures sections contain meaningful content.
        - Removes redundant text (e.g., headers or repeated titles).
    - **Error Handling**:
        - Logs warnings for empty or poorly formatted sections.

4. **Normalize and Enhance Titles**

    - **Methods**:
        - `normalize_keys_with_numbering`: Standardizes TOC numbering formats.
        - `find_and_replace_numberings`: Fixes non-logical numbering (e.g., `1.1` followed by `1.3`).
        - `remove_title_from_text`: Removes TOC titles embedded in their corresponding sections.
    - **Details**:
        - Improves TOC accuracy for documents with inconsistent numbering.

5. **Organize Hierarchically**

    - **Methods**:
        - `organize_by_levels_with_grouping`: Groups sections into hierarchical levels (e.g., `1`, `1.1`, `1.1.1`).
        - `restructure_levels`: Builds nested dictionaries for parent-child relationships.
        - `resolve_and_filter_dict`: Filters invalid or redundant entries.
    - **Details**:
        - Creates a final, hierarchical representation of the document.

6. **Extract Metadata and Clean Text**

    - **Methods**:
        - `extract_metadata`: Extracts PDF metadata using PyMuPDF.
        - `extract_pdf_textand_clean`: Extracts and cleans the full raw text.
    - **Details**:
        - Metadata includes attributes like `title`, `author`, `creation_date`.
        - Cleaned text is useful for full-text search or analysis.

7. **Save Results to JSON**

    - Combines outputs into an `OrderedDict` and saves it as a JSON file.

    **Pseudocode**:
    ```plaintext
    data = {
        "metadata": extract_metadata(),
        "leveled_text": leveled_text,
        "processed_text": structured_processed_text,
        "cleaned_text": cleaned_text
    }
    save_to_json(data)
    ```

### **Outputs and JSON Structure**

#### **Outputs**

The final output of the `extract_all` method is twofold:

1. **Returned Dictionary**:
    - The method returns a dictionary containing:
      - **Metadata**: Document information such as title, author, and creation date.
      - **Leveled Text**: Hierarchically organized text based on TOC numbering.
      - **Processed Text**: Raw text split into sections as defined by the TOC.
      - **Cleaned Text**: Full document text cleaned and normalized.

    Example structure:
    ```json
    {
        "metadata": {
            "title": "Sample Document",
            "author": "John Doe",
            "creation_date": "2023-01-01T12:00:00",
            "producer": "PDF Producer"
        },
        "leveled_text": {
            "1. Introduction": {
                "1.1 Overview": "Text for Overview...",
                "1.2 Details": "Text for Details..."
            },
            "2. Methods": {
                "2.1 Experiment Setup": "Setup text..."
            }
        },
        "processed_text": {
            "Introduction": "Raw text for Introduction section...",
            "Methods": "Raw text for Methods section..."
        },
        "cleaned_text": "Full cleaned text of the document..."
    }
    ```

2. **Saved JSON File**:
    - The results are saved as a JSON file in the specified `doc_output_folder`.
    - The filename is derived from the document name (e.g., `sample_document_data.json`).

---

#### **JSON File Format**

The JSON file includes the following top-level keys:

1. **`metadata`**:
    - A dictionary containing document metadata extracted from the PDF.
    - Example:
      ```json
      {
          "title": "Sample Document",
          "author": "John Doe",
          "creation_date": "2023-01-01T12:00:00",
          "producer": "PDF Producer"
      }
      ```

2. **`leveled_text`**:
    - A dictionary representing text structured hierarchically.
    - Organized by TOC numbering with parent-child relationships.
    - Example:
      ```json
      {
          "1. Introduction": {
              "1.1 Overview": "Text for Overview...",
              "1.2 Details": "Text for Details..."
          },
          "2. Methods": {
              "2.1 Experiment Setup": "Setup text..."
          }
      }
      ```

3. **`processed_text`**:
    - A flat dictionary mapping TOC titles to their respective text sections.
    - Titles are cleaned, and text is split based on TOC boundaries.
    - Example:
      ```json
      {
          "Introduction": "Raw text for Introduction section...",
          "Methods": "Raw text for Methods section..."
      }
      ```

4. **`cleaned_text`**:
    - The fully extracted and cleaned text of the PDF document.
    - Suitable for full-text search or general analysis.
    - Example:
      ```json
      "This is the full cleaned text of the document, spanning all pages and sections."
      ```

This structure ensures the results are both human-readable and machine-parseable for further analysis.

### **Error Handling**

The `extract_all` method incorporates robust error handling at every stage of the processing pipeline. The following mechanisms are in place:

1. **Step-Specific Logging**:
    - Logs detailed messages for each processing step, including success, warnings, and failures.
    - Example log format:
      ```
      2023-01-01 12:00:00 - ERROR - Step 3 failed: Failed to extract sections: Exception message
      ```

2. **Fallbacks**:
    - If specific steps fail (e.g., TOC extraction), the pipeline continues to execute other steps, ensuring partial results are available.
    - Metadata and cleaned text are always extracted, even if TOC-based structuring fails.

3. **Common Error Handling**:
    - **Missing TOC**: If the TOC is absent or poorly formatted, a warning is logged, and text structuring proceeds without it.
    - **Malformed JSON Configuration**: If the configuration file is invalid, the cleaning step is skipped, and a default cleaning strategy is applied.
    - **File I/O Errors**: Logs issues with reading or writing files, such as missing output folders or permission errors.

---

### **Strengths**

- **TOC Processing**:
    - Handles both numbered and unnumbered TOC formats, ensuring compatibility with diverse document structures.
    - Cleans and normalizes titles for consistency.

- **Hierarchical Organization**:
    - Structures text into nested levels based on TOC numbering, making the output suitable for reporting or further analysis.

- **Customizability**:
    - Allows users to define text cleaning rules in a JSON configuration file.

- **Error Resilience**:
    - Logs errors and continues processing to produce partial results even in case of failures.

- **Output Format**:
    - Generates human-readable and machine-parseable JSON output.

---

### **Limitations**

- **TOC Dependency**:
    - Relies heavily on a well-structured TOC for accurate text segmentation.
    - In the absence of a TOC, fallback strategies may not perform well for complex documents.

- **Performance**:
    - Processing large PDFs with many pages and a detailed TOC can be time-intensive.
    - Advanced features like hierarchical structuring may increase computational overhead.

- **Configuration Requirements**:
    - Requires a valid JSON configuration file for advanced text cleaning and processing.
    - If the configuration is missing or invalid, default behaviors may not meet user expectations.

---

### **Function Relationships**

The `extract_all` method orchestrates various class methods, each responsible for a specific task. Below is a summary of these relationships:

| **Task**                       | **Method(s) Used**                                                                                     |
|--------------------------------|--------------------------------------------------------------------------------------------------------|
| **TOC Extraction**             | `extract_toc`: Retrieves and formats the Table of Contents.                                           |
| **Raw Text Structuring**        | `structure_raw_text_by_toc`, `structure_raw_text_by_toc_no_numbering`: Organizes text into sections.  |
| **Section Refinement**          | `extract_sections_from_processed_text`, `process_titles`, `refine_extracted_sections`: Improves text segmentation and formatting. |
| **Normalization and Cleaning**  | `normalize_keys_with_numbering`, `find_and_replace_numberings`, `remove_title_from_text`: Standardizes and cleans text and TOC titles. |
| **Hierarchical Organization**   | `organize_by_levels_with_grouping`, `restructure_levels`, `resolve_and_filter_dict`: Builds nested structures for hierarchical representation. |
| **Metadata and Raw Text Extraction** | `extract_metadata`, `extract_pdf_textand_clean`: Retrieves document metadata and cleans full text. |
| **Output Generation**           | Saves results to JSON using Python's `json` library.                                                 |

