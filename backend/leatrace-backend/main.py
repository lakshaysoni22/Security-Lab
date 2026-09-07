import uvicorn
import multiprocessing
import sys
from shared.logger import logger

def run_service(app_import_str: str, port: int):
    logger.info(f"Starting service {app_import_str} on port {port}")
    uvicorn.run(app_import_str, host="127.0.0.1", port=port, log_level="warning")

if __name__ == "__main__":
    # Prevent infinite spawn loops on Windows
    multiprocessing.freeze_support()

    # List of microservices and their corresponding ports
    services = [
        ("gateway.main:app", 8000),
        ("services.auth_service.main:app", 8001),
        ("services.cpos_service.main:app", 8002),
        ("services.riil_service.main:app", 8003),
        ("services.ngel_service.main:app", 8004),
        ("services.qcal_service.main:app", 8005),
        ("services.arns_service.main:app", 8006),
        ("services.blockchain_service.main:app", 8007),
        ("services.investigation_service.main:app", 8008),
    ]

    processes = []
    logger.info("Initializing LEAtTrace Microservices Cluster...")

    for service_path, port in services:
        p = multiprocessing.Process(target=run_service, args=(service_path, port))
        p.start()
        processes.append(p)

    logger.info("All microservices are active. Press Ctrl+C to terminate.")

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        logger.info("Terminating all active microservices...")
        for p in processes:
            p.terminate()
        sys.exit(0)
