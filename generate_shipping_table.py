#!/usr/bin/env python3
"""
Total Express Shipping Cost Table Generator

This script generates a comprehensive shipping cost table for Total Express
by querying their SOAP API for various CEP ranges and weight ranges.

The table format includes:
- ZipCodeStart, ZipCodeEnd: CEP ranges
- WeightStart, WeightEnd: Weight ranges in grams
- AbsoluteMoneyCost: Shipping cost in BRL
- TimeCost: Delivery time in days
"""

import requests
import json
import csv
import time
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging
from urllib.parse import urlparse
import base64
import xml.etree.ElementTree as ET
from io import StringIO
import sys
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('shipping_table_generator.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ShippingQuery:
    """Represents a single shipping cost query"""
    cep_start: int
    cep_end: int
    weight_start: int  # in grams
    weight_end: int    # in grams
    service_type: str  # 'STD' or 'EXP'

@dataclass
class ShippingResult:
    """Represents the result of a shipping cost query"""
    cep_start: int
    cep_end: int
    weight_start: int
    weight_end: int
    cost: float
    delivery_days: int
    service_type: str

class TotalExpressAPI:
    """Handles communication with Total Express SOAP API"""

    WSDL_URL = "https://edi.totalexpress.com.br/webservice_calculo_frete.php?wsdl"
    BASE_URL = "https://edi.totalexpress.com.br/webservice_calculo_frete.php"

    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.session = requests.Session()

        # Set up authentication
        auth_string = f"{username}:{password}"
        auth_bytes = auth_string.encode('utf-8')
        auth_b64 = base64.b64encode(auth_bytes).decode('utf-8')
        self.auth_header = f"Basic {auth_b64}"

        self.session.headers.update({
            'Authorization': self.auth_header,
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': ''
        })

    def get_wsdl(self) -> Optional[str]:
        """Fetch the WSDL definition"""
        try:
            response = self.session.get(self.WSDL_URL)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch WSDL: {e}")
            return None

    def calculate_shipping_cost(self, params: Dict) -> Optional[Dict]:
        """
        Calculate shipping cost using SOAP API

        Args:
            params: Dictionary containing:
                - TipoServico: Service type ('STD' or 'EXP')
                - CepDestino: Destination CEP
                - Peso: Weight in kg (formatted as "10,00")
                - ValorDeclarado: Declared value
                - TipoEntrega: Delivery type (0)
                - ServicoCOD: Cash on delivery (false)
                - Altura: Height in cm
                - Largura: Width in cm
                - Profundidade: Length in cm
        """
        # First get the WSDL
        wsdl_content = self.get_wsdl()
        if not wsdl_content:
            return None

        try:
            # Create SOAP client from WSDL
            from zeep import Client, Settings
            from zeep.transports import Transport

            # Set up transport with authentication
            transport = Transport(session=self.session)

            # Configure settings
            settings = Settings(strict=False, xml_huge_tree=True)

            # Create client
            client = Client(wsdl=wsdl_content, transport=transport, settings=settings)

            # Make the SOAP call
            result = client.service.calcularFrete(**params)

            logger.info(f"API Response: {result}")

            if hasattr(result, 'CodigoProc') and result.CodigoProc == 1:
                if hasattr(result, 'DadosFrete'):
                    return {
                        'cost': float(str(result.DadosFrete.ValorServico).replace(',', '.')),
                        'delivery_days': int(result.DadosFrete.Prazo),
                        'success': True
                    }

            return None

        except Exception as e:
            logger.error(f"SOAP call failed: {e}")
            return None

class ShippingTableGenerator:
    """Generates shipping cost tables"""

    def __init__(self, api: TotalExpressAPI):
        self.api = api

    def generate_cep_ranges(self) -> List[Tuple[int, int]]:
        """
        Generate complete Brazilian CEP ranges for all states and territories.
        Covers all 26 states + Federal District with official CEP range assignments.
        """
        ranges = [
            (1000000, 1999999), # São Paulo (SP) - 01000-000 to 19999-999
            (2000000, 2899999), # Rio de Janeiro (RJ) - 20000-000 to 28999-999
            (2900000, 2999999), # Espírito Santo (ES) - 29000-000 to 29999-999
            (3000000, 3999999), # Minas Gerais (MG) - 30000-000 to 39999-999
            (4000000, 4899999), # Bahia (BA) - 40000-000 to 48999-999
            (4900000, 4999999), # Sergipe (SE) - 49000-000 to 49999-999
            (5000000, 5699999), # Pernambuco (PE) - 50000-000 to 56999-999
            (5700000, 5799999), # Alagoas (AL) - 57000-000 to 57999-999
            (5800000, 5899999), # Paraíba (PB) - 58000-000 to 58999-999
            (5900000, 5999999), # Rio Grande do Norte (RN) - 59000-000 to 59999-999
            (6000000, 6399999), # Ceará (CE) - 60000-000 to 63999-999
            (6400000, 6499999), # Piauí (PI) - 64000-000 to 64999-999
            (6500000, 6599999), # Maranhão (MA) - 65000-000 to 65999-999
            (6600000, 6889999), # Pará (PA) - 66000-000 to 68899-999
            (6890000, 6899999), # Amapá (AP) - 68900-000 to 68999-999
            (7000000, 7279999), # Distrito Federal (DF) - 70000-000 to 72799-999
            (7280000, 7679999), # Goiás (GO) - 72800-000 to 76799-999
            (7680000, 7699999), # Rondônia (RO) - 76800-000 to 76999-999
            (6990000, 6999999), # Acre (AC) - 69900-000 to 69999-999
            (7800000, 7889999), # Mato Grosso (MT) - 78000-000 to 78899-999
            (7900000, 7999999), # Mato Grosso do Sul (MS) - 79000-000 to 79999-999
            (8000000, 8799999), # Paraná (PR) - 80000-000 to 87999-999
            (8800000, 8999999), # Santa Catarina (SC) - 88000-000 to 89999-999
            (9000000, 9999999), # Rio Grande do Sul (RS) - 90000-000 to 99999-999
            (7700000, 7799999), # Tocantins (TO) - 77000-000 to 77999-999
            (6930000, 6939999), # Roraima (RR) - 69300-000 to 69399-999
        ]
        return ranges

    def generate_weight_ranges(self) -> List[Tuple[int, int]]:
        """Generate weight ranges in grams"""
        ranges = [
            (1, 250),
            (251, 500),
            (501, 750),
            (751, 1000),
            (1001, 2000),
            (2001, 3000),
            (3001, 4000),
            (4001, 5000),
            (5001, 6000),
            (6001, 7000),
            (7001, 8000),
            (8001, 9000),
            (9001, 10000),
        ]
        return ranges

    def format_weight_for_api(self, weight_grams: int) -> str:
        """Convert weight from grams to kg and format for API"""
        weight_kg = weight_grams / 1000.0
        return ".2f"

    def format_cep_for_api(self, cep: int) -> str:
        """Format CEP for API (add leading zeros if needed)"""
        return "08d"

    def generate_table(self, service_type: str = 'STD', output_file: str = 'shipping_table.csv') -> None:
        """
        Generate the complete shipping cost table

        Args:
            service_type: 'STD' for Standard or 'EXP' for Express
            output_file: Output CSV file path (will be saved in ./output/ folder)
        """
        # Create output directory if it doesn't exist
        output_dir = os.path.join(os.path.dirname(__file__), 'output')
        os.makedirs(output_dir, exist_ok=True)

        # Update output file path to include output directory
        if not os.path.dirname(output_file):
            output_file = os.path.join(output_dir, output_file)
        cep_ranges = self.generate_cep_ranges()
        weight_ranges = self.generate_weight_ranges()

        results = []
        total_queries = len(cep_ranges) * len(weight_ranges)

        logger.info(f"Starting table generation for {service_type} service")
        logger.info(f"Total queries to make: {total_queries}")

        query_count = 0

        for cep_start, cep_end in cep_ranges:
            # Use a representative CEP from the range for API calls
            # In production, you might want to test multiple CEPs per range
            test_cep = cep_start + (cep_end - cep_start) // 2

            for weight_start, weight_end in weight_ranges:
                query_count += 1

                # Use average weight for the range
                test_weight = (weight_start + weight_end) // 2

                logger.info(f"Processing query {query_count}/{total_queries}: "
                          f"CEP {cep_start}-{cep_end}, Weight {weight_start}-{weight_end}g")

                # Prepare API parameters
                params = {
                    'TipoServico': service_type,
                    'CepDestino': self.format_cep_for_api(test_cep),
                    'Peso': self.format_weight_for_api(test_weight),
                    'ValorDeclarado': '0,00',  # No declared value for basic shipping
                    'TipoEntrega': 0,
                    'ServicoCOD': False,
                    'Altura': '10,00',   # Default dimensions
                    'Largura': '15,00',
                    'Profundidade': '20,00'
                }

                # Make API call
                api_result = self.api.calculate_shipping_cost(params)

                if api_result:
                    result = ShippingResult(
                        cep_start=cep_start,
                        cep_end=cep_end,
                        weight_start=weight_start,
                        weight_end=weight_end,
                        cost=api_result['cost'],
                        delivery_days=api_result['delivery_days'],
                        service_type=service_type
                    )
                    results.append(result)
                    logger.info(f"Success: Cost R$ {result.cost:.2f}, {result.delivery_days} days")
                else:
                    logger.warning(f"Failed to get result for CEP {test_cep}, weight {test_weight}g")
                    # You might want to add a default/fallback value here

                # Add delay to avoid overwhelming the API
                time.sleep(1)

        # Write results to CSV
        self.write_csv(results, output_file)
        logger.info(f"Table generation completed. Results saved to {output_file}")

    def write_csv(self, results: List[ShippingResult], output_file: str) -> None:
        """Write results to CSV file"""
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['ZipCodeStart', 'ZipCodeEnd', 'WeightStart', 'WeightEnd',
                         'AbsoluteMoneyCost', 'TimeCost']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()

            for result in results:
                writer.writerow({
                    'ZipCodeStart': result.cep_start,
                    'ZipCodeEnd': result.cep_end,
                    'WeightStart': result.weight_start,
                    'WeightEnd': result.weight_end,
                    'AbsoluteMoneyCost': ".2f",
                    'TimeCost': result.delivery_days
                })

def main():
    """Main function"""
    # Load environment variables from .env file
    load_dotenv()

    # You need to provide your Total Express API credentials
    # These should be stored securely in a .env file
    USERNAME = os.getenv('TOTAL_EXPRESS_USERNAME', 'your_username')
    PASSWORD = os.getenv('TOTAL_EXPRESS_PASSWORD', 'your_password')

    if USERNAME == 'your_username' or PASSWORD == 'your_password':
        logger.error("Please set TOTAL_EXPRESS_USERNAME and TOTAL_EXPRESS_PASSWORD in your .env file")
        logger.info("Copy env-example.txt to .env and fill in your actual credentials")
        sys.exit(1)

    # Initialize API client
    api = TotalExpressAPI(USERNAME, PASSWORD)

    # Initialize table generator
    generator = ShippingTableGenerator(api)

    # Generate tables for both services (saved in ./output/ folder)
    logger.info("Generating Standard shipping table...")
    generator.generate_table('STD', 'total_express_standard.csv')

    logger.info("Generating Express shipping table...")
    generator.generate_table('EXP', 'total_express_express.csv')

    logger.info("All tables generated successfully!")

if __name__ == "__main__":
    main()
