import logging
import queue
import threading
import time

from .mail import MockMailClient

log = logging.getLogger(__name__)


class WelcomeEmailWorker:
    """Simple threaded background worker that processes welcome-email jobs."""

    def __init__(self):
        self._queue = queue.Queue()
        self._stop = threading.Event()
        self._mail = MockMailClient()
        self._thread = threading.Thread(target=self._run, name="welcome-email-worker", daemon=True)

    def start(self):
        self._thread.start()
        log.info("Welcome email worker started (mock mail)")

    def stop(self):
        self._stop.set()
        self._queue.put(None)
        self._thread.join(timeout=2)

    def enqueue(self, lead_id, name, email):
        self._queue.put({"lead_id": lead_id, "name": name, "email": email})

    def _run(self):
        while not self._stop.is_set():
            job = self._queue.get()
            if job is None:
                break
            try:
                log.info("Queueing mocked welcome email for lead id=%s", job["lead_id"])
                time.sleep(0.5)
                self._mail.send(
                    job["name"],
                    job["email"],
                    "Welcome!",
                    f"Thanks for signing up, {job['name']}.",
                )
            except Exception:
                log.exception("Failed to process welcome email job")
            finally:
                self._queue.task_done()
