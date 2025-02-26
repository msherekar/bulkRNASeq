import gseapy as gp
import pandas as pd
import mygene

def convert_ensembl_to_symbols(gene_list):
    """
    Convert Ensembl IDs to gene symbols using mygene.
    """
    try:
        mg = mygene.MyGeneInfo()
        # Query mygene for the gene info
        gene_info = mg.querymany(gene_list, scopes='ensembl.gene', fields='symbol', species='human')
        
        # Extract symbols, handling cases where the gene isn't found
        symbols = []
        for info in gene_info:
            if 'symbol' in info:
                symbols.append(info['symbol'])
        
        return symbols
    except Exception as e:
        print(f"Error converting gene IDs: {str(e)}")
        return gene_list

def perform_go_enrichment(gene_list):
    """
    Perform real GO enrichment analysis using Enrichr from gseapy.

    Args:
        gene_list (list): List of gene names/IDs.

    Returns:
        pd.DataFrame: Enriched pathways and their significance scores.
    """
    try:
        # Convert Ensembl IDs to gene symbols
        gene_symbols = convert_ensembl_to_symbols(gene_list)
        
        if not gene_symbols:
            return "Error: No valid gene symbols found after conversion"
        
        # Run enrichr with multiple relevant gene sets
        gene_sets = [
            'GO_Biological_Process_2021',
            'GO_Molecular_Function_2021',
            'GO_Cellular_Component_2021'
        ]
        
        enrichr_results = gp.enrichr(
            gene_list=gene_symbols,
            gene_sets=gene_sets,
            cutoff=0.05  # Only show terms with adjusted p-value < 0.05
        )
        
        return enrichr_results.results  # Return enrichment DataFrame
    except Exception as e:
        return f"Error in GO Enrichment Analysis: {str(e)}"

def perform_network_analysis(gene_list):
    """
    Query STRING database for real protein-protein interaction networks.

    Args:
        gene_list (list): List of gene names/IDs.

    Returns:
        dict or str: STRING API results or error message.
    """
    import requests

    # Limit the number of gene IDs to avoid overly long URLs
    max_genes = 10
    limited_gene_list = gene_list[:max_genes]
    
    # Clean gene IDs by removing version numbers (e.g., "ENSG00000115414.21" -> "ENSG00000115414")
    cleaned_gene_list = [gene.split('.')[0] for gene in limited_gene_list]
    
    string_api_url = "https://string-db.org/api/json/network"
    params = {
        "identifiers": "%0d".join(cleaned_gene_list),
        "species": 9606,  # Human (adjust for other species)
        "limit": 10
    }
    
    try:
        response = requests.get(string_api_url, params=params)
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except Exception as e:
        return f"Error in STRING Network Analysis: {str(e)}"
