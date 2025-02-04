import fitz  # PyMuPDF
import os
import json
import re
from itertools import product
from collections import defaultdict, OrderedDict

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def list_pdfs_in_folder(folder_path):
    """
    Lists all PDF files in the specified folder.

    Args:
        folder_path (str): The path to the folder.

    Returns:
        list: A list of PDF file names in the folder.
    """
    try:
        # List all files in the folder and filter for PDFs
        pdf_files = [file for file in os.listdir(folder_path) if file.endswith('.pdf')]
        return pdf_files
    except FileNotFoundError:
        raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")
    except Exception as e:
        raise RuntimeError(f"An error occurred while listing PDF files: {e}")


class PDFExtractor:
    """
    A class for extracting, cleaning, and processing text and metadata from PDF files.
    Provides methods for cleaning text, extracting metadata, and handling TOC.
    """

    def __init__(self, pdf_path, output_folder="outputs", config_path="text_cleanup_config.json"):
        """
        Initializes the PDFExtractor with a PDF file, output folder, and text cleanup configuration.

        Args:
            pdf_path (str): Path to the PDF file.
            output_folder (str): Directory for storing output files.
            config_path (str): Path to the JSON configuration file for text cleanup rules.
        """
        self.pdf_path = pdf_path
        self.doc_name = os.path.splitext(os.path.basename(pdf_path))[0]
        self.doc_output_folder = output_folder
        self._create_output_folder()
        self.doc = self._open_pdf()
        self.config = self._load_config(config_path)
        self.processed_text = {}

    import fitz  # PyMuPDF

    def extract_pdf_textand_clean(self):
        """
        Extracts raw text from a PDF file and returns it as a single string.

        Args:
            pdf_path (str): The path to the PDF file to extract text from.

        Returns:
            str: The concatenated raw text from all pages in the PDF.
        """
        # Open the PDF document
        try:
            pdf_document = fitz.open(self.pdf_path)
        except Exception as e:
            raise FileNotFoundError(f"Error opening file {self.pdf_path}: {e}")

        # Initialize an empty string to store all the text
        all_text = ""

        # Iterate over each page in the PDF
        for page_num in range(len(pdf_document)):
            # Access the current page
            page = pdf_document[page_num]
            # Extract text from the current page
            all_text += page.get_text()  # Append the extracted text to the string
            # Optionally, you could add page breaks here:
            # all_text += "\n\n--- PAGE BREAK ---\n\n"

        # Close the PDF document to free up resources
        pdf_document.close()

        # Cleaning text
        all_cleaning_text = self.clean_text(all_text)

        # Return the extracted text
        return all_cleaning_text


    def _create_output_folder(self):
        """Ensures the output folder exists or creates it."""
        try:
            os.makedirs(self.doc_output_folder, exist_ok=True)
        except OSError as e:
            raise OSError(f"Error creating output folder: {e}")

    def _open_pdf(self):
        """Opens the PDF document using PyMuPDF."""
        try:
            return fitz.open(self.pdf_path)
        except Exception as e:
            raise FileNotFoundError(f"Failed to open PDF file: {e}")

    def _load_config(self, config_path):
        """
        Loads a JSON configuration file for text cleanup rules.

        Args:
            config_path (str): Path to the configuration file.

        Returns:
            dict: Parsed configuration data.
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at: {config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in configuration file: {config_path}")

    def clean_text(self, text):
        """
        Cleans text by removing special characters, applying regex substitutions,
        and normalizing whitespace.

        Args:
            text (str): The raw text to clean.

        Returns:
            str: Cleaned text.
        """
        try:
            for char in self.config.get("special_characters", []):
                text = text.replace(char, "")

            for expr in self.config.get("expressions", []):
                text = re.sub(expr, "", text)

            text = re.sub(r"\s+", " ", text).strip()
            return text
        except Exception as e:
            raise RuntimeError(f"Error during text cleaning: {e}")

    def clean_title_suffix(self, title):
        """
        Removes trailing uppercase letters or digits from the end of a title.

        Args:
            title (str): The title to clean.

        Returns:
            str: Cleaned title.
        """
        try:
            clean_pattern = re.compile(r"(.*?)([A-Z]+\s*|\d+\s*)*$")
            match = clean_pattern.match(title)
            return match.group(1).strip() if match else title
        except Exception as e:
            raise RuntimeError(f"Error during title suffix cleaning: {e}")

    def extract_metadata(self):
        """
        Extracts metadata from the PDF.

        Returns:
            dict: Metadata as key-value pairs.
        """
        try:
            return self.doc.metadata
        except Exception as e:
            raise RuntimeError(f"Error extracting metadata: {e}")

    def extract_toc(self):
        """
        Extracts the Table of Contents (TOC) from the PDF and cleans the titles.

        Returns:
            list[dict]: A list of TOC entries with level, cleaned title, and page number.
        """
        try:
            self.toc = self.doc.get_toc(simple=False)  # Extract detailed TOC
            self.formatted_toc = []
            self.no_numbering_flag = True  # Assume titles have no numbering initially

            # Regex pattern to detect numbering formats (e.g., "1.", "1.1.", "1.1.1.")
            numbering_pattern = re.compile(r"^\d+(\.\d+)*\.?\s")

            for item in self.toc:
                level = item[0]  # Hierarchical level of the TOC entry
                raw_title = item[1]  # Raw title from the TOC
                page = item[2]  # Page number of the TOC entry

                cleaned_title = self.clean_text(raw_title)

                # Check if the title contains numbering
                if numbering_pattern.match(cleaned_title):
                    self.no_numbering_flag = False

                # Clean title suffix if no numbering is present
                if self.no_numbering_flag:
                    cleaned_title = self.clean_title_suffix(cleaned_title)

                toc_entry = {
                    "level": level,
                    "title": cleaned_title,
                    "page": page
                }
                self.formatted_toc.append(toc_entry)

            # If no numbering was found, attempt to search and replace numbered titles in the text
            if self.no_numbering_flag:
                self.search_and_replace_numbered_titles(self.formatted_toc, self.processed_text)

            return self.formatted_toc
        except Exception as e:
            raise RuntimeError(f"Error extracting TOC: {e}")


    def generate_title_variations(self, title):
        """
        Generates variations of a title by combining different spacing and numbering patterns.

        Args:
            title (str): The original title.

        Returns:
            list: A list of possible variations for the title, including numbering patterns.
        """
        try:
            words = title.split()
            variations = []

            # Generate all combinations of spaces between words
            for space_combination in product([True, False], repeat=len(words) - 1):
                new_title = words[0]
                for i, keep_space in enumerate(space_combination):
                    new_title += (" " if keep_space else "") + words[i + 1]
                variations.append(new_title)

            # Add numbering patterns (e.g., "1.", "1.1.", "1.1.1.") to each variation
            for variation in variations[:]:  # Iterate over existing variations
                for numbering_depth in range(1, 5):  # Generate up to four levels of numbering
                    numbering = '.'.join(['\\d+'] * numbering_depth)
                    numbered_variation = numbering + r'\s*' + re.escape(variation)
                    variations.append(numbered_variation)

            return variations
        except Exception as e:
            raise RuntimeError(f"Error generating title variations: {e}")


    def search_and_replace_numbered_titles(self, toc, processed_text):
        """
        Searches for and replaces TOC titles with numbered titles found in the document text.

        Args:
            toc (list): List of TOC entries with levels, titles, and page numbers.
            processed_text (dict): Processed text sections for updating corresponding titles.
        """
        try:
            # Define numbering patterns (e.g., "1.", "1.1.", "1.1.1.")
            numbering_patterns = [
                r"\d+", r"\d+\.", r"\d+\.\d+", r"\d+\.\d+\.", r"\d+\.\d+\.\d+",
                r"\d+\.\d+\.\d+\.", r"\d+\.\d+\.\d+\.\d+"
            ]

            for i, toc_entry in enumerate(toc):
                original_title = toc_entry["title"]
                start_page = toc_entry["page"] - 1
                end_page = toc[i + 1]["page"] - 1 if i + 1 < len(toc) else self.doc.page_count - 1

                # Generate title variations
                title_variations = self.generate_title_variations(original_title)
                found_match = False

                for numbering in numbering_patterns:
                    for title_variant in title_variations:
                        pattern = f"{numbering}\\s*{title_variant}"

                        # Search through pages in the range for a matching pattern
                        for page_num in range(start_page, end_page + 1):
                            page = self.doc.load_page(page_num)
                            page_text = self.clean_text(page.get_text("text"))

                            # Perform character-by-character search for the pattern
                            match_position = -1
                            for start_index in range(len(page_text)):
                                if re.match(pattern, page_text[start_index:], re.IGNORECASE):
                                    match_position = start_index
                                    break

                            if match_position != -1:
                                # Extract the matched numbered title
                                numbered_title = page_text[match_position:match_position + len(numbering) + len(title_variant)]

                                # Clean trailing uppercase or digit-only suffix if numbering is absent
                                if self.no_numbering_flag:
                                    numbered_title = self.clean_title_suffix(numbered_title)

                                # Update the TOC entry with the numbered title
                                toc_entry["title"] = numbered_title

                                # Update the processed_text dictionary with the new title
                                if original_title in processed_text:
                                    processed_text[numbered_title] = processed_text.pop(original_title)

                                found_match = True
                                break
                        if found_match:
                            break
        except Exception as e:
            raise RuntimeError(f"Error during search and replace of numbered titles: {e}")


    def extract_raw_text(self):
        """
        Extracts the raw text from the PDF while excluding headers and footers.

        Returns:
            str: Concatenated text from all pages of the PDF.
        """
        try:
            full_text = ""
            header_height = 50
            footer_height = 70

            for page_num in range(self.doc.page_count):
                page = self.doc.load_page(page_num)
                page_rect = page.rect

                # Define the main content area to exclude headers and footers
                main_content_rect = fitz.Rect(
                    page_rect.x0,
                    page_rect.y0 + header_height,
                    page_rect.x1,
                    page_rect.y1 - footer_height
                )

                # Extract text from the content area
                full_text += page.get_text("text", clip=main_content_rect) + "\n"

            return full_text
        except Exception as e:
            raise RuntimeError(f"Error extracting raw text: {e}")


    def structure_raw_text_by_toc_no_numbering(self):
        """
        Structures raw text into sections based on TOC when numbering is absent.

        Returns:
            dict: Dictionary of sections with titles as keys and their corresponding text as values.
        """
        try:
            sections = {}
            toc = self.formatted_toc
            self.texts_to_remove = self.config.get("texts_to_remove", [])

            # Regex to remove trailing number chains directly attached to titles
            trailing_number_pattern = re.compile(r"(.*?)(\d+(\.\d+)*\.)$")

            header_height = 50
            footer_height = 70

            for i, toc_entry in enumerate(toc):
                title = toc_entry["title"]

                # Clean trailing number chains from the title
                match = trailing_number_pattern.match(title)
                if match:
                    title = match.group(1).strip()

                start_page = toc_entry["page"] - 1
                end_page = toc[i + 1]["page"] - 1 if i + 1 < len(toc) else self.doc.page_count - 1

                section_text = ""
                start_found = False
                end_position = None

                for page_num in range(start_page, end_page + 1):
                    page = self.doc.load_page(page_num)
                    page_text = self.clean_text(page.get_text("text"))

                    # Find the start of the section
                    if not start_found:
                        for start_index in range(len(page_text)):
                            if page_text[start_index:].startswith(title):
                                start_position = start_index
                                start_found = True
                                break
                        if start_found:
                            section_text += page_text[start_position:] + "\n"
                        continue

                    # Find the end of the section
                    if start_found and i + 1 < len(toc):
                        next_title = toc[i + 1]["title"]
                        for end_index in range(len(page_text)):
                            if page_text[end_index:].startswith(next_title):
                                end_position = end_index
                                break
                        if end_position is not None:
                            section_text += page_text[:end_position]
                            break

                    # Add full page text if within the section
                    if start_found and end_position is None:
                        section_text += page_text + "\n"

                # Remove unwanted text snippets
                for text_to_remove in self.texts_to_remove:
                    section_text = section_text.replace(text_to_remove, "").strip()

                sections[title] = self.clean_text(section_text)

            return sections
        except Exception as e:
            raise RuntimeError(f"Error structuring raw text by TOC: {e}")


    def structure_raw_text_by_toc(self):
        """
        Structures the raw text from the PDF into sections based on the Table of Contents (TOC).

        This method uses the TOC to determine the boundaries of each section and extracts text
        from the corresponding pages, excluding headers and footers.

        Returns:
            dict: A dictionary with TOC titles as keys and the corresponding cleaned text as values.
        """
        try:
            sections = {}
            toc = self.extract_toc()  # Extract the TOC to define section boundaries
            self.texts_to_remove = self.config.get("texts_to_remove", [])  # Load any unwanted text markers to remove

            # Define the heights to exclude headers and footers during text extraction
            header_height = 50
            footer_height = 70

            for i, entry in enumerate(toc):
                title = entry["title"]
                start_page = entry["page"] - 1  # Convert page number to 0-based index
                end_page = toc[i + 1]["page"] - 1 if i + 1 < len(toc) else self.doc.page_count - 1  # Determine the last page

                section_text = ""
                for page_num in range(start_page, end_page + 1):
                    # Load the current page
                    page = self.doc.load_page(page_num)
                    page_rect = page.rect

                    # Define the content area excluding headers and footers
                    main_content_rect = fitz.Rect(
                        page_rect.x0,
                        page_rect.y0 + header_height,
                        page_rect.x1,
                        page_rect.y1 - footer_height
                    )

                    # Extract text from the defined content area
                    section_text += page.get_text("text", clip=main_content_rect) + "\n"

                # Remove unwanted texts specified in the configuration
                for text_to_remove in self.texts_to_remove:
                    section_text = section_text.replace(text_to_remove, "").strip()

                # Clean and normalize the section text
                sections[title] = self.clean_text(section_text)

            return sections
        except Exception as e:
            raise RuntimeError(f"Error while structuring raw text by TOC: {e}")
        
    
    def extract_sections_from_processed_text(self, titles, processed_text):
        """
        Extracts sections of text based on TOC titles and their boundaries in the processed text.

        Args:
            titles (list): List of TOC titles to define section boundaries.
            processed_text (dict): Dictionary with titles as keys and corresponding raw text as values.

        Returns:
            dict: Dictionary with titles as keys and their corresponding sectioned text as values.
        """
        try:
            sectioned_text = {}

            for i, title in enumerate(titles):
                # Determine the modified version of the current title
                if re.match(r"^\d+\.\d+\.\d+\.\s+.+", title):
                    modified_title = title
                elif re.match(r"^\d+\.\d+\..+", title) or re.match(r"^\d+\.\d+\.\d+\..+", title):
                    modified_title = re.sub(r"((\d+\.){2,3})", r"\1 ", title).strip()
                elif re.match(r"^\d+\..+", title):
                    modified_title = re.sub(r"^\d+\.\s*", "", title)  # Remove numbering to get the plain title
                else:
                    modified_title = title  # Keep unchanged if no specific match

                # Get the raw text corresponding to the current title
                current_text = processed_text.get(title, "")
                if not current_text:
                    sectioned_text[title] = ""  # Skip empty sections
                    continue

                section_text = current_text

                # Identify the next title for the end boundary of the current section
                if i + 1 < len(titles):
                    next_title = titles[i + 1]

                    # Transform the next title similarly to the current title
                    if re.match(r"^\d+\.\d+\.\d+\.\s+.+", next_title):
                        modified_next_title = next_title
                    elif re.match(r"^\d+\.\d+\..+", next_title) or re.match(r"^\d+\.\d+\.\d+\..+", next_title):
                        modified_next_title = re.sub(r"((\d+\.){2,3})", r"\1 ", next_title).strip()
                    elif re.match(r"^\d+\..+", next_title):
                        modified_next_title = re.sub(r"^\d+\.\s*", "", next_title)
                    else:
                        modified_next_title = next_title

                    # Find the start index of the current section
                    start_index = current_text.find(modified_title)
                    if start_index == -1:  # Fallback to use the original title
                        start_index = current_text.find(title)
                    if start_index == -1 and re.match(r"^\d+\.\s*.+", title):  # Fallback to plain title
                        stripped_title = re.sub(r"^\d+\.\s*", "", title)
                        start_index = current_text.find(stripped_title)

                    # Find the end index using the next title
                    end_index = current_text.find(modified_next_title, start_index + len(modified_title))
                    if end_index == -1:  # Fallback to use the original next title
                        end_index = current_text.find(next_title, start_index + len(modified_title))

                    # Extract the section text
                    if start_index != -1:
                        section_text = current_text[start_index:end_index].strip()
                else:
                    # If no next title, take everything from the current title to the end of the text
                    start_index = current_text.find(modified_title)
                    if start_index != -1:
                        section_text = current_text[start_index:].strip()

                # Store the extracted section text
                sectioned_text[title] = section_text

            return sectioned_text
        except Exception as e:
            raise RuntimeError(f"Error while extracting sections from processed text: {e}")
        
    def refine_extracted_sections(self, extracted_sections):
        """
        Refines the extracted sections by:
        1. Removing the title from the beginning of the section text if present.
        2. Setting the section text to an empty string if it is too short.
        3. Handling cases where numbering is directly attached to the title.

        Args:
            extracted_sections (dict): The output of extract_sections_from_processed_text.

        Returns:
            dict: A dictionary with titles as keys and their corresponding refined section text as values.
        """
        try:
            refined_sections = {}

            for title, text in extracted_sections.items():
                # 1. Remove the title from the beginning of the text if it exists
                if text.startswith(title):
                    text = text[len(title):].strip()

                # 2. Check if the section text length is too short after removing numbering
                stripped_title = re.sub(r"\d+[\.\s]*", "", title).strip()  # Remove numbering from the title
                stripped_text = re.sub(r"\d+[\.\s]*", "", text).strip()  # Remove numbering from the text
                if len(stripped_text) <= 50:  # Threshold for considering text too short
                    text = ""

                # 3. Handle cases where numbering is attached to the title
                numbering_pattern = re.match(r"^(\d+(\.\d+)*\.)", title)  # Matches numbering like "1.", "1.1."
                if numbering_pattern:
                    numbering = numbering_pattern.group(0)  # Extract the numbering (e.g., "1.1.")
                    expected_start = f"{numbering} {stripped_title}"  # Form the expected start of the section text
                    if text.startswith(expected_start):
                        text = text[len(expected_start):].strip()

                # Save the refined section
                refined_sections[title] = text

            return refined_sections
        except Exception as e:
            raise RuntimeError(f"Error refining extracted sections: {e}")
    
    def normalize_keys_with_numbering(self, input_dict):
        """
        Normalizes the keys of a dictionary to ensure consistent numbering formats.

        Args:
            input_dict (dict): A dictionary with keys containing strings with or without numbering.

        Returns:
            dict: A new dictionary with normalized keys.
        """
        try:
            normalized_dict = {}

            for key, value in input_dict.items():
                # Regex to match and separate numbering and title
                match = re.match(r'^(\d+(\.\d+)*)(\.?)(\s*)(.*)', key)
                if match:
                    # Extract numbering and title
                    numbering = match.group(1)  # Group 1 contains the numbering (e.g., "1", "1.1")
                    title = match.group(5)  # Group 5 contains the title
                    normalized_key = f"{numbering}. {title.strip()}"  # Format as "X. Title"
                else:
                    # No numbering, retain the original key
                    normalized_key = key

                # Add the normalized key and value to the new dictionary
                normalized_dict[normalized_key] = value

            return normalized_dict
        except Exception as e:
            raise RuntimeError(f"Error normalizing keys with numbering: {e}")


    def process_string(self,input_string):
        # Separate numbering from the text
        match = re.match(r"^(\d+(?:\.\d+)*\.*)(.*)$", input_string)
        if not match:
            return input_string
        else:            
            numbering, text = match.groups()
            numbering = numbering.strip()
            text = text.strip()

            # Find the last uppercase letter from the end
            for i in range(len(text) - 1, -1, -1):
                if text[i].isupper():
                    # If the uppercase letter is the last character, do nothing
                    if i == 0:
                        break
                    # Check the next character (if exists)
                    if i + 1 < len(text) and text[i + 1] != " ":
                        # Remove from the end to this uppercase letter
                        text = text[:i]
                    break
            
            # Reconstruct the result
            result = f"{numbering} {text}"
            return result

    # Main function to process a dictionary
    def process_titles(self,input_dict):
        # Process each key in the dictionary using the helper function
        return {self.process_string(key): value for key, value in input_dict.items()}
    

    def process_titles_in_one_step(self, original_dict, input_list):
        """
        Processes a dictionary of titles and reconstructs the keys by merging numbering and text.

        Args:
            original_dict (dict): A dictionary with original titles as keys and associated text as values.
            input_list (list): A list of dictionaries with keys 'level', 'title', and 'page'.

        Returns:
            dict: A new dictionary with reconstructed titles as keys and the same text values.

        Raises:
            RuntimeError: If any error occurs during the processing of titles.
        """
        try:
            # Step 1: Extract numbering from input_list
            numbering_list = []
            for item in input_list:
                title = item.get("title", "")
                # Match numbering patterns like "1.", "1.1", etc.
                match = re.match(r"^(\d+(\.\d+)*)", title)
                if match:
                    numbering = match.group(1)  # Extract the numbering
                    if not numbering.endswith("."):
                        numbering += "."  # Ensure numbering ends with a dot
                    numbering_list.append(numbering)
                else:
                    numbering_list.append("")  # No numbering found, add an empty string

            # Step 2: Extract plain text from original_dict titles
            text_list = []
            for title in original_dict.keys():
                # Match titles with optional numbering followed by the actual text
                match = re.match(r"^\s*(\d+(\.\d+)*\.?\s*)?(.*)", title)
                if match:
                    text = match.group(3).strip()  # Extract and clean the actual text
                    text_list.append(text if text else "")  # Add text or an empty string
                else:
                    text_list.append("")  # Add an empty string if no match is found

            # Step 3: Reconstruct titles by combining numbering and text
            reconstructed_titles = []
            for numbering, text in zip(numbering_list, text_list):
                if numbering:
                    reconstructed_titles.append(f"{numbering} {text}".strip())  # Merge numbering and text
                else:
                    reconstructed_titles.append(text)  # Use text alone if numbering is absent

            # Step 4: Replace original titles with reconstructed titles in the dictionary
            updated_dict = {new_title: text for new_title, text in zip(reconstructed_titles, original_dict.values())}

            return updated_dict
        except Exception as e:
            raise RuntimeError(f"Error processing titles in one step: {e}")

    
    def find_and_replace_numberings(self, data):
        """
        Identifies non-logical numbering suites, reconstructs numbering where necessary, 
        and updates the input dictionary with corrected titles.

        Args:
            data (dict): A dictionary where keys are titles potentially starting with numberings
                        (e.g., "1. Introduction") and values are associated content.

        Returns:
            dict: A dictionary with updated titles containing corrected numbering.

        Raises:
            ValueError: If the input data is not a dictionary.
            TypeError: If keys in the dictionary are not strings.
        """

        def generate_next_numberings(current_numbering):
            """
            Generate all possible logical numbering sequences following the given numbering.
            Dynamically expands sub-levels, sibling levels, and higher levels.

            Args:
                current_numbering (str): The current numbering string (e.g., "1.2.3.").

            Returns:
                list: A sorted list of possible logical next numberings.
            """
            try:
                # Parse the current numbering into a list of integers
                parts = list(map(int, current_numbering.strip('.').split('.')))
            except ValueError:
                raise ValueError(f"Invalid numbering format: {current_numbering}")

            possibilities = []

            # Increment the last number in the current numbering
            incremented = parts[:-1] + [parts[-1] + 1]
            possibilities.append('.'.join(map(str, incremented)) + '.')

            # Add new sub-levels dynamically
            if len(parts) < 4:
                for x in range(1, 10):
                    sub_level = parts + [x]
                    possibilities.append('.'.join(map(str, sub_level)) + '.')
                    if len(sub_level) < 4:
                        for y in range(1, 10):
                            nested_sub_level = sub_level + [y]
                            possibilities.append('.'.join(map(str, nested_sub_level)) + '.')

            # Generate sibling levels
            for x in range(parts[-1] + 1, parts[-1] + 10):
                sibling_level = parts[:-1] + [x]
                possibilities.append('.'.join(map(str, sibling_level)) + '.')
                if len(sibling_level) < 4:
                    for y in range(1, 10):
                        sibling_sub_level = sibling_level + [y]
                        possibilities.append('.'.join(map(str, sibling_sub_level)) + '.')

            # Increment higher levels
            for i in range(len(parts) - 1):
                for x in range(1, 10):
                    higher_level = parts[:i + 1] + [parts[i + 1] + x]
                    possibilities.append('.'.join(map(str, higher_level)) + '.')

            # Increment the top-level number
            top_level_increment = [parts[0] + 1]
            possibilities.append('.'.join(map(str, top_level_increment)) + '.')

            return sorted(set(possibilities))

        # Input validation
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary.")
        if any(not isinstance(key, str) for key in data.keys()):
            raise TypeError("All keys in the dictionary must be strings.")

        # Extract numberings from dictionary keys
        numberings = []
        blank_indexes = []  # Indices of titles without numberings
        for idx, key in enumerate(data.keys()):
            parts = key.split(' ', 1)
            if parts[0].replace('.', '').isdigit():
                numberings.append(parts[0])
            else:
                numberings.append("")
                blank_indexes.append(idx)

        non_logical_indexes = []
        i = 0

        while i < len(numberings) - 1:
            current_numbering = numberings[i]
            if current_numbering == "":
                i += 1  # Skip blank entries
                continue

            logical_found = False
            j = i + 1
            while j < len(numberings):
                next_numbering = numberings[j]
                if next_numbering == "":
                    j += 1  # Skip blank entries
                    continue

                # Generate logical possibilities from the current numbering
                generated_next_numberings = generate_next_numberings(current_numbering)

                if next_numbering not in generated_next_numberings:
                    non_logical_indexes.append(j)
                    j += 1
                else:
                    logical_found = True
                    i = j - 1  # Update i to the last logical point
                    break

            if not logical_found:
                break
            i += 1

        # Deduplicate non-logical indexes
        non_logical_indexes = sorted(set(non_logical_indexes))

        # Reconstruct non-logical numberings
        reconstructed_numberings = numberings[:]
        for idx in non_logical_indexes:
            prev_valid = None
            next_valid = None

            # Find the previous valid numbering
            for i in range(idx - 1, -1, -1):
                if reconstructed_numberings[i] != "":
                    prev_valid = reconstructed_numberings[i]
                    break

            # Find the next valid numbering
            for i in range(idx + 1, len(reconstructed_numberings)):
                if reconstructed_numberings[i] != "":
                    next_valid = reconstructed_numberings[i]
                    break

            # Reconstruct based on adjacent valid numberings
            if prev_valid and next_valid:
                prev_parts = list(map(int, prev_valid.strip('.').split('.')))
                next_parts = list(map(int, next_valid.strip('.').split('.')))

                if len(prev_parts) == 1 and next_parts[0] == prev_parts[0]:
                    sub_level = prev_parts + [1] if len(prev_parts) < 4 else prev_parts[:-1] + [prev_parts[-1] + 1]
                    reconstructed_numberings[idx] = '.'.join(map(str, sub_level)) + '.'
                elif len(prev_parts) == len(next_parts) and prev_parts[:-1] == next_parts[:-1]:
                    reconstructed_numberings[idx] = '.'.join(map(str, prev_parts[:-1] + [prev_parts[-1] + 1])) + '.'
                else:
                    next_sibling = prev_parts[:-1] + [prev_parts[-1] + 1]
                    reconstructed_numberings[idx] = '.'.join(map(str, next_sibling)) + '.'

        # Update dictionary with corrected titles
        updated_dict = {}
        for idx, (key, value) in enumerate(data.items()):
            if idx in blank_indexes:
                updated_dict[key] = value  # Retain blank titles
            else:
                parts = key.split(' ', 1)
                new_numbering = reconstructed_numberings[idx]
                if len(parts) > 1:
                    updated_dict[new_numbering + " " + parts[1]] = value
                else:
                    updated_dict[new_numbering] = value

        return updated_dict

    def remove_title_from_text(self, input_dict):
        """
        For each title in a dictionary, remove numbering from the title, find its first occurrence in the text,
        and remove everything from the beginning of the text up to and including the matched title.

        Args:
            input_dict (dict): A dictionary with title:text pairs.

        Returns:
            dict: A new dictionary with updated text values where matched titles and preceding text are removed.

        Raises:
            ValueError: If the input is not a dictionary or if any key is not a string.
        """
        import re

        def remove_numbering(title):
            """
            Remove numbering (e.g., '1.', '1.1.', etc.) from the title.

            Args:
                title (str): The title from which numbering should be removed.

            Returns:
                str: The title without numbering.
            """
            if not isinstance(title, str):
                raise ValueError(f"Title must be a string. Got {type(title)}.")
            return re.sub(r'^\d+(\.\d+)*\.\s*', '', title).strip()

        def find_and_remove(text, title):
            """
            Find the first occurrence of the title in the text and remove everything 
            up to and including the matched title.

            Args:
                text (str): The text to search within.
                title (str): The title to find and remove.

            Returns:
                str: Updated text with the matched title and preceding content removed.

            Raises:
                ValueError: If text or title is not a string.
            """
            if not isinstance(text, str) or not isinstance(title, str):
                raise ValueError("Both text and title must be strings.")
            
            # Iterate character by character to find the first exact match of the title
            for i in range(len(text) - len(title) + 1):
                if text[i:i + len(title)] == title:
                    # Remove everything up to and including the title
                    return text[i + len(title):].lstrip()
            return text  # Return text unchanged if no match is found

        # Validate input
        if not isinstance(input_dict, dict):
            raise ValueError("Input must be a dictionary with title:text pairs.")
        if any(not isinstance(k, str) or not isinstance(v, str) for k, v in input_dict.items()):
            raise ValueError("All keys and values in the dictionary must be strings.")

        # Process each title:text pair
        result_dict = {}
        for title, text in input_dict.items():
            clean_title = remove_numbering(title)
            updated_text = find_and_remove(text, clean_title)
            result_dict[title] = updated_text

        return result_dict
    
    def organize_by_levels_with_grouping(self, input_dict):
        """
        Organizes titles and content into hierarchical levels based on numbering,
        and groups them by parent levels dynamically.

        Args:
            input_dict (dict): A dictionary with titles and their associated content.

        Returns:
            dict: A nested dictionary organized by levels, with grouped sub-levels.
        """
        organized = defaultdict(dict)  # Dictionary to hold organized levels
        unnumbered = {}

        # Regex to extract numbering prefix
        numbering_pattern = re.compile(r'^(\d+(\.\d+)*\.)')  # Matches "X.", "X.X.", "X.X.X." at the start of a title

        for title, content in input_dict.items():
            # Match the numbering prefix
            match = numbering_pattern.match(title)

            if match:
                # Extract the numbering prefix
                numbering = match.group(1).rstrip('.')  # e.g., "1", "2.1", "3.2.1"
                parent_numbering = '.'.join(numbering.split('.')[:-1])  # Determine the parent numbering
                
                if parent_numbering:
                    # Group under the parent level
                    parent_level = numbering.count('.') + 1
                    level_key = f"level {parent_level} for {parent_numbering}"
                    organized[level_key][title] = content
                else:
                    # Top-level entries
                    organized["level 1"][title] = content
            else:
                # Unnumbered titles
                unnumbered[title] = content

        # Add unnumbered titles to 'level 0'
        if unnumbered:
            organized["level 0"] = unnumbered

        return dict(organized)
    
    def restructure_levels(self, input_dict):
        """
        Restructure hierarchical levels in the dictionary based on parent numbering and titles.
        
        Args:
            input_dict (dict): A dictionary with hierarchical levels.
            
        Returns:
            dict: A new dictionary reorganized based on parent titles with recursive nesting.
        """
        new_dict = {}
        
        # Process level 0 directly
        if "level 0" in input_dict:
            for title, content in input_dict["level 0"].items():
                new_dict[title] = content

        # Process top-level keys (e.g., level 1)
        for key, value in input_dict.items():
            for i in range(1,5):
                if key.startswith("level {}".format(i)):
                    for title, content in value.items():
                        new_dict[title] = content

        # Recursive processing for nested levels
        def add_nested_levels(nested_key, nested_dict):
            # Extract parent numbering (e.g., "X.Y")
            parent_key = nested_key.split("for")[-1].strip()
            parent_title = next((title for title in new_dict if title.startswith(parent_key)), None)

            if parent_title:
                # Ensure the parent entry is a dictionary
                if isinstance(new_dict[parent_title], str):
                    new_dict[parent_title] = {"introduction": new_dict[parent_title]}
                
                # Add the nested dictionary to the appropriate parent
                for nested_title, nested_content in nested_dict.items():
                    if isinstance(nested_content, dict):  # Handle deeper nesting
                        add_nested_levels(nested_title, nested_content)
                    else:
                        # Add the nested content to the parent dictionary
                        new_dict[parent_title][nested_title] = nested_content

            else:
                # If no matching parent, process orphaned level

                if isinstance(nested_dict, dict):
                    for nested_title, nested_content in nested_dict.items():
                        if isinstance(nested_content, dict):  # Handle deeper nesting
                            add_nested_levels(nested_title, nested_content)
                        else:
                            new_dict[nested_key] = nested_dict
                else:
                    new_dict[nested_key] = nested_dict

        # Process all nested levels
        for key, sub_dict in input_dict.items():
            if "for" in key:
                add_nested_levels(key, sub_dict)

        return new_dict
    
    def resolve_and_filter_dict(self, data):
        """
        Process the dictionary to:
        1. Replace string values with dictionary values as described previously.
        2. Filter the root-level keys based on specified rules:
        - Keep keys without numbering.
        - Keep keys with numbering in the format X. or X. Something (e.g., '1. Introduction', '3. Methods').

        Args:
            data (dict): Nested dictionary structure.

        Returns:
            dict: Processed and filtered dictionary.
        """
        def flatten_dict(d, flat_mapping):
            """
            Recursively flatten the dictionary to build a reference map of key-value pairs.
            """
            for key, value in d.items():
                if key in flat_mapping:
                    # Only overwrite if the existing value is a string and the new one is a dict
                    if isinstance(flat_mapping[key], str) and isinstance(value, dict):
                        flat_mapping[key] = value
                else:
                    flat_mapping[key] = value
                
                if isinstance(value, dict):
                    flatten_dict(value, flat_mapping)

        def replace_strings_with_dicts(d, flat_mapping):
            """
            Recursively replace string values with dictionary values if applicable.
            """
            for key, value in d.items():
                if isinstance(value, dict):
                    replace_strings_with_dicts(value, flat_mapping)
                elif isinstance(value, str) and key in flat_mapping and isinstance(flat_mapping[key], dict):
                    d[key] = flat_mapping[key]

        def filter_root_keys(d):
            """
            Filter the root-level keys to keep:
            - Keys without numbering.
            - Keys with numbering in the format X. or X. Something.
            """
            filtered_dict = {}
            for key, value in d.items():
                if not re.match(r'\d+(\.\d+)+', key):  # Exclude keys like X.Y., X.Y.Z., etc.
                    if re.match(r'\d+\.$', key) or not re.match(r'\d+', key):  # Keep keys like X. or no numbering
                        filtered_dict[key] = value
                    elif re.match(r'^\d+\..*$', key) and not re.match(r'\d+\.\d+\.', key):
                        filtered_dict[key] = value  # Include keys like "3. Methods" or "2. General quality issues"
            return filtered_dict

        # Step 1: Build a flat reference mapping
        reference_mapping = {}
        flatten_dict(data, reference_mapping)

        # Step 2: Replace strings with dicts based on the reference mapping
        replace_strings_with_dicts(data, reference_mapping)

        # Step 3: Filter root-level keys
        return filter_root_keys(data)
    

    def extract_all(self):
        """
        Extracts and processes document data, including metadata, table of contents, 
        and structured content, then saves it to a JSON file.

        Returns:
            dict: A dictionary containing metadata, leveled_text, processed_text, and cleaned_text.

        Logs errors for failed steps and continues execution.
        """
        data = {"metadata": {}, "processed_text": {}, "leveled_text": {}, "cleaned_text": ""}

        try:
            # Step 1: Extract and update TOC titles
            try:
                self.extract_toc()
            except Exception as e:
                logging.error(f"Step 1 failed: Failed to extract and update TOC titles: {e}")

            # Step 2: Structure raw text into sections using TOC
            structured_processed_text = {}
            try:
                structured_processed_text = (
                    self.structure_raw_text_by_toc_no_numbering()
                    if self.no_numbering_flag
                    else self.structure_raw_text_by_toc()
                )
            except Exception as e:
                logging.error(f"Step 2 failed: Failed to structure raw text by TOC: {e}")

            # Step 3: Extract sections and refine structure
            try:
                if structured_processed_text:
                    titles = list(structured_processed_text.keys())
                    structured_processed_text = self.extract_sections_from_processed_text(
                        titles=titles, processed_text=structured_processed_text
                    )
            except Exception as e:
                logging.error(f"Step 3 failed: Failed to extract sections: {e}")

            # Step 4: Apply no-numbering specific refinements if needed
            try:
                if self.no_numbering_flag and structured_processed_text:
                    structured_processed_text = self.process_titles(structured_processed_text)
                    structured_processed_text = self.refine_extracted_sections(structured_processed_text)
            except Exception as e:
                logging.error(f"Step 4 failed: Failed during no_numbering_flag processing: {e}")

            # Step 5: Normalize keys, refine numbering, and clean text
            try:
                if structured_processed_text:
                    structured_processed_text = self.normalize_keys_with_numbering(structured_processed_text)
                    structured_processed_text = self.find_and_replace_numberings(structured_processed_text)
                    structured_processed_text = self.remove_title_from_text(structured_processed_text)
            except Exception as e:
                logging.error(f"Step 5 failed: Failed during normalization or text cleaning: {e}")

            # Step 6: Handle numbering-based processing for titles
            try:
                if not self.no_numbering_flag and structured_processed_text:
                    structured_processed_text = self.process_titles_in_one_step(
                        structured_processed_text, self.formatted_toc
                    )
            except Exception as e:
                logging.error(f"Step 6 failed: Failed to process titles in one step: {e}")

            # Step 7: Process leveled text and prepare the final structure
            leveled_text = {}
            try:
                if structured_processed_text:
                    leveled_text = self.organize_by_levels_with_grouping(structured_processed_text)
                    leveled_text = self.restructure_levels(leveled_text)
                    leveled_text = self.resolve_and_filter_dict(leveled_text)
            except Exception as e:
                logging.error(f"Step 7 failed: Failed to prepare leveled text: {e}")

            # Populate final data structure
            try:
                data["metadata"] = self.extract_metadata()
                data["leveled_text"] = leveled_text
                data["processed_text"] = structured_processed_text
                data["cleaned_text"] = self.extract_pdf_textand_clean()
            except Exception as e:
                logging.error(f"Step 7 failed: Failed to extract metadata or process final structure: {e}")

        except Exception as e:
            # Log fallback error
            logging.error(f"Pipeline encountered an unexpected error: {e}")
            data["metadata"] = self.extract_metadata()
            data["cleaned_text"] = self.extract_pdf_textand_clean()

        # Step 8: Save the processed data to a JSON file with ordered keys
        ordered_data = OrderedDict([
            ("metadata", data.get("metadata", {})),
            ("leveled_text", data.get("leveled_text", {})),
            ("processed_text", data.get("processed_text", {})),
            ("cleaned_text", data.get("cleaned_text", ""))
        ])

        try:
            json_output_path = os.path.join(self.doc_output_folder, f"{self.doc_name}_data.json")
            with open(json_output_path, 'w', encoding='utf-8') as json_file:
                json.dump(ordered_data, json_file, indent=4, ensure_ascii=False)
        except FileNotFoundError:
            logging.error(f"Step 8 failed: Output folder '{self.doc_output_folder}' does not exist.")
        except IOError as e:
            logging.error(f"Step 8 failed: An error occurred while saving the JSON file: {e}")
        except Exception as e:
            logging.error(f"Step 8 failed: Unexpected error while saving JSON: {e}")

        return ordered_data
