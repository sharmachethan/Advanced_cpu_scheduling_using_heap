import heapq
import random
import time
from typing import List
from collections import deque
from datetime import datetime

class Process:
    """Represents a process with comprehensive scheduling attributes"""
    
    def __init__(self, pid, arrival, burst, priority, process_type="CPU"):
        self.pid = pid
        self.arrival = arrival
        self.burst = burst
        self.priority = priority
        self.process_type = process_type  # CPU-bound or I/O-bound
        self.remaining = burst
        self.start = None
        self.finish = None
        self.waiting = 0
        self.turnaround = 0
        self.response_time = None
        self.context_switches = 0
        self.execution_history = []  # Track execution intervals
        self.state = "NEW"  # NEW, READY, RUNNING, WAITING, TERMINATED
        
    def __repr__(self):
        return f"Process({self.pid}, Priority={self.priority}, Burst={self.burst})"
    
    def calculate_metrics(self):
        """Calculate all scheduling metrics"""
        if self.start is not None and self.finish is not None:
            self.waiting = self.start - self.arrival
            self.turnaround = self.finish - self.arrival
            self.response_time = self.start - self.arrival


class ProcessScheduler:
    """Advanced heap-based process scheduler with multiple features"""
    
    def __init__(self, processes: List[Process], mode="preemptive", algorithm="priority"):
        self.processes = sorted(processes, key=lambda p: p.arrival)
        self.mode = mode  # preemptive or non-preemptive
        self.algorithm = algorithm  # priority, sjf, fcfs
        self.timeline = []
        self.completed = []
        self.context_switches = 0
        self.cpu_utilization = 0
        self.throughput = 0
        self.idle_time = 0
        self.execution_log = []
        
    def schedule(self):
        """Main scheduling algorithm with support for multiple scheduling types"""
        clock = 0
        ready_heap = []
        process_index = 0
        running = None
        total_processes = len(self.processes)
        last_process = None
        
        while process_index < total_processes or ready_heap or running:
            # Add all processes that have arrived by current clock time
            while process_index < total_processes and self.processes[process_index].arrival <= clock:
                proc = self.processes[process_index]
                proc.state = "READY"
                
                # Different heap organization based on algorithm
                if self.algorithm == "priority":
                    heapq.heappush(ready_heap, (-proc.priority, proc.arrival, proc.pid, proc))
                elif self.algorithm == "sjf":  # Shortest Job First
                    heapq.heappush(ready_heap, (proc.remaining, proc.arrival, proc.pid, proc))
                elif self.algorithm == "fcfs":  # First Come First Serve
                    heapq.heappush(ready_heap, (proc.arrival, proc.pid, proc))
                
                self.execution_log.append(f"[Time {clock}] Process {proc.pid} arrived and added to ready queue")
                process_index += 1
            
            # Preemptive check: if a higher priority/shorter process arrives
            if running and self.mode == "preemptive" and ready_heap:
                should_preempt = False
                
                if self.algorithm == "priority":
                    highest_priority = -ready_heap[0][0]
                    should_preempt = highest_priority > running.priority
                elif self.algorithm == "sjf":
                    shortest_remaining = ready_heap[0][0]
                    should_preempt = shortest_remaining < running.remaining
                
                if should_preempt:
                    # Preempt current process
                    running.state = "READY"
                    running.context_switches += 1
                    self.context_switches += 1
                    
                    if self.algorithm == "priority":
                        heapq.heappush(ready_heap, (-running.priority, running.arrival, running.pid, running))
                    elif self.algorithm == "sjf":
                        heapq.heappush(ready_heap, (running.remaining, running.arrival, running.pid, running))
                    
                    self.execution_log.append(f"[Time {clock}] Process {running.pid} preempted")
                    running = None
            
            # If no process is running, get next from heap
            if not running and ready_heap:
                if self.algorithm == "fcfs":
                    _, _, running = heapq.heappop(ready_heap)
                else:
                    *_, running = heapq.heappop(ready_heap)
                
                running.state = "RUNNING"
                
                if running.start is None:
                    running.start = clock
                    running.response_time = clock - running.arrival
                
                # Track context switch
                if last_process and last_process.pid != running.pid:
                    self.context_switches += 1
                
                self.execution_log.append(f"[Time {clock}] Process {running.pid} started/resumed execution")
            
            # Execute the running process for 1 time unit
            if running:
                running.remaining -= 1
                running.execution_history.append(clock)
                last_process = running
                
                # If process completes
                if running.remaining == 0:
                    running.finish = clock + 1
                    running.state = "TERMINATED"
                    running.calculate_metrics()
                    self.completed.append(running)
                    self.execution_log.append(f"[Time {clock + 1}] Process {running.pid} completed")
                    running = None
            else:
                # CPU idle
                self.idle_time += 1
                self.execution_log.append(f"[Time {clock}] CPU idle")
            
            clock += 1
        
        # Calculate overall metrics
        self.calculate_system_metrics(clock)
        return self.completed
    
    def calculate_system_metrics(self, total_time):
        """Calculate system-wide performance metrics"""
        if total_time > 0:
            self.cpu_utilization = ((total_time - self.idle_time) / total_time) * 100
            self.throughput = len(self.completed) / total_time
    
    def display_results(self):
        """Display comprehensive scheduling results and metrics"""
        print("\n" + "="*120)
        print(f"{'PROCESS SCHEDULING RESULTS':^120}")
        print(f"{'Mode: ' + self.mode.upper() + ' | Algorithm: ' + self.algorithm.upper():^120}")
        print("="*120)
        
        print(f"\n{'PID':<8}{'Type':<12}{'Arrival':<10}{'Burst':<10}{'Priority':<10}{'Start':<10}"
              f"{'Finish':<10}{'Waiting':<10}{'Turnaround':<12}{'Response':<10}{'Switches':<10}")
        print("-"*120)
        
        total_waiting = 0
        total_turnaround = 0
        total_response = 0
        
        for proc in self.completed:
            print(f"{proc.pid:<8}{proc.process_type:<12}{proc.arrival:<10}{proc.burst:<10}"
                  f"{proc.priority:<10}{proc.start:<10}{proc.finish:<10}{proc.waiting:<10}"
                  f"{proc.turnaround:<12}{proc.response_time:<10}{proc.context_switches:<10}")
            total_waiting += proc.waiting
            total_turnaround += proc.turnaround
            total_response += proc.response_time
        
        print("-"*120)
        n = len(self.completed)
        avg_waiting = total_waiting / n if n > 0 else 0
        avg_turnaround = total_turnaround / n if n > 0 else 0
        avg_response = total_response / n if n > 0 else 0
        
        print(f"\n{'PERFORMANCE METRICS':^120}")
        print("-"*120)
        print(f"Average Waiting Time:      {avg_waiting:.2f} time units")
        print(f"Average Turnaround Time:   {avg_turnaround:.2f} time units")
        print(f"Average Response Time:     {avg_response:.2f} time units")
        print(f"CPU Utilization:           {self.cpu_utilization:.2f}%")
        print(f"Throughput:                {self.throughput:.4f} processes/time unit")
        print(f"Total Context Switches:    {self.context_switches}")
        print(f"Total Idle Time:           {self.idle_time} time units")
        print("="*120 + "\n")
    
    def display_gantt_chart(self):
        """Display a visual Gantt chart"""
        print("\nGANTT CHART:")
        print("-" * 100)
        
        gantt_representation = []
        current_process = None
        start_time = 0
        
        for proc in self.completed:
            if proc.start is not None and proc.finish is not None:
                gantt_representation.append(f"{proc.pid}[{proc.start}-{proc.finish}]")
        
        print(" -> ".join(gantt_representation))
        print("-" * 100 + "\n")
    
    def display_execution_log(self, max_lines=20):
        """Display execution log"""
        print("\nEXECUTION LOG (First {} entries):".format(max_lines))
        print("-" * 100)
        for i, log in enumerate(self.execution_log[:max_lines]):
            print(log)
        if len(self.execution_log) > max_lines:
            print(f"... and {len(self.execution_log) - max_lines} more entries")
        print("-" * 100 + "\n")
    
    def compare_with_other_algorithms(self, original_processes):
        """Compare current algorithm with other scheduling algorithms"""
        print("\n" + "="*120)
        print(f"{'ALGORITHM COMPARISON':^120}")
        print("="*120)
        
        algorithms = ["priority", "sjf", "fcfs"]
        results = {}
        
        for algo in algorithms:
            # Create fresh copies of processes
            test_processes = [Process(p.pid, p.arrival, p.burst, p.priority, p.process_type) 
                            for p in original_processes]
            
            scheduler = ProcessScheduler(test_processes, mode=self.mode, algorithm=algo)
            scheduler.schedule()
            
            n = len(scheduler.completed)
            avg_waiting = sum(p.waiting for p in scheduler.completed) / n if n > 0 else 0
            avg_turnaround = sum(p.turnaround for p in scheduler.completed) / n if n > 0 else 0
            
            results[algo] = {
                'avg_waiting': avg_waiting,
                'avg_turnaround': avg_turnaround,
                'cpu_util': scheduler.cpu_utilization,
                'context_switches': scheduler.context_switches
            }
        
        print(f"\n{'Algorithm':<15}{'Avg Waiting':<18}{'Avg Turnaround':<20}{'CPU Util %':<15}{'Context Switches':<20}")
        print("-"*120)
        
        for algo, metrics in results.items():
            print(f"{algo.upper():<15}{metrics['avg_waiting']:<18.2f}{metrics['avg_turnaround']:<20.2f}"
                  f"{metrics['cpu_util']:<15.2f}{metrics['context_switches']:<20}")
        
        print("="*120 + "\n")
    
    def export_to_csv(self, filename="scheduling_results.csv"):
        """Export results to CSV file"""
        try:
            with open(filename, 'w') as f:
                f.write("PID,Type,Arrival,Burst,Priority,Start,Finish,Waiting,Turnaround,Response,ContextSwitches\n")
                for proc in self.completed:
                    f.write(f"{proc.pid},{proc.process_type},{proc.arrival},{proc.burst},{proc.priority},"
                           f"{proc.start},{proc.finish},{proc.waiting},{proc.turnaround},"
                           f"{proc.response_time},{proc.context_switches}\n")
            print(f"✓ Results exported to {filename}")
        except Exception as e:
            print(f"✗ Error exporting to CSV: {e}")


