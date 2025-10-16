#!/usr/bin/env python3
"""
merge_blocklist.py

A tool to merge IP and domain block entries from an XML file into an extracted RethinkDNS backup (.rbk),
and repackage it into a new .rbk file that can be imported back into the app.

Usage:
    python merge_blocklist.py \
        --ds-xml <path_to_xml_file> \
        --extracted-dir <path_to_extracted_rbk_dir> \
        --output-rbk <path_to_output_rbk_file> \
        [--sqlite-table <table_name>] \
        [--sqlite-column <column_name>] \
        [-v | --verbose]

Options:
    --ds-xml           Path to the XML file containing domain and IP block entries.
    --extracted-dir    Path to the extracted contents of a RethinkDNS .rbk backup.
    --output-rbk       Path where the updated .rbk file will be saved.
    --sqlite-table     (Optional) SQLite table to modify (default: 'blocked').
    --sqlite-column    (Optional) Column in the SQLite table (default: 'addr').
    -v, --verbose      Enable verbose logging for debugging or traceability.

Description:
    This script parses an XML file for entries to block (e.g., IPs and domains),
    injects them into the appropriate backup text files and/or SQLite DBs,
    then repackages the modified content into a new .rbk archive suitable for re-import.

"""
import os
import xml.etree.ElementTree as ET
import argparse
import shutil
import zipfile
import logging

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger()

def parse_ds_xml(ds_xml_path):
    logger.debug(f"Parsing ds.xml: {ds_xml_path}")
    tree = ET.parse(ds_xml_path)
    root = tree.getroot()
    entries = set()

    for host in root.findall('.//host'):
        name = host.get('name')
        if name:
            entries.add(name.strip())

    for ip in root.findall('.//ip'):
        addr = ip.get('addr')
        if addr:
            entries.add(addr.strip())

    logger.info(f"Extracted {len(entries)} unique entries from ds.xml")
    return entries

def read_existing_entries(txt_path):
    if not os.path.exists(txt_path):
        return set()

    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(txt_path, 'r', encoding='latin-1') as f:
            lines = f.readlines()

    entries = set(line.strip() for line in lines if line.strip())
    logger.info(f"Read {len(entries)} existing entries from {txt_path}")
    return entries

def write_entries(txt_path, entries):
    logger.info(f"Writing {len(entries)} entries to {txt_path}")
    with open(txt_path, 'w', encoding='utf-8') as f:
        for entry in sorted(entries):
            f.write(entry + '\n')

def zip_directory(source_dir, output_file):
    logger.info(f"Zipping directory {source_dir} to {output_file}")
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for foldername, _, filenames in os.walk(source_dir):
            for filename in filenames:
                file_path = os.path.join(foldername, filename)
                arcname = os.path.relpath(file_path, start=source_dir)
                zipf.write(file_path, arcname)

def main():
    parser = argparse.ArgumentParser(description="Merge blocklist entries from ds.xml into RethinkDNS .rbk backup")
    parser.add_argument('--ds-xml', required=True, help="Path to ds.xml file")
    parser.add_argument('--extracted-dir', required=True, help="Path to extracted .rbk folder")
    parser.add_argument('--output-rbk', required=True, help="Path to output .rbk file")
    parser.add_argument('--verbose', '-v', action='store_true', help="Enable debug logging")
    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Paths
    ds_xml = args.ds_xml
    extracted_dir = args.extracted_dir
    output_rbk = args.output_rbk
    rethink_backup_path = os.path.join(extracted_dir, "rethink_backup.txt")

    logger.info("Starting merge process")

    # Step 1: Extract entries from ds.xml
    new_entries = parse_ds_xml(ds_xml)

    # Step 2: Read existing entries
    existing_entries = read_existing_entries(rethink_backup_path)

    # Step 3: Merge
    combined = existing_entries.union(new_entries)

    # Step 4: Write back to file
    write_entries(rethink_backup_path, combined)

    # Step 5: Zip everything to .rbk
    zip_directory(extracted_dir, output_rbk)

    logger.info("Finished. Output RBK created at: " + output_rbk)

if __name__ == "__main__":
    main()
