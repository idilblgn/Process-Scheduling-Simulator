import sys
from collections import deque
from typing import List, Tuple, Dict, Any
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

class Process:
    def __init__(self, process_id: str, arrival_time: int, burst_time: int, priority: int):
        self.process_id = process_id
        self.arrival_time = arrival_time
        self.burst_time = burst_time
        self.priority = priority
        self.remaining_time = burst_time
        self.finish_time = 0
        self.turnaround_time = 0
        self.waiting_time = 0
    
    def copy(self):
        """Create a copy of the process"""
        p = Process(self.process_id, self.arrival_time, self.burst_time, self.priority)
        p.remaining_time = self.remaining_time
        return p
    
    def to_dict(self):
        """Convert process to dictionary"""
        return {
            'process_id': self.process_id,
            'arrival_time': self.arrival_time,
            'burst_time': self.burst_time,
            'priority': self.priority,
            'finish_time': self.finish_time,
            'turnaround_time': self.turnaround_time,
            'waiting_time': self.waiting_time
        }

class GanttEntry:
    def __init__(self, process_id: str, start_time: int, end_time: int):
        self.process_id = process_id
        self.start_time = start_time
        self.end_time = end_time
    
    def to_dict(self):
        """Convert Gantt entry to dictionary"""
        return {
            'process_id': self.process_id,
            'start_time': self.start_time,
            'end_time': self.end_time
        }

def read_processes(filename: str) -> List[Process]:
    """Read processes from input file"""
    processes = []

    try:
        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(',')
                if len(parts) != 4:
                    continue
                
                process_id = parts[0].strip()
                arrival_time = int(parts[1].strip())
                burst_time = int(parts[2].strip())
                priority = int(parts[3].strip())
                
                processes.append(Process(process_id, arrival_time, burst_time, priority))
        
        return processes
    
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found!")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

def schedule_fcfs(processes: List[Process]) -> Dict[str, Any]:
    """First-Come, First-Served (FCFS) Scheduling"""
    processes.sort(key=lambda p: p.arrival_time)
    
    gantt = []
    current_time = 0
    total_idle_time = 0
    
    for process in processes:
        if current_time < process.arrival_time:
            gantt.append(GanttEntry("IDLE", current_time, process.arrival_time))
            total_idle_time += (process.arrival_time - current_time)
            current_time = process.arrival_time
        
        gantt.append(GanttEntry(process.process_id, current_time, current_time + process.burst_time))
        current_time += process.burst_time
        process.finish_time = current_time
        process.turnaround_time = process.finish_time - process.arrival_time
        process.waiting_time = process.turnaround_time - process.burst_time
    
    return get_results_dict(processes, gantt, current_time, total_idle_time)

def schedule_sjf(processes: List[Process]) -> Dict[str, Any]:
    """Shortest Job First (SJF) Scheduling - Non-preemptive"""
    completed = []
    gantt = []
    current_time = 0
    total_idle_time = 0
    
    while len(completed) < len(processes):
        available = [p for p in processes if p.arrival_time <= current_time and p not in completed]
        
        if not available:
            next_arrival = min(p.arrival_time for p in processes if p not in completed)
            gantt.append(GanttEntry("IDLE", current_time, next_arrival))
            total_idle_time += (next_arrival - current_time)
            current_time = next_arrival
            continue
        
        selected = min(available, key=lambda p: (p.burst_time, p.arrival_time))
        
        gantt.append(GanttEntry(selected.process_id, current_time, current_time + selected.burst_time))
        current_time += selected.burst_time
        selected.finish_time = current_time
        selected.turnaround_time = selected.finish_time - selected.arrival_time
        selected.waiting_time = selected.turnaround_time - selected.burst_time
        completed.append(selected)
    
    return get_results_dict(processes, gantt, current_time, total_idle_time)

