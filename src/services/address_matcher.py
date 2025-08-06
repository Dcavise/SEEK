"""
Address Matching Service

Handles fuzzy address matching for FOIA data integration with confidence scoring.
Implements multi-tier matching strategy: exact -> normalized -> fuzzy.
"""

import logging
import re
from typing import Optional

import usaddress
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class AddressMatcher:
    """
    Advanced address matching service with fuzzy logic and confidence scoring.

    Used for matching FOIA addresses against parcel database addresses
    with multiple matching strategies and validation.
    """

    def __init__(self, confidence_threshold: float = 0.75):
        self.confidence_threshold = confidence_threshold
        self.stats = {
            "exact_matches": 0,
            "normalized_matches": 0,
            "fuzzy_matches": 0,
            "no_matches": 0,
            "total_processed": 0,
        }

    def normalize_address(self, address: str) -> str:
        """
        Normalize address for consistent matching.

        Handles common abbreviations, directionals, and formatting issues.
        """
        if not address or not isinstance(address, str):
            return ""

        addr = address.upper().strip()
        addr = re.sub(r"\s+", " ", addr)  # Remove extra whitespace

        # Remove suite/unit information for better matching
        addr = re.sub(r"\b(SUITE?|UNIT|APT|APARTMENT|STE|#)\s*[A-Z0-9-]+\b", "", addr, flags=re.IGNORECASE)

        # Normalize street types
        street_type_mapping = {
            r"\bST\b": "STREET",
            r"\bAVE\b": "AVENUE",
            r"\bDR\b": "DRIVE",
            r"\bCT\b": "COURT",
            r"\bLN\b": "LANE",
            r"\bRD\b": "ROAD",
            r"\bBLVD\b": "BOULEVARD",
            r"\bPKWY\b": "PARKWAY",
            r"\bCIR\b": "CIRCLE",
            r"\bPL\b": "PLACE",
        }

        for pattern, replacement in street_type_mapping.items():
            addr = re.sub(pattern, replacement, addr)

        # Normalize directionals
        directional_mapping = {
            r"\bN\b": "NORTH",
            r"\bS\b": "SOUTH",
            r"\bE\b": "EAST",
            r"\bW\b": "WEST",
            r"\bNE\b": "NORTHEAST",
            r"\bNW\b": "NORTHWEST",
            r"\bSE\b": "SOUTHEAST",
            r"\bSW\b": "SOUTHWEST",
        }

        for pattern, replacement in directional_mapping.items():
            addr = re.sub(pattern, replacement, addr)

        return addr.strip()

    def extract_street_number(self, address: str) -> Optional[str]:
        """Extract street number from address for validation."""
        try:
            parsed = usaddress.parse(address)
            for component, label in parsed:
                if label == "AddressNumber":
                    return component
        except Exception:
            # Fallback: extract first number sequence
            match = re.match(r"^(\d+)", address.strip())
            if match:
                return match.group(1)
        return None

    def calculate_similarity(self, addr1: str, addr2: str) -> float:
        """Calculate similarity score between two addresses."""
        if not addr1 or not addr2:
            return 0.0

        # Exact match
        if addr1 == addr2:
            return 1.0

        # Use multiple fuzzy matching algorithms
        ratio_score = fuzz.ratio(addr1, addr2) / 100.0
        token_sort_score = fuzz.token_sort_ratio(addr1, addr2) / 100.0
        token_set_score = fuzz.token_set_ratio(addr1, addr2) / 100.0

        # Weight the scores (token_set is most robust for addresses)
        return ratio_score * 0.3 + token_sort_score * 0.3 + token_set_score * 0.4

    def find_address_matches(self, foia_address: str, candidate_addresses: list[dict]) -> list[dict]:
        """
        Find matching addresses from candidate list with confidence scores.

        Args:
            foia_address: Address from FOIA data
            candidate_addresses: List of {'id': str, 'address': str} from database

        Returns:
            List of matches with confidence scores, sorted by confidence
        """
        if not foia_address or not candidate_addresses:
            return []

        foia_normalized = self.normalize_address(foia_address)
        foia_street_num = self.extract_street_number(foia_address)

        matches = []

        for candidate in candidate_addresses:
            candidate_addr = candidate.get("address", "")
            candidate_normalized = self.normalize_address(candidate_addr)
            candidate_street_num = self.extract_street_number(candidate_addr)

            # Skip if different street numbers (prevents false positives)
            if foia_street_num and candidate_street_num and foia_street_num != candidate_street_num:
                continue

            # Calculate similarity
            similarity = self.calculate_similarity(foia_normalized, candidate_normalized)

            if similarity >= self.confidence_threshold:
                match_type = self._determine_match_type(similarity)
                matches.append(
                    {
                        "parcel_id": candidate["id"],
                        "database_address": candidate_addr,
                        "foia_address": foia_address,
                        "confidence": similarity,
                        "match_type": match_type,
                        "normalized_foia": foia_normalized,
                        "normalized_db": candidate_normalized,
                    }
                )

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        return matches

    def _determine_match_type(self, confidence: float) -> str:
        """Determine match type based on confidence score."""
        if confidence >= 0.95:
            return "exact_match"
        if confidence >= 0.85:
            return "high_confidence"
        if confidence >= self.confidence_threshold:
            return "medium_confidence"
        return "low_confidence"

    def batch_match_addresses(self, foia_addresses: list[str], database_query_func) -> dict[str, list[dict]]:
        """
        Batch process multiple FOIA addresses against database.

        Args:
            foia_addresses: List of FOIA addresses to match
            database_query_func: Function that takes address and returns candidates

        Returns:
            Dictionary mapping FOIA address to list of matches
        """
        results = {}

        for foia_addr in foia_addresses:
            self.stats["total_processed"] += 1

            # Get candidates from database
            candidates = database_query_func(foia_addr)

            # Find matches
            matches = self.find_address_matches(foia_addr, candidates)

            # Update statistics
            if not matches:
                self.stats["no_matches"] += 1
            else:
                best_match = matches[0]
                if best_match["match_type"] == "exact_match":
                    self.stats["exact_matches"] += 1
                elif best_match["confidence"] >= 0.85:
                    self.stats["normalized_matches"] += 1
                else:
                    self.stats["fuzzy_matches"] += 1

            results[foia_addr] = matches

        return results

    def get_matching_stats(self) -> dict:
        """Get current matching statistics."""
        if self.stats["total_processed"] == 0:
            return self.stats

        return {
            **self.stats,
            "exact_match_rate": self.stats["exact_matches"] / self.stats["total_processed"],
            "total_match_rate": (
                self.stats["exact_matches"] + self.stats["normalized_matches"] + self.stats["fuzzy_matches"]
            )
            / self.stats["total_processed"],
        }


def match_addresses(foia_addresses: list[str], parcel_data) -> list[dict]:
    """
    Simple address matching function for testing.
    
    Args:
        foia_addresses: List of FOIA addresses to match
        parcel_data: DataFrame with parcel data including addresses
        
    Returns:
        List of match results with confidence scores
    """
    matcher = AddressMatcher(confidence_threshold=0.75)
    
    # Convert parcel data to candidate format
    candidates = []
    for _, row in parcel_data.iterrows():
        candidates.append({
            'id': row['parcel_number'],
            'address': row['address']
        })
    
    results = []
    for foia_addr in foia_addresses:
        matches = matcher.find_address_matches(foia_addr, candidates)
        if matches:
            results.extend(matches)
    
    return results
