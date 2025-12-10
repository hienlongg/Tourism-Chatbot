import pandas as pd
import unicodedata
import re
from typing import List, Dict, Tuple, Optional

from langchain_core.documents import Document

def slugify(value: str) -> str:
    """
    Convert Vietnamese text with diacritics into a URL-safe slug.
    
    Purpose: Create unique, safe identifiers for each location.
    
    Example:
        "Khu nhà công tử Bạc Liêu" -> "khu_nha_cong_tu_bac_lieu"
        "Thác Khe Vằn" -> "thac_khe_van"
    
    Args:
        value: Vietnamese location name with diacritics
    
    Returns:
        Lowercase slug with underscores (URL-safe)
    """
    # Step 1: Convert Vietnamese 'đ' to 'd' (not handled by NFKD)
    value = str(value).replace("đ", "d").replace("Đ", "D")
    
    # Step 2: Remove Vietnamese diacritics using Unicode normalization
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('utf-8')
    
    # Step 3: Remove special characters, keep only alphanumeric and spaces
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    
    # Step 4: Replace spaces and hyphens with underscores
    value = re.sub(r'[\s-]+', '_', value)
    
    return value

def load_and_process_data(csv_path: str) -> pd.DataFrame:
    """
    Load tourism location CSV and prepare it for vectorization.
    
    Purpose: 
    - Load raw CSV data
    - Generate loc_id for each location
    - Filter out rows with missing critical fields
    - Set loc_id as index for easy lookup
    
    Args:
        csv_path: Path to the CSV file
    
    Returns:
        Processed DataFrame with loc_id as index
    """
    print("📂 Loading CSV data...")
    df = pd.read_csv(csv_path)
    print(f"   Loaded {len(df)} rows")
    
    # Generate loc_id using slugify
    print("🔑 Generating loc_id for each location...")
    df['loc_id'] = df['TenDiaDanh'].apply(slugify)
    
    # Filter: Keep only rows with TenDiaDanh, DiaChi (NoiDung can be null)
    print("🔍 Filtering rows with missing critical data...")
    df_filtered = df.dropna(subset=['TenDiaDanh', 'DiaChi']).copy()
    
    # Fill NaN in NoiDung with empty string
    df_filtered['NoiDung'] = df_filtered['NoiDung'].fillna('')
    
    print(f"   Kept {len(df_filtered)} rows after filtering")
    
    # Set loc_id as index for fast lookup
    df_filtered = df_filtered.set_index('loc_id')
    
    return df_filtered


def create_documents(df: pd.DataFrame) -> List[Document]:
    """
    Convert DataFrame rows into LangChain Document objects.
    
    Purpose:
    - Create rich text content for embedding (TenDiaDanh + NoiDung + DiaChi)
    - Store metadata (loc_id, original columns) for retrieval
    - Each Document will be embedded and stored in ChromaDB
    
    Document Structure:
    - page_content: Combined text for semantic search
    - metadata: All original fields for context generation
    
    Args:
        df: Processed DataFrame with loc_id as index
    
    Returns:
        List of LangChain Document objects
    """
    print("📝 Creating documents for vectorization...")
    documents = []
    
    for loc_id, row in df.iterrows():
        # Build rich content: Title + Description + Location
        # This combined text will be embedded for semantic search
        content_parts = [
            f"Tên địa danh: {row['TenDiaDanh']}",
            f"Địa chỉ: {row['DiaChi']}"
        ]
        
        # Add description if available
        if row['NoiDung'] and str(row['NoiDung']).strip():
            content_parts.append(f"Mô tả: {row['NoiDung']}")
        
        page_content = "\n".join(content_parts)
        
        # Store all metadata for later use in recommendations
        metadata = {
            'loc_id': loc_id,
            'TenDiaDanh': row['TenDiaDanh'],
            'DiaChi': row['DiaChi'],
            'NoiDung': row['NoiDung'] if row['NoiDung'] else '',
            'ImageURL': row.get('ImageURL', ''),
            'DichVu': row.get('DichVu', ''),
            'ThongTinLienHe': row.get('ThongTinLienHe', ''),
            'DanhGia': row.get('DanhGia (Google Map)', '')
        }
        
        documents.append(Document(
            page_content=page_content,
            metadata=metadata
        ))
    
    print(f"   Created {len(documents)} documents")
    return documents