def schedule_rr(processes: List[Process], time_quantum: int) -> Dict[str, Any]:
    """Round Robin (RR) Scheduling - Preemptive"""
    processes_copy = [p.copy() for p in processes]
    processes_copy.sort(key=lambda p: p.arrival_time)
    
    ready_queue = deque()
    gantt = []
    current_time = 0
    total_idle_time = 0
    completed = 0
    process_index = 0
    
    if process_index < len(processes_copy) and processes_copy[process_index].arrival_time <= current_time:
        ready_queue.append(processes_copy[process_index])
        process_index += 1
    
    while completed < len(processes_copy):
        if not ready_queue:
            next_arrival = processes_copy[process_index].arrival_time
            gantt.append(GanttEntry("IDLE", current_time, next_arrival))
            total_idle_time += (next_arrival - current_time)
            current_time = next_arrival
            ready_queue.append(processes_copy[process_index])
            process_index += 1
        
        current = ready_queue.popleft()
        execute_time = min(time_quantum, current.remaining_time)
        
        gantt.append(GanttEntry(current.process_id, current_time, current_time + execute_time))
        current_time += execute_time
        current.remaining_time -= execute_time
        
        while process_index < len(processes_copy) and processes_copy[process_index].arrival_time <= current_time:
            ready_queue.append(processes_copy[process_index])
            process_index += 1
        
        if current.remaining_time > 0:
            ready_queue.append(current)
        else:
            current.finish_time = current_time
            current.turnaround_time = current.finish_time - current.arrival_time
            current.waiting_time = current.turnaround_time - current.burst_time
            completed += 1
    
    return get_results_dict(processes_copy, gantt, current_time, total_idle_time)

def schedule_priority(processes: List[Process]) -> Dict[str, Any]:
    """Priority Scheduling - Non-preemptive (Lower number = Higher priority)"""
    completed = []
    gantt = []
    current_time = 0
    total_idle_time = 0
    
    while len(completed) < len(processes):
        available = [p for p in processes if p.arrival_time <= current_time and p not in completed]
        
        if not available:
            next_arrival = min(p.arrival_time for p in processes if p not in completed)
            gantt.append(GanttEntry("IDLE", current_time, next_arrival))
            total_idle_time += (next_arrival - current_time)
            current_time = next_arrival
            continue
        
        selected = min(available, key=lambda p: (p.priority, p.arrival_time))
        
        gantt.append(GanttEntry(selected.process_id, current_time, current_time + selected.burst_time))
        current_time += selected.burst_time
        selected.finish_time = current_time
        selected.turnaround_time = selected.finish_time - selected.arrival_time
        selected.waiting_time = selected.turnaround_time - selected.burst_time
        completed.append(selected)
    
    return get_results_dict(processes, gantt, current_time, total_idle_time)

def get_results_dict(processes: List[Process], gantt: List[GanttEntry], total_time: int, total_idle_time: int) -> Dict[str, Any]:
    """Get scheduling results as dictionary"""
    total_turnaround = sum(p.turnaround_time for p in processes)
    total_waiting = sum(p.waiting_time for p in processes)
    
    avg_turnaround = total_turnaround / len(processes) if processes else 0
    avg_waiting = total_waiting / len(processes) if processes else 0
    cpu_utilization = ((total_time - total_idle_time) / total_time) * 100 if total_time > 0 else 0
    
    return {
        'processes': [p.to_dict() for p in processes],
        'gantt': [g.to_dict() for g in gantt],
        'total_time': total_time,
        'total_idle_time': total_idle_time,
        'average_turnaround_time': round(avg_turnaround, 2),
        'average_waiting_time': round(avg_waiting, 2),
        'cpu_utilization': round(cpu_utilization, 1)
    }

