import csv
import os

# Ensure data dir exists
os.makedirs("data", exist_ok=True)

# 1. Literature Inventory
with open("data/literature_inventory.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["file_name", "full_path", "file_type", "author", "year", "title", "journal_report", "organization", "doi", "url", "topic", "relevance_to_model", "extraction_status"])
    writer.writerow(["1734411984.pdf", "/Users/aviralakshat/Documents/SEM7/BTP/1734411984.pdf", "PDF", "BEE", "2019", "ENERGY CONSERVATION GUIDELINES FOR MSME SECTOR", "Report", "BEE", "", "", "Guidelines", "High", "Done"])
    writer.writerow(["Hydrogen-rotary-kilns-for-ironmaking.pdf", "/Users/aviralakshat/Documents/SEM7/BTP/Hydrogen-rotary-kilns-for-ironmaking.pdf", "PDF", "Will Hall et al.", "2025", "Hydrogen Rotary Kilns for Ironmaking in India", "Report", "TERI", "", "", "Hydrogen", "High", "Done"])
    writer.writerow(["decarbonising-coal-based-dri-production.pdf", "/Users/aviralakshat/Documents/SEM7/BTP/decarbonising-coal-based-dri-production.pdf", "PDF", "Kartheek Nitturu et al.", "2024", "Decarbonising Coal-based Direct Reduced Iron Production", "Report", "CEEW", "", "", "Decarbonization", "High", "Done"])

# 2. Literature Parameters
with open("data/literature_parameters.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["source_id", "file_name", "author", "year", "title", "parameter", "value", "min_value", "max_value", "unit", "plant_capacity", "plant_type", "ore_type", "coal_type", "page", "table", "figure", "source_location", "confidence", "notes", "model_module"])
    writer.writerow(["BEE_2019", "1734411984.pdf", "BEE", "2019", "ENERGY CONSERVATION GUIDELINES FOR MSME SECTOR", "Specific energy consumption", "0.64", "0.64", "0.82", "toe/tonne", "All", "Rotary Kiln", "Any", "Any", "39", "6.18", "", "", "High", "", "Economics"])

# 3. Engineering Assumptions
with open("data/engineering_assumptions.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["parameter", "value", "unit", "rationale", "assumption_type", "sensitivity_required", "literature_gap"])
    writer.writerow(["baseline_coal_consumption", "0.95", "t/t DRI", "Typical Indian DRI plant based on CEEW report", "Base", "Yes", "False"])

