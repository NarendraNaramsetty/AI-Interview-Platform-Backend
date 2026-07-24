import logging
import json

logger = logging.getLogger("ai_metrics")

class MetricsCollector:
    @staticmethod
    def increment_counter(name: str, labels: dict = None, value: int = 1):
        metric_log = {
            "metric_type": "counter",
            "metric_name": name,
            "value": value,
            "labels": labels or {}
        }
        logger.info(json.dumps(metric_log))

    @staticmethod
    def record_histogram(name: str, value: float, labels: dict = None):
        metric_log = {
            "metric_type": "histogram",
            "metric_name": name,
            "value": value,
            "labels": labels or {}
        }
        logger.info(json.dumps(metric_log))

    @staticmethod
    def set_gauge(name: str, value: float, labels: dict = None):
        metric_log = {
            "metric_type": "gauge",
            "metric_name": name,
            "value": value,
            "labels": labels or {}
        }
        logger.info(json.dumps(metric_log))
