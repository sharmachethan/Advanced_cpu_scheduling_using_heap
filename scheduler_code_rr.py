import heapq
import random
from collections import deque
from typing import List
from datetime import datetime


class Process:
    """Represents a process with comprehensive scheduling attributes"""

    def __init__(self, pid, arrival, burst, priority, process_type="CPU"):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.priority = priority
        self.process_type = process_type
        self.remaining = burst
        self.start = None
        self.finish = None
        self.waiting = 0
        self.turnaround = 0
        self.response_time = None
        self.context_switches = 0
        self.execution_history = []
        self.state = "NEW"

    def __repr__(self):
        return f"Process({self.pid}, Priority={self.priority}, Burst={self.burst})"

    def calculate_metrics(self):
        """Accurate waiting, turnaround, and response calculations"""
        if self.start is not None and self.finish is not None:
            # Total CPU active time = total execution intervals
            active_time = len(self.execution_history)
            self.turnaround = self.finish - self.arrival
            self.waiting = self.turnaround - active_time
            if self.response_time is None:
                self.response_time = self.start - self.arrival


class ProcessScheduler:
    """Advanced heap-based scheduler with Round Robin support"""

    def __init__(self, processes: List[Process], mode="preemptive", algorithm="priority", quantum=2):
        self.processes = sorted(processes, key=lambda p: p.arrival)
        self.mode = mode
        self.algorithm = algorithm.lower()
        self.quantum = quantum
        self.completed = []
        self.context_switches = 0
        self.cpu_utilization = 0
        self.throughput = 0
        self.idle_time = 0
        self.execution_log = []

    def schedule(self):
        """Main scheduling entry point"""
        if self.algorithm == "rr":
            return self._round_robin()
        else:
            return self._heap_based_schedule()

    # ===============================================================
    # HEAP-BASED SCHEDULERS: PRIORITY, SJF, FCFS
    # ===============================================================
    def _heap_based_schedule(self):
        clock = 0
        ready_heap = []
        process_index = 0
        running = None
        total_processes = len(self.processes)
        last_process = None

        while process_index < total_processes or ready_heap or running:
            # Add processes that have arrived
            while process_index < total_processes and self.processes[process_index].arrival <= clock:
                proc = self.processes[process_index]
                proc.state = "READY"
                if self.algorithm == "priority":
                    heapq.heappush(ready_heap, (-proc.priority, proc.arrival, proc.pid, proc))
                elif self.algorithm == "sjf":
                    heapq.heappush(ready_heap, (proc.remaining, proc.arrival, proc.pid, proc))
                elif self.algorithm == "fcfs":
                    heapq.heappush(ready_heap, (proc.arrival, proc.pid, proc))
                self.execution_log.append(f"[Time {clock}] {proc.pid} arrived")
                process_index += 1

            # Preemption check
            if running and self.mode == "preemptive" and ready_heap:
                should_preempt = False
                if self.algorithm == "priority":
                    highest_priority = -ready_heap[0][0]
                    should_preempt = highest_priority > running.priority
                elif self.algorithm == "sjf":
                    shortest = ready_heap[0][0]
                    should_preempt = shortest < running.remaining
                if should_preempt:
                    running.state = "READY"
                    heapq.heappush(
                        ready_heap,
                        (-running.priority if self.algorithm == "priority" else running.remaining,
                         running.arrival, running.pid, running),
                    )
                    running = None
                    self.context_switches += 1

            # Pick next process if CPU is idle
            if not running and ready_heap:
                if self.algorithm == "fcfs":
                    _, _, running = heapq.heappop(ready_heap)
                else:
                    *_, running = heapq.heappop(ready_heap)
                if running.start is None:
                    running.start = clock
                running.state = "RUNNING"
                if last_process and last_process.pid != running.pid:
                    self.context_switches += 1
                last_process = running

            # Execute one time unit
            if running:
                running.remaining -= 1
                running.execution_history.append(clock)
                if running.remaining == 0:
                    running.finish = clock + 1
                    running.state = "TERMINATED"
                    running.calculate_metrics()
                    self.completed.append(running)
                    running = None
            else:
                self.idle_time += 1
            clock += 1

        self.calculate_system_metrics(clock)
        return self.completed

    # ===============================================================
    # ROUND ROBIN SCHEDULER
    # ===============================================================
    def _round_robin(self):
        clock = 0
        ready_queue = deque()
        process_index = 0
        total_processes = len(self.processes)
        quantum = self.quantum

        while process_index < total_processes or ready_queue:
            # Add processes that arrived
            while process_index < total_processes and self.processes[process_index].arrival <= clock:
                proc = self.processes[process_index]
                proc.state = "READY"
                ready_queue.append(proc)
                self.execution_log.append(f"[Time {clock}] {proc.pid} arrived")
                process_index += 1

            if not ready_queue:
                self.execution_log.append(f"[Time {clock}] CPU idle")
                self.idle_time += 1
                clock += 1
                continue

            proc = ready_queue.popleft()
            if proc.start is None:
                proc.start = clock
                proc.response_time = clock - proc.arrival

            self.execution_log.append(f"[Time {clock}] {proc.pid} executing")
            exec_time = min(quantum, proc.remaining)
            for _ in range(exec_time):
                proc.execution_history.append(clock)
                clock += 1

            proc.remaining -= exec_time

            if proc.remaining > 0:
                ready_queue.append(proc)
                self.execution_log.append(f"[Time {clock}] {proc.pid} preempted")
            else:
                proc.finish = clock
                proc.calculate_metrics()
                proc.state = "TERMINATED"
                self.completed.append(proc)
                self.execution_log.append(f"[Time {clock}] {proc.pid} finished")

            self.context_switches += 1

        self.calculate_system_metrics(clock)
        return self.completed

    # ===============================================================
    # SYSTEM METRICS
    # ===============================================================
    def calculate_system_metrics(self, total_time):
        if total_time > 0:
            self.cpu_utilization = ((total_time - self.idle_time) / total_time) * 100
            self.throughput = len(self.completed) / total_time

    # ===============================================================
    # COMPARISON (OPTIONAL)
    # ===============================================================
    def compare_with_other_algorithms(self, original_processes):
        """Compare Priority, SJF, FCFS, RR"""
        algorithms = ["Priority", "SJF", "FCFS", "RR"]
        print("\nALGORITHM COMPARISON\n" + "-" * 80)
        print(f"{'Algorithm':<15}{'Avg Waiting':<18}{'Avg Turnaround':<20}{'CPU Util %':<15}{'Context Switches':<20}")
        print("-" * 80)
        for algo in algorithms:
            test_procs = [Process(p.pid, p.arrival, p.burst, p.priority, p.process_type) for p in original_processes]
            scheduler = ProcessScheduler(test_procs, mode=self.mode, algorithm=algo.lower(), quantum=self.quantum)
            scheduler.schedule()
            n = len(scheduler.completed)
            avg_w = sum(p.waiting for p in scheduler.completed) / n
            avg_t = sum(p.turnaround for p in scheduler.completed) / n
            print(f"{algo:<15}{avg_w:<18.2f}{avg_t:<20.2f}{scheduler.cpu_utilization:<15.2f}{scheduler.context_switches:<20}")


# ===============================================================
# RANDOM PROCESS GENERATOR
# ===============================================================
def generate_random_processes(n=10):
    processes = []
    for i in range(n):
        pid = f"P{i+1}"
        arrival = random.randint(0, 10)
        burst = random.randint(1, 10)
        priority = random.randint(1, 5)
        ptype = random.choice(["CPU", "I/O"])
        processes.append(Process(pid, arrival, burst, priority, ptype))
    return processes
