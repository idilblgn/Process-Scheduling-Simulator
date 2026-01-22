# Process Scheduling Simulator

A web application that visualizes process scheduling algorithms.

## Features

- **FCFS (First-Come, First-Served)**: First come, first served
- **SJF (Shortest Job First)**: Shortest job first (Non-preemptive)
- **Round Robin**: Time slice-based operation (Preemptive)
- **Priority Scheduling**: Priority-based operation (Non-preemptive)

## Installation

1. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

### Web Interface

1. Start the Flask server:
```bash
python process_scheduling.py
```

2. Navigate to the following address in your browser:
```
http://localhost:5000
```

3. Add processes, select an algorithm, and run it.

### Command Line (CLI)

```bash
python process_scheduling.py process.txt [time_quantum]
```

Example:
```bash
python process_scheduling.py process.txt 3
```

## API Endpoint

### POST /api/schedule

Request body:
```json
{
    "processes": [
        {
            "id": "P1",
            "arrival": 0,
            "burst": 5,
            "priority": 1
        }
    ],
    "algorithm": "fcfs",
    "time_quantum": 3
}
```

Response:
```json
{
    "processes": [...],
    "gantt": [...],
    "total_time": 26,
    "total_idle_time": 0,
    "average_turnaround_time": 15.5,
    "average_waiting_time": 9.75,
    "cpu_utilization": 100.0
}
```

## Algorithm cuts

- `fcfs`: First-Come, First-Served
- `sjf`: Shortest Job First
- `rr`: Round Robin
- `priority`: Priority Scheduling

