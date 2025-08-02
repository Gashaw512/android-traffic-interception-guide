import os
import re
import subprocess
from logger import Logger

logger = Logger(os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs"))

# --- Constants ---
TEMP_CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_cert")

def get_cert_file():
    logger.info("\nPlease provide the path to your Burp Suite .der certificate")
    logger.info("You can drag and drop the file into this window")
    logger.info("(Type 'help' for assistance or 'exit' to cancel)")
    
    while True:
        path = input("Certificate path: ").strip()
        
        if path.lower() == 'help':
            logger.info("Help: Export Burp certificate from Proxy > Proxy Settings /Options > Import/Export CA Certificate")
            logger.info("      Save as DER format and provide the path here")
            continue
            
        if path.lower() == 'exit':
            return None
            
        path = re.sub(r'^["\']|["\']$', '', path)
        path = path.replace("\\ ", " ")
        
        if not path:
            continue
            
        if not os.path.exists(path):
            logger.error("File not found. Please try again.")
            continue
            
        if not path.lower().endswith('.der'):
            logger.warn("File doesn't have .der extension. Are you sure this is a Burp certificate?")
            confirm = input("Continue anyway? (y/n): ").strip().lower()
            if confirm != 'y':
                continue
                
        return os.path.abspath(path)

def convert_cert(cert_path, openssl_path):
    try:
        os.makedirs(TEMP_CERT_DIR, exist_ok=True)
        
        logger.info("Converting certificate format...")
        pem_file = os.path.join(TEMP_CERT_DIR, "burp.pem")
        os.makedirs(os.path.dirname(pem_file), exist_ok=True)
        
        subprocess.run(
            [openssl_path, "x509", "-inform", "der", "-in", cert_path, "-out", pem_file],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.progress("Conversion progress", 1, 3)
        
        result = subprocess.run(
            [openssl_path, "x509", "-inform", "pem", "-subject_hash_old", "-in", pem_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        cert_hash = result.stdout.splitlines()[0].strip()
        logger.progress("Processing certificate", 2, 3)
        
        hash_file = os.path.join(TEMP_CERT_DIR, f"{cert_hash}.0")
        os.rename(pem_file, hash_file)
        logger.progress("Finalizing conversion", 3, 3)
        logger.success(f"Certificate prepared: {cert_hash}.0")
        
        return hash_file, cert_hash
        
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode().strip() if isinstance(e.stderr, bytes) else e.stderr.strip()
        logger.error(f"OpenSSL command failed: {error_msg}")
        return None, None
    except Exception as e:
        logger.error(f"Certificate processing error: {str(e)}")
        logger.info("Please check your certificate file and try again")
        return None, None