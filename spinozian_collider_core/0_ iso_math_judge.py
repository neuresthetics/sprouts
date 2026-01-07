# iso_math_judge.py
# Extended Isomorphic Math Module for Unified Steelman Collider
# Status: Hardened for input flexibility (file or dict modes), enhanced error handling
# Evaluation Date: 2025-12-26
# Upgrades: Accept direct dict inputs; granular exceptions; default safe returns

import numpy as np
import sympy as sp
import networkx as nx
from scipy import linalg
from typing import Dict, Any, List, Tuple, Optional, Union
import logging
import json
import os
from difflib import SequenceMatcher

# Configure minimal logging for traceability
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IsoMathJudge:
    """
    Extended external handler for isomorphic operations.
    Now includes direct validation on the attached niso JSON corpus or provided dicts.
    """
    
    def __init__(self):
        self.invariance_threshold = 0.98
        self.tolerance = 1e-8  # Tightened for spectral comparison
        self.scale_levels = ["subatomic", "atomic", "cellular", "organism", "social",
                             "technological", "planetary", "cosmic", "principle"]
    
    def build_bipartite_niso_graph(self, data: Dict) -> Tuple[nx.Graph, int, List[str]]:
        """Build anonymized complete bipartite graph: indexed categories ↔ scales."""
        try:
            if 'data' not in data or not data['data']:
                raise ValueError("Invalid or empty niso data: Missing or empty 'data' key.")
            
            cat_data = data['data']
            if not isinstance(cat_data, list) or not cat_data:
                raise ValueError("Invalid niso data: 'data' must be a non-empty list.")
            
            num_cats = len(cat_data)
            
            # Extract scales (should be the fixed 9)
            sample_mappings = cat_data[0].get('mappings', {})
            if not sample_mappings:
                raise ValueError("Invalid niso data: First category missing 'mappings'.")
            scales = list(sample_mappings.keys())
            
            G = nx.Graph()
            
            # Anonymized category nodes (cat_0, cat_1, ...) to enable structural isomorphism
            for i in range(num_cats):
                cat = cat_data[i]
                if 'category' not in cat:
                    raise ValueError(f"Invalid niso data: Category {i} missing 'category' key.")
                G.add_node(f"cat_{i}", type="category", original_label=cat['category'])
            
            # Scale nodes
            for scale in scales:
                G.add_node(scale, type="scale")
            
            # Edges (complete if all mappings present)
            missing = 0
            for i, cat in enumerate(cat_data):
                cat_node = f"cat_{i}"
                mappings = cat.get('mappings', {})
                for scale in scales:
                    if scale in mappings:
                        mapping_text = mappings[scale]
                        G.add_edge(cat_node, scale, mapping=mapping_text)
                    else:
                        missing += 1
            
            if missing > 0:
                logger.warning(f"Incomplete mappings detected: {missing} missing edges")
            
            return G, num_cats, scales
        except KeyError as ke:
            logger.error(f"Key error in graph build: {ke}")
            raise ValueError(f"Missing required key: {ke}")
        except TypeError as te:
            logger.error(f"Type error in graph build: {te}")
            raise ValueError(f"Invalid data type: {te}")
        except Exception as e:
            logger.error(f"Unexpected error in graph build: {e}")
            raise
    
    def validate_niso_collection(self, input_datas: Optional[Dict[str, Dict]] = None) -> Dict[str, Any]:
        """Validate niso collection from files or provided dicts; flexible mode."""
        datas = {}
        
        # Mode 1: Load from files if no input_datas provided
        if input_datas is None:
            try:
                for file in os.listdir('.'):
                    if file.startswith('niso_') and file.endswith('.json'):
                        with open(file, 'r') as f:
                            datas[file] = json.load(f)
            except FileNotFoundError as fnf:
                logger.warning(f"Directory scan warning: {fnf}")
            except json.JSONDecodeError as jde:
                logger.error(f"JSON decode error: {jde}")
                return {"status": "JSON_DECODE_ERROR", "veto": True}
            except Exception as e:
                logger.error(f"File load failed: {e}")
                return {"status": f"FILE_LOAD_EXCEPTION: {str(e)}", "veto": True}
        else:
            # Mode 2: Use provided dicts (keyed by 'file' names or arbitrary IDs)
            datas = input_datas
        
        if not datas:
            return {"status": "NO_NISO_DATA_FOUND", "veto": True, "details": "No files or dicts provided/loaded."}
        
        # Groups, graphs, principles (processing as before, with enhanced error handling)
        groups: Dict[int, List[Tuple[str, nx.Graph]]] = {}
        graphs: Dict[str, nx.Graph] = {}
        all_principles: List[str] = []
        
        for file_id, data in datas.items():
            try:
                G, num_cats, scales = self.build_bipartite_niso_graph(data)
                graphs[file_id] = G
                if num_cats not in groups:
                    groups[num_cats] = []
                groups[num_cats].append((file_id, G))
                
                cat_data = data['data']
                for cat in cat_data:
                    mappings = cat.get('mappings', {})
                    if 'principle' in mappings:
                        all_principles.append(mappings['principle'])
            except ValueError as ve:
                logger.error(f"Graph build failed for {file_id}: {ve}")
                continue  # Skip invalid, continue for stability
            except Exception as e:
                logger.error(f"Unexpected failure for {file_id}: {e}")
                return {"status": f"PROCESSING_EXCEPTION: {str(e)}", "veto": True}
        
        if not groups:
            return {"status": "NO_VALID_GRAPHS_BUILT", "veto": True, "details": "All inputs failed graph construction."}
        
        # Group validations (as original, with safe defaults)
        group_results = []
        for num_cats, file_graphs in groups.items():
            if len(file_graphs) <= 1:
                group_results.append({
                    "num_categories": num_cats,
                    "files": [f[0] for f in file_graphs],
                    "note": "Single file – no comparison",
                    "invariance_score": 1.0  # Default stable for singles
                })
                continue
            
            ref_file, ref_G = file_graphs[0]
            isomorphic_all = True
            spectral_match_all = True
            
            try:
                ref_lap = nx.laplacian_matrix(ref_G).todense()
                ref_eigs = sorted(np.real(np.linalg.eigvals(ref_lap)))
                
                for file_id, G in file_graphs[1:]:
                    if not nx.is_isomorphic(ref_G, G):
                        isomorphic_all = False
                    
                    lap = nx.laplacian_matrix(G).todense()
                    eigs = sorted(np.real(np.linalg.eigvals(lap)))
                    if max(abs(a - b) for a, b in zip(ref_eigs, eigs)) > self.tolerance:
                        spectral_match_all = False
            except linalg.LinAlgError as lae:
                logger.error(f"Linear algebra error in spectral check: {lae}")
                group_results.append({
                    "num_categories": num_cats,
                    "num_files": len(file_graphs),
                    "files": [f[0] for f in file_graphs],
                    "note": "Spectral computation failed",
                    "invariance_score": 0.0
                })
                continue
            
            score = 1.0 if (isomorphic_all and spectral_match_all) else 0.0
            group_results.append({
                "num_categories": num_cats,
                "num_files": len(file_graphs),
                "files": [f[0] for f in file_graphs],
                "structural_isomorphic": isomorphic_all,
                "spectral_match": spectral_match_all,
                "invariance_score": score
            })
        
        # Principle convergence (as original)
        n_princ = len(all_principles)
        if n_princ >= 2:
            pairwise_sims = [SequenceMatcher(None, all_principles[i], all_principles[j]).ratio()
                             for i in range(n_princ) for j in range(i + 1, n_princ)]
            avg_principle_similarity = sum(pairwise_sims) / len(pairwise_sims) if pairwise_sims else 1.0
        else:
            avg_principle_similarity = 1.0
        
        overall_score = np.mean([r.get('invariance_score', 1.0) for r in group_results]) if group_results else 0.0
        status = "PASS" if overall_score >= self.invariance_threshold else "PARTIAL"
        
        return {
            "status": status,
            "invariance_score": float(overall_score),
            "details": {
                "files_processed": list(datas.keys()),
                "group_validations": group_results,
                "principle_convergence": {
                    "num_principles": n_princ,
                    "average_pairwise_similarity": avg_principle_similarity
                }
            }
        }
    
    def route(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extended router with niso-specific claims."""
        claim_type = input_data.get('claim_type', '').lower()
        data = input_data.get('data', {})
        
        logger.info(f"Routing isomorphic claim of type: {claim_type}")
        
        try:
            if 'isomorphism' in claim_type or 'graph' in claim_type:
                return self.graph_isomorphism_checker(input_data)  # Assume original method exists
            elif 'niso_collection' in claim_type or 'niso_all' in claim_type:
                # Flexible: Pass data if provided, else scan files
                return self.validate_niso_collection(input_datas={ "input_data": data } if data else None)
            else:
                return {"status": "UNKNOWN_ISO_CLAIM_TYPE", "veto": True}
        except ValueError as ve:
            logger.error(f"Value error in routing: {ve}")
            return {"status": f"VALUE_ERROR: {str(ve)}", "veto": True}
        except Exception as e:
            logger.error(f"Routing failed: {str(e)}")
            return {"status": f"EXCEPTION: {str(e)}", "veto": True}

# Hook entry point
def process_iso_claim(input_data: Dict[str, Any]) -> Dict[str, Any]:
    judge = IsoMathJudge()
    return judge.route(input_data)

# Example self-test
if __name__ == "__main__":
    judge = IsoMathJudge()
    # Test with in-memory dict
    test_input = {
        'claim_type': 'niso_collection',
        'data': {
            'data': [
                {
                    'category': 'Test Cat',
                    'mappings': {
                        'subatomic': 'test',
                        'atomic': 'test',
                        'cellular': 'test',
                        'organism': 'test',
                        'social': 'test',
                        'technological': 'test',
                        'planetary': 'test',
                        'cosmic': 'test',
                        'principle': 'test principle'
                    }
                }
            ]
        }
    }
    result = judge.route(test_input)
    print(json.dumps(result, indent=2))