def print_results(processes: List[Process], gantt: List[GanttEntry], total_time: int, total_idle_time: int):
    """Print scheduling results (for CLI use)"""
    print("Gantt Chart: ", end="")
    for entry in gantt:
        print(f"[{entry.start_time}]--{entry.process_id}--", end="")
    print(f"[{total_time}]")
    
    print("\nProcess   | Finish Time | Turnaround Time | Waiting Time")
    print("-" * 57)
    
    total_turnaround = 0
    total_waiting = 0
    
    for process in processes:
        print(f"{process.process_id:<9} | {process.finish_time:<11} | {process.turnaround_time:<15} | {process.waiting_time:<12}")
        total_turnaround += process.turnaround_time
        total_waiting += process.waiting_time
    
    avg_turnaround = total_turnaround / len(processes)
    avg_waiting = total_waiting / len(processes)
    cpu_utilization = ((total_time - total_idle_time) / total_time) * 100 if total_time > 0 else 0
    
    print()
    print(f"Average Turnaround Time: {avg_turnaround:.2f}")
    print(f"Average Waiting Time: {avg_waiting:.2f}")
    print(f"CPU Utilization: {cpu_utilization:.1f}%")

@app.route('/api/schedule', methods=['POST'])
def api_schedule():
    """API endpoint for scheduling"""
    try:
        data = request.json
        processes_data = data.get('processes', [])
        algorithm = data.get('algorithm', 'fcfs')
        time_quantum = data.get('time_quantum', 3)
        
        # Convert JSON data to Process objects
        processes = []
        for p_data in processes_data:
            processes.append(Process(
                process_id=p_data['id'],
                arrival_time=p_data['arrival'],
                burst_time=p_data['burst'],
                priority=p_data['priority']
            ))
        
        if not processes:
            return jsonify({'error': 'No processes provided'}), 400
        
        # Run selected algorithm
        if algorithm == 'fcfs':
            result = schedule_fcfs([p.copy() for p in processes])
        elif algorithm == 'sjf':
            result = schedule_sjf([p.copy() for p in processes])
        elif algorithm == 'rr':
            result = schedule_rr([p.copy() for p in processes], time_quantum)
        elif algorithm == 'priority':
            result = schedule_priority([p.copy() for p in processes])
        else:
            return jsonify({'error': 'Invalid algorithm'}), 400
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/favicon.ico')
def favicon():
    """Handle favicon requests to avoid 404 errors"""
    return '', 204  # No Content

@app.route('/')
def index():
    """Serve the HTML interface"""
    try:
        with open('scheduler.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "HTML dosyası bulunamadı!", 404

def print_results_from_dict(result_dict: Dict[str, Any]):
    """Print results from dictionary format"""
    processes = result_dict['processes']
    gantt = result_dict['gantt']
    total_time = result_dict['total_time']
    
    # Convert dict format back to objects for printing
    process_objs = []
    for p_dict in processes:
        p = Process(p_dict['process_id'], p_dict['arrival_time'], 
                   p_dict['burst_time'], p_dict['priority'])
        p.finish_time = p_dict['finish_time']
        p.turnaround_time = p_dict['turnaround_time']
        p.waiting_time = p_dict['waiting_time']
        process_objs.append(p)
    
    gantt_objs = [GanttEntry(g['process_id'], g['start_time'], g['end_time']) 
                  for g in gantt]
    
    total_idle_time = result_dict['total_idle_time']
    print_results(process_objs, gantt_objs, total_time, total_idle_time)

def main():
    """CLI main function (for backward compatibility)"""
    if len(sys.argv) < 2:
        print("Usage: python process_scheduler.py <input_file> [time_quantum]")
        sys.exit(1)
    
    filename = sys.argv[1]
    time_quantum = 3  
    
    if len(sys.argv) > 2:
        time_quantum = int(sys.argv[2])
    
    processes = read_processes(filename)
    
    if not processes:
        print("No processes to schedule.")
        sys.exit(1)
    
    result = schedule_fcfs([p.copy() for p in processes])
    print_results_from_dict(result)
    print("\n")
    
    result = schedule_sjf([p.copy() for p in processes])
    print_results_from_dict(result)
    print("\n")
    
    result = schedule_rr([p.copy() for p in processes], time_quantum)
    print_results_from_dict(result)
    print("\n")
    
    result = schedule_priority([p.copy() for p in processes])
    print_results_from_dict(result)

if __name__ == "__main__":
    # Run as Flask app if no command line arguments, otherwise run CLI
    if len(sys.argv) > 1 and sys.argv[1] != 'run':
        main()
    else:
        app.run(debug=True, port=5000)