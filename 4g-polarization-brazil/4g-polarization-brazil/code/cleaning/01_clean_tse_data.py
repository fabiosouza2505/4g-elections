"""
Script: 01_clean_tse_data.py
Author: Fabio [Surname]
Date: December 2024
Description: Clean and process TSE electoral data for polarization analysis

This script:
1. Reads raw TSE voting data (2010, 2014, 2018, 2022)
2. Merges with party ideology classifications
3. Calculates Esteban-Ray polarization index by municipality-year
4. Outputs cleaned dataset for analysis

Input: 
  - data/raw/votacao_candidato_munzona_YYYY.csv (from TSE)
  - data/raw/party_ideology_zucco_power.csv (from Harvard Dataverse)
  
Output:
  - data/processed/tse_cleaned.csv
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging
from typing import Dict, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
RAW_DATA_PATH = Path("data/raw")
PROCESSED_DATA_PATH = Path("data/processed")
ELECTION_YEARS = [2010, 2014, 2018, 2022]
CHUNK_SIZE = 100_000

# Party ideology additions for 2018 (missing from original Zucco & Power)
PARTY_IDEOLOGY_2018_ADDITIONS = {
    'PSL': 8.5,   # Bolsonaro's platform
    'NOVO': 9.0,  # Libertarian right
    'PATRI': 5.0, # Center
    'PODE': 4.5,  # Center-left
    'PMN': 5.5    # Center-right
}


def esteban_ray_index(
    vote_shares: np.ndarray, 
    ideologies: np.ndarray, 
    alpha: float = 1.6
) -> float:
    """
    Calculate Esteban-Ray polarization index
    
    Parameters:
    -----------
    vote_shares : np.ndarray
        Array of vote shares for each party (must sum to 1)
    ideologies : np.ndarray
        Array of ideology positions (0-10 scale)
    alpha : float
        Polarization sensitivity parameter (default 1.6)
        
    Returns:
    --------
    float : Polarization index value
    
    References:
    -----------
    Esteban, J., & Ray, D. (1994). On the measurement of polarization. 
    Econometrica, 62(4), 819-851.
    """
    # Remove parties with zero vote share
    mask = vote_shares > 0
    vote_shares = vote_shares[mask]
    ideologies = ideologies[mask]
    
    # Normalize vote shares (in case they don't sum to exactly 1)
    vote_shares = vote_shares / vote_shares.sum()
    
    # Calculate pairwise polarization
    polarization = 0
    n = len(vote_shares)
    
    for i in range(n):
        for j in range(n):
            if i != j:
                identification = vote_shares[i] ** (1 + alpha)
                alienation = vote_shares[j]
                distance = abs(ideologies[i] - ideologies[j])
                polarization += identification * alienation * distance
    
    # Normalization constant K (ensures bounded measure)
    K = 1.0  # Simplified; can adjust based on scale preferences
    
    return K * polarization


def load_party_ideologies() -> pd.DataFrame:
    """
    Load and prepare party ideology classifications
    
    Combines original Zucco & Power data with 2018 additions
    """
    logger.info("Loading party ideology classifications...")
    
    # Load base data from Zucco & Power
    ideology_path = RAW_DATA_PATH / "party_ideology_zucco_power.csv"
    ideology_df = pd.read_csv(ideology_path, encoding='utf-8')
    
    # Add 2018 missing parties
    additions = pd.DataFrame([
        {'party': party, 'ideology': score, 'year': 2018}
        for party, score in PARTY_IDEOLOGY_2018_ADDITIONS.items()
    ])
    
    ideology_df = pd.concat([ideology_df, additions], ignore_index=True)
    
    logger.info(f"Loaded ideologies for {len(ideology_df)} party-year observations")
    return ideology_df


def load_tse_data(year: int) -> pd.DataFrame:
    """
    Load TSE voting data for a given year with proper encoding
    
    Parameters:
    -----------
    year : int
        Election year (2010, 2014, 2018, or 2022)
    """
    logger.info(f"Loading TSE data for {year}...")
    
    file_path = RAW_DATA_PATH / f"votacao_candidato_munzona_{year}.csv"
    
    # TSE files typically use Latin1 encoding with semicolon separator
    try:
        # Try chunked reading for memory efficiency
        chunks = []
        for chunk in pd.read_csv(
            file_path,
            encoding='latin1',
            sep=';',
            chunksize=CHUNK_SIZE,
            low_memory=False
        ):
            # Filter for presidential elections, first round
            chunk = chunk[
                (chunk['DS_CARGO'] == 'Presidente') & 
                (chunk['NR_TURNO'] == 1)
            ]
            chunks.append(chunk)
        
        df = pd.concat(chunks, ignore_index=True)
        logger.info(f"  Loaded {len(df):,} records for {year}")
        return df
        
    except UnicodeDecodeError:
        # Fallback to ISO-8859-1 if Latin1 fails
        logger.warning(f"  Latin1 failed, trying ISO-8859-1...")
        df = pd.read_csv(file_path, encoding='iso-8859-1', sep=';')
        return df


def calculate_municipality_polarization(
    votes_df: pd.DataFrame, 
    ideology_df: pd.DataFrame,
    year: int
) -> pd.DataFrame:
    """
    Calculate polarization index for each municipality in given year
    
    Parameters:
    -----------
    votes_df : pd.DataFrame
        Voting data with columns: CD_MUNICIPIO, SG_PARTIDO, QT_VOTOS
    ideology_df : pd.DataFrame  
        Party ideology data with columns: party, ideology, year
    year : int
        Election year
    """
    logger.info(f"Calculating polarization for {year}...")
    
    # Get relevant ideology scores for this year
    ideology_year = ideology_df[ideology_df['year'] == year].copy()
    
    # Merge votes with ideology scores
    merged = votes_df.merge(
        ideology_year[['party', 'ideology']],
        left_on='SG_PARTIDO',
        right_on='party',
        how='left'
    )
    
    # Check for missing ideologies
    missing = merged[merged['ideology'].isna()]['SG_PARTIDO'].unique()
    if len(missing) > 0:
        logger.warning(f"  Missing ideology for parties: {missing}")
        logger.warning(f"  These votes will be excluded from polarization calculation")
    
    # Remove votes for parties without ideology scores
    merged = merged.dropna(subset=['ideology'])
    
    # Calculate vote shares by municipality
    municipality_totals = merged.groupby('CD_MUNICIPIO')['QT_VOTOS'].sum()
    merged['vote_share'] = merged.groupby('CD_MUNICIPIO')['QT_VOTOS'].transform(
        lambda x: x / x.sum()
    )
    
    # Calculate polarization for each municipality
    polarization_results = []
    
    for municipio, group in merged.groupby('CD_MUNICIPIO'):
        vote_shares = group['vote_share'].values
        ideologies = group['ideology'].values
        
        er_index = esteban_ray_index(vote_shares, ideologies)
        
        polarization_results.append({
            'cod_municipio': municipio,
            'ano': year,
            'polarizacao_er': er_index,
            'num_partidos': len(group),
            'total_votos': municipality_totals[municipio]
        })
    
    result_df = pd.DataFrame(polarization_results)
    logger.info(f"  Calculated polarization for {len(result_df):,} municipalities")
    
    return result_df


def main():
    """
    Main execution function
    """
    logger.info("="*60)
    logger.info("TSE Data Cleaning and Polarization Calculation")
    logger.info("="*60)
    
    # Create output directory if needed
    PROCESSED_DATA_PATH.mkdir(parents=True, exist_ok=True)
    
    # Load party ideologies
    ideology_df = load_party_ideologies()
    
    # Process each election year
    all_results = []
    
    for year in ELECTION_YEARS:
        # Load TSE data
        votes_df = load_tse_data(year)
        
        # Calculate polarization
        polarization_df = calculate_municipality_polarization(
            votes_df, 
            ideology_df, 
            year
        )
        
        all_results.append(polarization_df)
    
    # Combine all years
    final_df = pd.concat(all_results, ignore_index=True)
    
    # Sort by municipality and year
    final_df = final_df.sort_values(['cod_municipio', 'ano'])
    
    # Save processed data
    output_path = PROCESSED_DATA_PATH / "tse_cleaned.csv"
    final_df.to_csv(output_path, index=False, encoding='utf-8')
    
    logger.info("="*60)
    logger.info(f"Processing complete!")
    logger.info(f"Output saved to: {output_path}")
    logger.info(f"Total observations: {len(final_df):,}")
    logger.info(f"Municipalities: {final_df['cod_municipio'].nunique():,}")
    logger.info(f"Years: {sorted(final_df['ano'].unique())}")
    logger.info("="*60)
    
    # Summary statistics
    logger.info("\nPolarization Summary by Year:")
    summary = final_df.groupby('ano')['polarizacao_er'].describe()
    print(summary)


if __name__ == "__main__":
    main()
