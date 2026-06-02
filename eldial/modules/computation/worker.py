"""Фоновый обработчик задач моделирования."""

import threading
from collections.abc import Callable
from queue import Queue

from eldial.domain.entities import ModelResult, SimulationParameters, SimulationRun
from eldial.modules.computation.engine import ComputationEngine


class SimulationWorker(threading.Thread):
    """Поток выполнения расчёта без блокировки UI."""

    def __init__(
        self,
        simulation: SimulationRun,
        parameters: SimulationParameters,
        on_complete: Callable[[ModelResult], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
    ):
        super().__init__(daemon=True)
        self.simulation = simulation
        self.parameters = parameters
        self.on_complete = on_complete
        self.on_error = on_error
        self._engine = ComputationEngine()

    def run(self) -> None:
        try:
            result = self._engine.run_simulation(self.simulation, self.parameters)
            if self.on_complete:
                self.on_complete(result)
        except Exception as exc:
            if self.on_error:
                self.on_error(exc)


class SimulationScheduler:
    """Планировщик очереди вычислительных задач."""

    def __init__(self, max_workers: int = 2):
        self._queue: Queue = Queue()
        self._max_workers = max_workers
        self._workers: list[SimulationWorker] = []

    def submit(self, worker: SimulationWorker) -> None:
        self._queue.put(worker)
        worker.start()
        self._workers.append(worker)

    def pending_count(self) -> int:
        return self._queue.qsize()
