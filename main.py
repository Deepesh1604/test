from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import io
import re
from typing import Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FinTrack Expense Analyzer", version="1.0.0")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_amount(amount_str: str) -> float:
    """Clean and convert amount string to float."""
    if pd.isna(amount_str) or amount_str == '':
        return 0.0
    
    # Convert to string and strip whitespace
    amount_str = str(amount_str).strip()
    
    # Remove currency symbols and commas
    amount_str = re.sub(r'[$€£¥₹,]', '', amount_str)
    
    # Handle parentheses for negative numbers
    if amount_str.startswith('(') and amount_str.endswith(')'):
        amount_str = '-' + amount_str[1:-1]
    
    # Remove any remaining non-numeric characters except decimal point and minus
    amount_str = re.sub(r'[^\d\.-]', '', amount_str)
    
    try:
        return float(amount_str)
    except ValueError:
        logger.warning(f"Could not convert amount: {amount_str}")
        return 0.0

def clean_category(category: str) -> str:
    """Clean category string."""
    if pd.isna(category):
        return ''
    
    # Convert to string, strip whitespace, and normalize case
    category = str(category).strip().lower()
    
    # Remove extra spaces
    category = re.sub(r'\s+', ' ', category)
    
    return category

def is_food_category(category: str) -> bool:
    """Check if category is food-related."""
    food_keywords = [
        'food', 'restaurant', 'dining', 'lunch', 'dinner', 'breakfast',
        'cafe', 'coffee', 'snack', 'meal', 'grocery', 'groceries',
        'catering', 'takeout', 'delivery', 'fast food', 'fastfood'
    ]
    
    category_clean = category.lower().strip()
    
    # Direct match
    if category_clean == 'food':
        return True
    
    # Check for food-related keywords
    for keyword in food_keywords:
        if keyword in category_clean:
            return True
    
    return False

@app.post("/analyze")
async def analyze_expenses(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Analyze expenses from uploaded CSV file and return total Food category spending.
    """
    try:
        # Read the uploaded file
        contents = await file.read()
        
        # Try different encodings if UTF-8 fails
        try:
            csv_string = contents.decode('utf-8')
        except UnicodeDecodeError:
            try:
                csv_string = contents.decode('latin-1')
            except UnicodeDecodeError:
                csv_string = contents.decode('cp1252')
        
        # Read CSV with pandas, handling various potential issues
        try:
            df = pd.read_csv(
                io.StringIO(csv_string),
                skipinitialspace=True,
                skip_blank_lines=True,
                encoding_errors='replace'
            )
        except pd.errors.EmptyDataError:
            raise HTTPException(status_code=400, detail="CSV file is empty")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error reading CSV: {str(e)}")
        
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV file contains no data")
        
        logger.info(f"CSV columns: {list(df.columns)}")
        logger.info(f"CSV shape: {df.shape}")
        
        # Clean column names - remove extra spaces and normalize case
        df.columns = df.columns.str.strip().str.lower()
        
        # Try to identify relevant columns
        amount_col = None
        category_col = None
        
        # Look for amount/cost columns
        for col in df.columns:
            if any(keyword in col for keyword in ['amount', 'cost', 'price', 'total', 'sum', 'expense']):
                amount_col = col
                break
        
        # Look for category columns
        for col in df.columns:
            if any(keyword in col for keyword in ['category', 'type', 'description', 'item']):
                category_col = col
                break
        
        if amount_col is None:
            raise HTTPException(status_code=400, detail="Could not identify amount column in CSV")
        
        if category_col is None:
            raise HTTPException(status_code=400, detail="Could not identify category column in CSV")
        
        logger.info(f"Using amount column: {amount_col}")
        logger.info(f"Using category column: {category_col}")
        
        # Clean the data
        df[f'{amount_col}_clean'] = df[amount_col].apply(clean_amount)
        df[f'{category_col}_clean'] = df[category_col].apply(clean_category)
        
        # Filter for food-related categories
        food_mask = df[f'{category_col}_clean'].apply(is_food_category)
        food_expenses = df[food_mask]
        
        logger.info(f"Found {len(food_expenses)} food-related expenses")
        
        # Calculate total food spending
        total_food_spending = food_expenses[f'{amount_col}_clean'].sum()
        
        logger.info(f"Total food spending: {total_food_spending}")
        
        return {
            "answer": round(total_food_spending, 2),
            "email": "user@example.com",  # Replace with your actual email
            "exam": "tds-2025-05-roe"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "FinTrack Expense Analyzer API is running"}

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)