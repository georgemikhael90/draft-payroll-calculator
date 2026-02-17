# Overview

This is a military pay calculation and comparison application built with Streamlit. The system calculates compensation for military personnel across three service categories: Army National Guard, Air National Guard, and Texas State Guard. It compares "original" pay calculations against "correct" pay calculations, showing monthly breakdowns and generating detailed reports in PDF and Excel formats.

The application handles complex pay structures including base pay (determined by rank and years of service), housing allowances (BAH), subsistence allowances (BAS), per diem, special duty pays (hazard, hardship, danger), and minimum income adjustments to ensure personnel meet minimum daily rate requirements.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture

**Technology**: Streamlit web framework

**Design Pattern**: Single-page application with columnar layout

The UI is organized into comparison columns showing original vs. correct pay calculations side-by-side. The application uses Streamlit's native components for:
- Input forms for service member details (rank, years of service, service category)
- Month-by-month duty status tracking (presence, hazardous duty, hardship duty, border duty)
- Visual comparison displays with formatted currency
- Report generation buttons for PDF and Excel exports

**Rationale**: Streamlit was chosen for rapid development of data-focused applications with minimal frontend code, allowing focus on calculation logic rather than UI framework complexity.

## Business Logic Architecture

**Pay Calculation Engine**: Located in `utils.py`

The core calculation system uses:
- Lookup tables for military pay grades (O-1 through O-6, W-1 through W-5, E-1 through E-9)
- Daily rate calculations based on rank and years of service
- Service category-specific logic (Texas State Guard uses fixed rates vs. variable BAH/BAS for National Guard)
- Minimum daily rate enforcement ($241.67) with automatic adjustment calculations

**Data Structure**: Pay information stored as nested dictionaries with monthly breakdowns containing:
- Days worked
- Base pay, BAH, BAS components
- Special pays (hazard, hardship, danger)
- Per diem and allowances
- Minimum income adjustments
- Monthly totals

**Rationale**: Dictionary-based monthly breakdowns provide flexible storage for varying pay components across different service categories and duty conditions.

## Report Generation Architecture

**Technology**: ReportLab (PDF) and OpenPyXL (Excel)

**Design Approach**: Template-based document generation with:
- Custom header/footer callbacks for branding (logo placement)
- Watermark system for unofficial documents
- Structured table layouts matching pay breakdown structure
- Formatted currency and aligned columns

**Report Types**:
1. PDF reports with visual branding and watermarks
2. Excel spreadsheets with formatted cells and embedded images

**Rationale**: Dual-format reporting provides both presentation-ready documents (PDF) and data-manipulation-friendly formats (Excel) for different use cases.

## Data Storage

**Current State**: File-based pay rate storage

Pay tables are stored in text files within `attached_assets/` directory:
- Complete military pay breakdowns by rank and years of service
- Structured text format with rank headers and year-to-pay mappings

**In-Memory Processing**: All calculations performed in-memory using pandas DataFrames and numpy for numerical operations

**Rationale**: Static pay tables change infrequently (annual updates), making file-based storage sufficient. No database currently required as there's no user data persistence or transaction history.

**Future Consideration**: System could be extended to use a database (like Postgres) for storing historical pay calculations, user profiles, or audit trails.

# External Dependencies

## Core Libraries

**Streamlit**: Web application framework for the user interface

**Pandas & NumPy**: Data manipulation and numerical calculations for pay computations

**ReportLab**: PDF generation library for creating formatted pay comparison reports with tables, headers, and watermarks

**OpenPyXL**: Excel file generation for spreadsheet-based reports with cell formatting and image embedding

**Pillow (PIL)**: Image processing for logo handling in both PDF and Excel reports

## Assets

**Logo File**: `attached_assets/NEW LOGO SMALL.png` - Used for document branding in headers

**Pay Rate Tables**: Text files containing military pay scales organized by:
- Rank (O-1 through O-6 for Officers, W-1 through W-5 for Warrant Officers, E-1 through E-9 for Enlisted)
- Years of service (0-40 years)
- Daily base pay rates

## Python Standard Library

**datetime**: Date handling for pay period calculations and report timestamps

**io**: In-memory file operations for image buffering

**enum**: Type-safe service category definitions (Army NG, Air NG, Texas SG)