def generate_random_processes(n=10):
    """Generate random processes for testing"""
    processes = []
    process_types = ["CPU", "I/O"]
    
    for i in range(n):
        pid = f"P{i+1}"
        arrival = random.randint(0, 10)
        burst = random.randint(1, 10)
        priority = random.randint(1, 5)
        proc_type = random.choice(process_types)
        processes.append(Process(pid, arrival, burst, priority, proc_type))
    
    return processes


def run_predefined_examples():
    """Run predefined example scenarios"""
    print("\n" + "="*120)
    print(f"{'MULTI-LEVEL PROCESS SCHEDULER USING HEAP DATA STRUCTURE':^120}")
    print(f"{'Operating System Mini Project - Extended Version':^120}")
    print("="*120)
    
    # Example 1: Preemptive Priority Scheduling
    print("\n\nEXAMPLE 1: PREEMPTIVE PRIORITY SCHEDULING")
    print("-" * 120)
    
    processes1 = [
        Process('P1', 0, 4, 2, "CPU"),
        Process('P2', 1, 3, 3, "I/O"),
        Process('P3', 2, 2, 1, "CPU"),
        Process('P4', 3, 5, 4, "CPU"),
        Process('P5', 4, 2, 5, "I/O")
    ]
    
    scheduler1 = ProcessScheduler(processes1, mode="preemptive", algorithm="priority")
    scheduler1.schedule()
    scheduler1.display_results()
    scheduler1.display_gantt_chart()
    scheduler1.display_execution_log(15)
    scheduler1.export_to_csv("preemptive_priority.csv")
    
    # Example 2: Non-Preemptive Shortest Job First
    print("\n\nEXAMPLE 2: NON-PREEMPTIVE SHORTEST JOB FIRST (SJF)")
    print("-" * 120)
    
    processes2 = [
        Process('P1', 0, 6, 2, "CPU"),
        Process('P2', 1, 8, 3, "CPU"),
        Process('P3', 2, 7, 1, "I/O"),
        Process('P4', 3, 3, 4, "CPU"),
    ]
    
    scheduler2 = ProcessScheduler(processes2, mode="non-preemptive", algorithm="sjf")
    scheduler2.schedule()
    scheduler2.display_results()
    scheduler2.display_gantt_chart()
    
    # Example 3: Algorithm Comparison
    print("\n\nEXAMPLE 3: COMPARING DIFFERENT SCHEDULING ALGORITHMS")
    print("-" * 120)
    
    processes3 = [
        Process('P1', 0, 5, 3, "CPU"),
        Process('P2', 1, 3, 2, "I/O"),
        Process('P3', 2, 8, 1, "CPU"),
        Process('P4', 3, 6, 4, "CPU"),
    ]
    
    comparison_scheduler = ProcessScheduler(processes3, mode="preemptive", algorithm="priority")
    comparison_scheduler.schedule()
    comparison_scheduler.compare_with_other_algorithms(processes3)


