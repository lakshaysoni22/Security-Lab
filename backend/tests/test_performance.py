import time
from app.blockchain_classifier import blockchain_classifier

def test_address_classifier_latency_benchmark():
    addresses = [
        "0x71c20e241775e5332f143715df332f143789a71b",
        "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
        "1AGNa15ZQXAZUgFiqJ2i7Z2DPU2J6hW62i",
        "HN7cE2q4gY6hy9WcH1b7tD5Ji1b2x7T1b",
        "TY1b2x7T1b2x7T1b2x7T1b2x7T1b2x7T1b"
    ]
    
    # Target: average classification latency should be less than 2 milliseconds (0.002 seconds) per address
    t_start = time.perf_counter()
    for address in addresses:
        for _ in range(100): # Run 100 times to accumulate sample size
            blockchain_classifier.classify_address(address)
    t_end = time.perf_counter()
    
    avg_latency = (t_end - t_start) / (len(addresses) * 100)
    assert avg_latency < 0.002 # Must be ultra fast (under 2ms)
