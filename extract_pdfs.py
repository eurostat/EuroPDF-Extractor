import argparse
import multiprocessing
from utils.parser import PDFExtractor, list_pdfs_in_folder

def process_pdf(args):
    """
    Worker function to process a single PDF file.
    """
    pdf_path, output_folder, config_path = args
    try:
        print(f"Processing: {pdf_path}")
        extractor = PDFExtractor(pdf_path, output_folder=output_folder, config_path=config_path)
        extracted_data = extractor.extract_all()
        print(f"Extraction completed for: {pdf_path}")
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

def main(folder_path, output_folder, config_path):
    """
    Main function to extract information from PDF files in a folder using multiprocessing.

    Args:
        folder_path (str): Path to the folder containing PDF files.
        output_folder (str): Path to the folder where outputs will be saved.
        config_path (str): Path to the configuration JSON file.
    """
    # List all PDFs in the specified folder
    doc_list = list_pdfs_in_folder(folder_path)

    if not doc_list:
        print(f"No PDF files found in folder: {folder_path}")
        return

    # Prepare arguments for multiprocessing
    args_list = [(f"{folder_path}/{doc}", output_folder, config_path) for doc in doc_list]

    # Use multiprocessing to process PDFs
    num_processes = max(1, multiprocessing.cpu_count() - 4)
    print(f"Using {num_processes} processes for extraction.")
    
    with multiprocessing.Pool(processes=num_processes) as pool:
        pool.map(process_pdf, args_list)

if __name__ == "__main__":
    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(description="Process PDF files from a folder.")
    parser.add_argument("--folder_path", required=True, help="Path to the folder containing PDF files.")
    parser.add_argument("--output_folder", required=True, help="Path to the folder for saving outputs.")
    parser.add_argument("--config_path", required=True, help="Path to the text cleanup configuration file.")
    
    args = parser.parse_args()
    
    # Run the main function with parsed arguments
    main(args.folder_path, args.output_folder, args.config_path)



# python extract_pdfs.py --folder_path data/documents --output_folder data/outputs --config_path utils/text_cleanup_config.json