def interactive_mode():
    """Interactive mode for custom process input with error handling"""
    print("\n\nINTERACTIVE MODE")
    print("-" * 120)
    
    print("\nOptions:")
    print("1. Enter custom processes manually")
    print("2. Generate random processes")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == '1':
        custom_processes = []
        
        # Input validation for number of processes
        while True:
            try:
                n = int(input("Enter number of processes: "))
                if n <= 0:
                    print("❌ Please enter a positive number!")
                    continue
                break
            except ValueError:
                print("❌ Invalid input! Please enter a valid number (e.g., 5)")
        
        for i in range(n):
            print(f"\nProcess {i+1}:")
            
            # Process ID input
            while True:
                pid = input("  Enter Process ID: ").strip()
                if pid:
                    break
                print("  ❌ Process ID cannot be empty!")
            
            # Arrival time input with validation
            while True:
                try:
                    arrival = int(input("  Enter Arrival Time: "))
                    if arrival < 0:
                        print("  ❌ Arrival time cannot be negative!")
                        continue
                    break
                except ValueError:
                    print("  ❌ Invalid input! Please enter a valid number.")
            
            # Burst time input with validation
            while True:
                try:
                    burst = int(input("  Enter Burst Time: "))
                    if burst <= 0:
                        print("  ❌ Burst time must be greater than 0!")
                        continue
                    break
                except ValueError:
                    print("  ❌ Invalid input! Please enter a valid number.")
            
            # Priority input with validation
            while True:
                try:
                    priority = int(input("  Enter Priority (higher number = higher priority): "))
                    if priority <= 0:
                        print("  ❌ Priority must be greater than 0!")
                        continue
                    break
                except ValueError:
                    print("  ❌ Invalid input! Please enter a valid number.")
            
            # Process type input with validation
            while True:
                proc_type = input("  Enter Process Type (CPU/I/O): ").strip().upper()
                if proc_type in ['CPU', 'I/O']:
                    break
                print("  ❌ Invalid type! Please enter 'CPU' or 'I/O'.")
            
            custom_processes.append(Process(pid, arrival, burst, priority, proc_type))
        
        # Mode selection with validation
        while True:
            mode = input("\nSelect mode (preemptive/non-preemptive): ").strip().lower()
            if mode in ['preemptive', 'non-preemptive']:
                break
            print("❌ Invalid mode! Please enter 'preemptive' or 'non-preemptive'.")
        
        # Algorithm selection with validation
        while True:
            algorithm = input("Select algorithm (priority/sjf/fcfs): ").strip().lower()
            if algorithm in ['priority', 'sjf', 'fcfs']:
                break
            print("❌ Invalid algorithm! Please enter 'priority', 'sjf', or 'fcfs'.")
        
        custom_scheduler = ProcessScheduler(custom_processes, mode=mode, algorithm=algorithm)
        custom_scheduler.schedule()
        custom_scheduler.display_results()
        custom_scheduler.display_gantt_chart()
        custom_scheduler.display_execution_log()
        
        export = input("\nExport results to CSV? (yes/no): ").strip().lower()
        if export == 'yes':
            filename = input("Enter filename (default: custom_results.csv): ").strip() or "custom_results.csv"
            custom_scheduler.export_to_csv(filename)
    
    elif choice == '2':
        # Input validation for random process generation
        while True:
            try:
                n = int(input("Enter number of random processes to generate: "))
                if n <= 0:
                    print("❌ Please enter a positive number!")
                    continue
                break
            except ValueError:
                print("❌ Invalid input! Please enter a valid number (e.g., 10)")
        
        random_processes = generate_random_processes(n)
        
        print(f"\nGenerated {n} random processes:")
        for p in random_processes:
            print(f"  {p}")
        
        # Mode selection with validation
        while True:
            mode = input("\nSelect mode (preemptive/non-preemptive): ").strip().lower()
            if mode in ['preemptive', 'non-preemptive']:
                break
            print("❌ Invalid mode! Please enter 'preemptive' or 'non-preemptive'.")
        
        # Algorithm selection with validation
        while True:
            algorithm = input("Select algorithm (priority/sjf/fcfs): ").strip().lower()
            if algorithm in ['priority', 'sjf', 'fcfs']:
                break
            print("❌ Invalid algorithm! Please enter 'priority', 'sjf', or 'fcfs'.")
        
        random_scheduler = ProcessScheduler(random_processes, mode=mode, algorithm=algorithm)
        random_scheduler.schedule()
        random_scheduler.display_results()
        random_scheduler.display_gantt_chart()
        random_scheduler.compare_with_other_algorithms(random_processes)
    
    elif choice == '3':
        print("\n✓ Exiting interactive mode...")
    
    else:
        print("\n❌ Invalid option! Please select 1, 2, or 3.")


def main():
    """Main execution function"""
    print(f"\nExecution started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run predefined examples
    run_predefined_examples()
    
    # Interactive mode
    interactive = input("\nWould you like to try interactive mode? (yes/no): ").strip().lower()
    if interactive == 'yes':
        interactive_mode()
    
    print("\n" + "="*120)
    print(f"{'PROJECT COMPLETED SUCCESSFULLY!':^120}")
    print(f"Execution finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^120}")
    print("="*120 + "\n")


if __name__ == "__main__":
    main()
