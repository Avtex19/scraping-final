"""
Data processing module for cleaning, validation, and transformation.
Implements data pipelines for processing scraped data.
"""

import re
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Callable
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from .models import Product, AnalysisResult


class DataProcessor:
    """
    Main data processor for cleaning and transforming scraped data.
    Implements various data processing pipelines.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.processors = {}
        self.validators = {}
        self.transformers = {}
        
        # Register default processors
        self._register_default_processors()
    
    def _register_default_processors(self):
        """Register default data processors."""
        self.processors.update({
            'clean_text': self.clean_text,
            'normalize_price': self.normalize_price,
            'validate_url': self.validate_url,
            'extract_currency': self.extract_currency,
            'normalize_availability': self.normalize_availability,
            'clean_product_name': self.clean_product_name,
            'extract_brand': self.extract_brand,
            'standardize_condition': self.standardize_condition
        })
    
    def process_products(self, products: List[Dict[str, Any]], pipeline: List[str]) -> List[Product]:
        """
        Process list of product dictionaries through specified pipeline.
        
        Args:
            products: List of product dictionaries
            pipeline: List of processor names to apply
            
        Returns:
            List of processed Product objects
        """
        processed_products = []
        
        for product_data in products:
            try:
                # Apply processing pipeline
                for processor_name in pipeline:
                    if processor_name in self.processors:
                        processor = self.processors[processor_name]
                        product_data = processor(product_data)
                    else:
                        self.logger.warning(f"Unknown processor: {processor_name}")
                
                # Create Product object
                product = Product.from_dict(product_data)
                
                # Only include valid products
                if product.is_valid():
                    processed_products.append(product)
                else:
                    self.logger.debug(f"Skipped invalid product: {product.name}")
                    
            except Exception as e:
                self.logger.error(f"Error processing product: {e}")
                continue
        
        self.logger.info(f"Processed {len(processed_products)} valid products from {len(products)} total")
        return processed_products
    
    def clean_text(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean text fields in product data."""
        text_fields = ['name', 'description', 'availability', 'category', 'brand', 'seller']
        
        for field in text_fields:
            if field in data and data[field]:
                # Remove extra whitespace and special characters
                cleaned = re.sub(r'\s+', ' ', str(data[field]).strip())
                cleaned = re.sub(r'[^\w\s\-.,!?()]', '', cleaned)
                data[field] = cleaned if cleaned else None
        
        return data
    
    def normalize_price(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize price data and extract numeric values."""
        if 'price' in data and data['price']:
            price_str = str(data['price'])
            
            # Extract currency
            currency = self.extract_currency_from_price(price_str)
            if currency:
                data['currency'] = currency
            
            # Extract numeric value
            numeric_price = self.extract_numeric_price(price_str)
            if numeric_price is not None:
                data['price_numeric'] = numeric_price
        
        return data
    
    def validate_url(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and clean URLs."""
        url_fields = ['link', 'image']
        
        for field in url_fields:
            if field in data and data[field]:
                url = str(data[field])
                
                # Add protocol if missing
                if not url.startswith(('http://', 'https://')):
                    if url.startswith('//'):
                        url = 'https:' + url
                    elif url.startswith('/'):
                        # This would need the base domain, simplified here
                        data[field] = None
                        continue
                    else:
                        url = 'https://' + url
                
                # Basic URL validation
                if self._is_valid_url(url):
                    data[field] = url
                else:
                    data[field] = None
        
        return data
    
    def extract_currency(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract currency information from price."""
        if 'price' in data and data['price']:
            currency = self.extract_currency_from_price(str(data['price']))
            if currency:
                data['currency'] = currency
        
        return data
    
    def normalize_availability(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize availability status."""
        if 'availability' in data and data['availability']:
            availability = str(data['availability']).lower().strip()
            
            # Standardize availability statuses
            if any(term in availability for term in ['in stock', 'available', 'ready']):
                data['availability_status'] = 'in_stock'
            elif any(term in availability for term in ['out of stock', 'unavailable', 'sold out']):
                data['availability_status'] = 'out_of_stock'
            elif any(term in availability for term in ['limited', 'few left', 'low stock']):
                data['availability_status'] = 'limited_stock'
            else:
                data['availability_status'] = 'unknown'
        
        return data
    
    def clean_product_name(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and standardize product names."""
        if 'name' in data and data['name']:
            name = str(data['name'])
            
            # Remove promotional text
            promotional_patterns = [
                r'\b(new|sale|discount|offer|deal|free shipping)\b',
                r'\d+%\s*off',
                r'\$?\d+\s*off',
                r'\b(limited time|while supplies last)\b'
            ]
            
            for pattern in promotional_patterns:
                name = re.sub(pattern, '', name, flags=re.IGNORECASE)
            
            # Clean up extra spaces
            name = re.sub(r'\s+', ' ', name).strip()
            
            # Extract model/version if possible
            model_match = re.search(r'\b(model|version|v\.?)\s*[:.]?\s*([a-zA-Z0-9\-]+)', name, re.IGNORECASE)
            if model_match:
                data['model'] = model_match.group(2)
            
            data['name'] = name
        
        return data
    
    def extract_brand(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract brand information from product name."""
        if 'name' in data and data['name'] and 'brand' not in data:
            name = str(data['name']).lower()
            
            # Common tech brands
            tech_brands = [
                'apple', 'samsung', 'google', 'microsoft', 'amazon', 'sony', 'lg',
                'dell', 'hp', 'lenovo', 'acer', 'asus', 'nvidia', 'amd', 'intel'
            ]
            
            for brand in tech_brands:
                if brand in name:
                    data['brand'] = brand.title()
                    break
        
        return data
    
    def standardize_condition(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Standardize product condition information."""
        if 'condition' in data and data['condition']:
            condition = str(data['condition']).lower().strip()
            
            if any(term in condition for term in ['new', 'brand new', 'factory sealed']):
                data['condition_standard'] = 'new'
            elif any(term in condition for term in ['used', 'pre-owned', 'second hand']):
                data['condition_standard'] = 'used'
            elif any(term in condition for term in ['refurbished', 'renewed', 'reconditioned']):
                data['condition_standard'] = 'refurbished'
            elif any(term in condition for term in ['damaged', 'broken', 'parts']):
                data['condition_standard'] = 'damaged'
            else:
                data['condition_standard'] = 'unknown'
        
        return data
    
    def extract_numeric_price(self, price_str: str) -> Optional[float]:
        """Extract numeric price from price string."""
        if not price_str:
            return None
        
        # Remove currency symbols and extra spaces
        cleaned = re.sub(r'[^\d.,]', '', price_str)
        
        # Handle different decimal separators
        if ',' in cleaned and '.' in cleaned:
            # Both comma and period - assume period is decimal
            cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Only comma - could be thousands separator or decimal
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) <= 2:
                # Likely decimal separator
                cleaned = cleaned.replace(',', '.')
            else:
                # Likely thousands separator
                cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned)
        except ValueError:
            return None
    
    def extract_currency_from_price(self, price_str: str) -> Optional[str]:
        """Extract currency from price string."""
        if not price_str:
            return None
        
        # Currency symbols and codes
        currency_map = {
            '$': 'USD',
            '€': 'EUR',
            '£': 'GBP',
            '¥': 'JPY',
            '₹': 'INR',
            'usd': 'USD',
            'eur': 'EUR',
            'gbp': 'GBP',
            'jpy': 'JPY',
            'inr': 'INR'
        }
        
        price_lower = price_str.lower()
        
        for symbol, code in currency_map.items():
            if symbol in price_lower:
                return code
        
        return 'USD'  # Default fallback
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation."""
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return url_pattern.match(url) is not None


class ValidationPipeline:
    """Data validation pipeline for ensuring data quality."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.validators = {
            'required_fields': self._validate_required_fields,
            'price_range': self._validate_price_range,
            'url_format': self._validate_url_format,
            'text_length': self._validate_text_length,
            'duplicate_check': self._validate_duplicates
        }
    
    def validate_products(self, products: List[Product], rules: List[str]) -> List[Product]:
        """Validate products against specified rules."""
        valid_products = []
        
        for product in products:
            is_valid = True
            
            for rule in rules:
                if rule in self.validators:
                    if not self.validators[rule](product):
                        is_valid = False
                        break
            
            if is_valid:
                valid_products.append(product)
            else:
                self.logger.debug(f"Product failed validation: {product.name}")
        
        return valid_products
    
    def _validate_required_fields(self, product: Product) -> bool:
        """Validate that required fields are present."""
        required = ['name', 'price', 'link']
        return all(getattr(product, field, None) for field in required)
    
    def _validate_price_range(self, product: Product) -> bool:
        """Validate price is within reasonable range."""
        if not product.price:
            return False
        try:
            price = float(product.price)
            return 0.01 <= price <= 100000  # Reasonable price range
        except (ValueError, TypeError):
            return False
    
    def _validate_url_format(self, product: Product) -> bool:
        """Validate URL format."""
        if not product.link:
            return False
        return product.link.startswith(('http://', 'https://'))
    
    def _validate_text_length(self, product: Product) -> bool:
        """Validate text field lengths."""
        if product.name and len(product.name) > 500:
            return False
        return True
    
    def _validate_duplicates(self, product: Product) -> bool:
        """Basic duplicate validation (would need more context for full implementation)."""
        return True  # Placeholder - would implement with database context 