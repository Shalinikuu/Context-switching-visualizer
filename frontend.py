import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import numpy as np
import os
import subprocess
import tempfile
import time

class ContextSwitchVisualizer:
    def __init__(self, root):
        self.root = root
        self.root.title("CPU Context Switching Visualizer")
        self.root.geometry("1400x900")
        self.root.configure(bg='#1e293b')
        
        self.process_data = None
        self.switch_data = None
        
        self.setup_styles()
        self.create_widgets()
        
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background='#1e293b')
        style.configure('TLabel', background='#1e293b', foreground='#e2e8f0', 
                       font=('Arial', 10))
        style.configure('Title.TLabel', font=('Arial', 16, 'bold'), 
                       foreground='#60a5fa')
        
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title = ttk.Label(main_frame, text="🖥️ CPU Context Switching Visualizer", 
                         style='Title.TLabel')
        title.pack(pady=(0, 20))
        
        # Control Panel
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 20))
        
        left_controls = ttk.Frame(control_frame)
        left_controls.pack(side=tk.LEFT, padx=10)
        
        # Main action button
        self.run_cpp_btn = tk.Button(left_controls, text="▶ Run New Simulation", 
                                     command=self.run_simulation_dialog,
                                     bg='#10b981', fg='white', font=('Arial', 12, 'bold'),
                                     padx=25, pady=12, relief=tk.FLAT, cursor='hand2')
        self.run_cpp_btn.pack(side=tk.LEFT, padx=5)
        
        self.load_btn = tk.Button(left_controls, text="📂 Load CSV", 
                                  command=self.load_data,
                                  bg='#3b82f6', fg='white', font=('Arial', 11, 'bold'),
                                  padx=20, pady=10, relief=tk.FLAT, cursor='hand2')
        self.load_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_btn = tk.Button(left_controls, text="🗑️ Clear", 
                                   command=self.clear_data,
                                   bg='#ef4444', fg='white', font=('Arial', 11, 'bold'),
                                   padx=20, pady=10, relief=tk.FLAT, cursor='hand2')
        self.clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Statistics Panel
        stats_frame = tk.LabelFrame(main_frame, text="📊 Statistics", 
                                   bg='#334155', fg='#e2e8f0',
                                   font=('Arial', 12, 'bold'), padx=10, pady=10)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)
        
        self.stats_labels = {}
        stats_info = [
            ("Total Processes:", "total_proc"),
            ("Context Switches:", "context_switches"),
            ("Avg Wait Time:", "avg_wait"),
            ("Avg Turnaround:", "avg_turnaround"),
            ("CPU Utilization:", "cpu_util"),
            ("Throughput:", "throughput")
        ]
        
        for i, (label_text, key) in enumerate(stats_info):
            row = i // 3
            col = i % 3
            
            frame = ttk.Frame(stats_grid)
            frame.grid(row=row, column=col, padx=15, pady=5, sticky='w')
            
            label = ttk.Label(frame, text=label_text, font=('Arial', 10, 'bold'))
            label.pack(side=tk.LEFT)
            
            value = ttk.Label(frame, text="--", foreground='#60a5fa', 
                            font=('Arial', 11, 'bold'))
            value.pack(side=tk.LEFT, padx=(5, 0))
            
            self.stats_labels[key] = value
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab 1: Process Table
        self.table_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.table_frame, text="📋 Process Table")
        self.create_process_table()
        
        # Tab 2: Gantt Chart
        self.gantt_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.gantt_frame, text="📊 Gantt Chart")
        
        # Tab 3: Performance Graphs
        self.graph_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.graph_frame, text="📈 Performance Graphs")
        
        # Status bar
        self.status_bar = tk.Label(self.root, text="Ready - Click 'Run New Simulation' to start", 
                                   bd=1, relief=tk.SUNKEN,
                                   anchor=tk.W, bg='#0f172a', fg='#94a3b8',
                                   font=('Arial', 9))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def create_process_table(self):
        table_container = ttk.Frame(self.table_frame)
        table_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        vsb = ttk.Scrollbar(table_container, orient="vertical")
        hsb = ttk.Scrollbar(table_container, orient="horizontal")
        
        columns = ("PID", "Process", "Arrival", "Burst", "Completion", 
                  "Turnaround", "Wait", "Response", "Priority", "State")
        
        self.tree = ttk.Treeview(table_container, columns=columns, show='headings',
                                yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.tree.tag_configure('completed', background='#86efac')
        
    def run_simulation_dialog(self):
        """Show dialog to run simulation with user inputs"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Run CPU Scheduling Simulation")
        dialog.geometry("500x600")
        dialog.configure(bg='#1e293b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        title_label = tk.Label(dialog, text="Configure Simulation", 
                              font=('Arial', 16, 'bold'), 
                              bg='#1e293b', fg='#60a5fa')
        title_label.pack(pady=20)
        
        # Input frame
        input_frame = tk.Frame(dialog, bg='#334155', padx=20, pady=20)
        input_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Algorithm selection
        tk.Label(input_frame, text="Scheduling Algorithm:", 
                font=('Arial', 11, 'bold'), bg='#334155', fg='white').pack(anchor='w', pady=(0, 5))
        
        algo_var = tk.StringVar(value="RR")
        algorithms = [
            ("Round Robin", "RR"),
            ("First Come First Serve", "FCFS"),
            ("Priority Scheduling", "PRIORITY")
        ]
        
        for text, value in algorithms:
            tk.Radiobutton(input_frame, text=text, variable=algo_var, value=value,
                          bg='#334155', fg='white', selectcolor='#1e293b',
                          font=('Arial', 10)).pack(anchor='w')
        
        # Time quantum
        tk.Label(input_frame, text="\nTime Quantum:", 
                font=('Arial', 11, 'bold'), bg='#334155', fg='white').pack(anchor='w', pady=(10, 5))
        quantum_var = tk.IntVar(value=2)
        quantum_spin = tk.Spinbox(input_frame, from_=1, to=10, textvariable=quantum_var,
                                 font=('Arial', 10), width=10)
        quantum_spin.pack(anchor='w')
        
        # Number of processes
        tk.Label(input_frame, text="\nNumber of Processes:", 
                font=('Arial', 11, 'bold'), bg='#334155', fg='white').pack(anchor='w', pady=(10, 5))
        num_proc_var = tk.IntVar(value=3)
        num_proc_spin = tk.Spinbox(input_frame, from_=2, to=10, textvariable=num_proc_var,
                                   font=('Arial', 10), width=10)
        num_proc_spin.pack(anchor='w')
        
        # Process input method
        tk.Label(input_frame, text="\nProcess Input:", 
                font=('Arial', 11, 'bold'), bg='#334155', fg='white').pack(anchor='w', pady=(10, 5))
        
        input_method_var = tk.StringVar(value="manual")
        tk.Radiobutton(input_frame, text="Manual Entry (GUI Form)", 
                      variable=input_method_var, value="manual",
                      bg='#334155', fg='white', selectcolor='#1e293b',
                      font=('Arial', 10)).pack(anchor='w')
        tk.Radiobutton(input_frame, text="Random Generation", 
                      variable=input_method_var, value="random",
                      bg='#334155', fg='white', selectcolor='#1e293b',
                      font=('Arial', 10)).pack(anchor='w')
        tk.Radiobutton(input_frame, text="Fetch PC Processes (Real System)", 
                      variable=input_method_var, value="system",
                      bg='#334155', fg='white', selectcolor='#1e293b',
                      font=('Arial', 10)).pack(anchor='w')
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg='#1e293b')
        btn_frame.pack(pady=20)
        
        def run_sim():
            dialog.destroy()
            self.run_simulation(algo_var.get(), quantum_var.get(), 
                              num_proc_var.get(), input_method_var.get())
        
        tk.Button(btn_frame, text="▶ Run Simulation", command=run_sim,
                 bg='#10b981', fg='white', font=('Arial', 11, 'bold'),
                 padx=20, pady=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Cancel", command=dialog.destroy,
                 bg='#6b7280', fg='white', font=('Arial', 11, 'bold'),
                 padx=20, pady=10).pack(side=tk.LEFT, padx=5)
    
    def run_simulation(self, algorithm, quantum, num_processes, input_method):
        """Run simulation with given parameters"""
        try:
            self.status_bar.config(text="Running simulation...")
            self.root.update()
            
            processes = []
            
            if input_method == "manual":
                # Manual entry dialog
                processes = self.get_manual_processes(num_processes)
                if not processes:
                    self.status_bar.config(text="Simulation cancelled")
                    return
            elif input_method == "system":
                # Fetch real PC processes
                processes = self.fetch_system_processes(num_processes)
                if not processes:
                    self.status_bar.config(text="Failed to fetch processes")
                    return
            else:
                # Random generation
                for i in range(num_processes):
                    processes.append({
                        'name': f'P{i+1}',
                        'arrival': i * 2,
                        'burst': np.random.randint(3, 12),
                        'priority': np.random.randint(1, 6)
                    })
            
            # Run scheduling algorithm
            result = self.simulate_scheduling(processes, algorithm, quantum)
            
            # Save to CSV
            self.save_simulation_results(result)
            
            # Load and display
            self.load_data_from_memory(result)
            
            self.status_bar.config(text="✓ Simulation completed successfully!")
            messagebox.showinfo("Success", 
                              f"Simulation completed!\n\n"
                              f"Algorithm: {algorithm}\n"
                              f"Processes: {num_processes}\n"
                              f"Context Switches: {result['context_switches']}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Simulation failed:\n{str(e)}")
            self.status_bar.config(text="Simulation failed")
    
    def get_manual_processes(self, num_processes):
        """Get process details manually from user"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Enter Process Details")
        dialog.geometry("600x500")
        dialog.configure(bg='#1e293b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        processes = []
        entries = []
        
        # Scrollable frame
        canvas = tk.Canvas(dialog, bg='#1e293b')
        scrollbar = tk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1e293b')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Header
        header_frame = tk.Frame(scrollable_frame, bg='#334155', padx=10, pady=10)
        header_frame.pack(fill=tk.X, padx=10, pady=10)
        
        headers = ['Process', 'Arrival', 'Burst', 'Priority']
        for i, header in enumerate(headers):
            tk.Label(header_frame, text=header, font=('Arial', 10, 'bold'),
                    bg='#334155', fg='white', width=12).grid(row=0, column=i, padx=5)
        
        # Process entries
        for i in range(num_processes):
            frame = tk.Frame(scrollable_frame, bg='#1e293b', padx=10, pady=5)
            frame.pack(fill=tk.X, padx=10)
            
            name_entry = tk.Entry(frame, font=('Arial', 10), width=12)
            name_entry.insert(0, f'P{i+1}')
            name_entry.grid(row=0, column=0, padx=5)
            
            arrival_entry = tk.Entry(frame, font=('Arial', 10), width=12)
            arrival_entry.insert(0, str(i * 2))
            arrival_entry.grid(row=0, column=1, padx=5)
            
            burst_entry = tk.Entry(frame, font=('Arial', 10), width=12)
            burst_entry.insert(0, str(np.random.randint(3, 10)))
            burst_entry.grid(row=0, column=2, padx=5)
            
            priority_entry = tk.Entry(frame, font=('Arial', 10), width=12)
            priority_entry.insert(0, str(np.random.randint(1, 6)))
            priority_entry.grid(row=0, column=3, padx=5)
            
            entries.append((name_entry, arrival_entry, burst_entry, priority_entry))
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg='#1e293b', pady=10)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        result = {'cancelled': False}
        
        def submit():
            try:
                for name, arrival, burst, priority in entries:
                    processes.append({
                        'name': name.get(),
                        'arrival': int(arrival.get()),
                        'burst': int(burst.get()),
                        'priority': int(priority.get())
                    })
                result['cancelled'] = False
                dialog.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter valid numeric values!")
        
        def cancel():
            result['cancelled'] = True
            dialog.destroy()
        
        tk.Button(btn_frame, text="Submit", command=submit,
                 bg='#10b981', fg='white', font=('Arial', 11, 'bold'),
                 padx=30, pady=10).pack(side=tk.LEFT, padx=20)
        
        tk.Button(btn_frame, text="Cancel", command=cancel,
                 bg='#6b7280', fg='white', font=('Arial', 11, 'bold'),
                 padx=30, pady=10).pack(side=tk.LEFT)
        
        dialog.wait_window()
        
        return None if result['cancelled'] else processes
    
    def fetch_system_processes(self, num_processes):
        """Fetch real system processes using psutil"""
        try:
            import psutil
            
            # Get all running processes
            all_processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'nice']):
                try:
                    pinfo = proc.info
                    # Skip system idle and very small processes
                    if pinfo['name'] and pinfo['pid'] > 0:
                        all_processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'cpu': pinfo['cpu_percent'] or 0,
                            'memory': pinfo['memory_percent'] or 0,
                            'priority': pinfo['nice'] if pinfo['nice'] is not None else 0
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            
            if not all_processes:
                messagebox.showerror("Error", "No processes found!")
                return None
            
            # Show selection dialog
            return self.show_process_selection_dialog(all_processes, num_processes)
            
        except ImportError:
            messagebox.showwarning("psutil not installed",
                                 "Installing psutil to fetch system processes...\n\n"
                                 "Please run: pip install psutil\n"
                                 "Then restart the application.")
            
            # Fallback: Use simulated processes
            messagebox.showinfo("Using Simulated Data",
                              "Using simulated process data instead.\n"
                              "Install 'psutil' for real system processes.")
            
            processes = []
            common_apps = ['chrome.exe', 'vscode.exe', 'explorer.exe', 'spotify.exe', 
                          'discord.exe', 'python.exe', 'notepad.exe', 'firefox.exe']
            
            for i in range(min(num_processes, len(common_apps))):
                processes.append({
                    'name': common_apps[i],
                    'arrival': i * 2,
                    'burst': np.random.randint(4, 12),
                    'priority': np.random.randint(1, 6)
                })
            
            return processes
    
    def show_process_selection_dialog(self, all_processes, num_processes):
        """Show dialog to select which processes to simulate"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Select System Processes")
        dialog.geometry("800x600")
        dialog.configure(bg='#1e293b')
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Title
        title_label = tk.Label(dialog, 
                              text=f"Select {num_processes} processes from your PC", 
                              font=('Arial', 14, 'bold'), 
                              bg='#1e293b', fg='#60a5fa')
        title_label.pack(pady=10)
        
        # Info label
        info_label = tk.Label(dialog, 
                             text="Real-time processes running on your system", 
                             font=('Arial', 10), 
                             bg='#1e293b', fg='#94a3b8')
        info_label.pack()
        
        # Table frame
        table_frame = tk.Frame(dialog, bg='#334155')
        table_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Scrollbars
        vsb = tk.Scrollbar(table_frame, orient="vertical")
        hsb = tk.Scrollbar(table_frame, orient="horizontal")
        
        # Treeview
        columns = ("Select", "PID", "Process Name", "CPU %", "Memory %")
        tree = ttk.Treeview(table_frame, columns=columns, show='headings',
                           yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                           selectmode='extended')
        
        vsb.config(command=tree.yview)
        hsb.config(command=tree.xview)
        
        # Configure columns
        tree.heading("Select", text="✓")
        tree.column("Select", width=40, anchor='center')
        tree.heading("PID", text="PID")
        tree.column("PID", width=80, anchor='center')
        tree.heading("Process Name", text="Process Name")
        tree.column("Process Name", width=250)
        tree.heading("CPU %", text="CPU %")
        tree.column("CPU %", width=80, anchor='center')
        tree.heading("Memory %", text="Memory %")
        tree.column("Memory %", width=100, anchor='center')
        
        # Sort by CPU usage
        all_processes.sort(key=lambda x: x['cpu'], reverse=True)
        
        # Insert processes
        for proc in all_processes[:50]:  # Show top 50
            tree.insert('', tk.END, values=(
                '',
                proc['pid'],
                proc['name'],
                f"{proc['cpu']:.1f}%",
                f"{proc['memory']:.2f}%"
            ))
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Selection tracking
        selected_items = []
        
        def on_select(event):
            if len(tree.selection()) > num_processes:
                # Deselect the oldest selection
                tree.selection_remove(tree.selection()[0])
        
        tree.bind('<<TreeviewSelect>>', on_select)
        
        # Instructions
        inst_label = tk.Label(dialog, 
                             text=f"Select up to {num_processes} processes (Click to select, Ctrl+Click for multiple)", 
                             font=('Arial', 9), 
                             bg='#1e293b', fg='#fbbf24')
        inst_label.pack(pady=5)
        
        # Buttons
        btn_frame = tk.Frame(dialog, bg='#1e293b')
        btn_frame.pack(pady=10)
        
        result = {'processes': None}
        
        def submit():
            selected = tree.selection()
            if len(selected) == 0:
                messagebox.showwarning("No Selection", "Please select at least one process!")
                return
            
            if len(selected) > num_processes:
                messagebox.showwarning("Too Many", f"Please select maximum {num_processes} processes!")
                return
            
            processes = []
            for i, item in enumerate(selected):
                values = tree.item(item)['values']
                pid = values[1]
                name = values[2]
                
                # Find original process data
                proc_data = next((p for p in all_processes if p['pid'] == pid), None)
                
                if proc_data:
                    # Simulate burst time based on CPU usage
                    burst = max(3, min(15, int(proc_data['cpu'] / 10) + np.random.randint(3, 8)))
                    # Priority based on nice value (lower is higher priority)
                    priority = max(1, min(5, abs(proc_data['priority']) % 5 + 1))
                    
                    processes.append({
                        'name': name,
                        'arrival': i * 2,
                        'burst': burst,
                        'priority': priority
                    })
            
            result['processes'] = processes
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        def auto_select():
            # Auto-select top N by CPU usage
            tree.selection_set(tree.get_children()[:num_processes])
        
        tk.Button(btn_frame, text="Auto Select Top Processes", command=auto_select,
                 bg='#8b5cf6', fg='white', font=('Arial', 10, 'bold'),
                 padx=20, pady=8).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Submit", command=submit,
                 bg='#10b981', fg='white', font=('Arial', 11, 'bold'),
                 padx=30, pady=10).pack(side=tk.LEFT, padx=5)
        
        tk.Button(btn_frame, text="Cancel", command=cancel,
                 bg='#6b7280', fg='white', font=('Arial', 11, 'bold'),
                 padx=30, pady=10).pack(side=tk.LEFT, padx=5)
        
        dialog.wait_window()
        
        return result['processes']
    
    def simulate_scheduling(self, processes, algorithm, quantum):
        """Simulate CPU scheduling"""
        n = len(processes)
        proc_list = []
        
        for i, p in enumerate(processes):
            proc_list.append({
                'pid': 1000 + i,
                'name': p['name'],
                'arrival': p['arrival'],
                'burst': p['burst'],
                'remaining': p['burst'],
                'priority': p['priority'],
                'wait': 0,
                'turnaround': 0,
                'completion': 0,
                'response': -1,
                'state': 'NEW'
            })
        
        current_time = 0
        completed = 0
        context_switches = 0
        current_proc = None
        switch_log = []
        
        if algorithm == "RR":
            # Round Robin
            queue = []
            while completed < n:
                # Add arrived processes
                for p in proc_list:
                    if p['arrival'] == current_time and p['state'] == 'NEW':
                        p['state'] = 'READY'
                        queue.append(p)
                
                if not queue:
                    current_time += 1
                    continue
                
                proc = queue.pop(0)
                
                if current_proc != proc:
                    context_switches += 1
                    switch_log.append({
                        'time': current_time,
                        'from': current_proc['name'] if current_proc else 'IDLE',
                        'to': proc['name']
                    })
                    current_proc = proc
                
                if proc['response'] == -1:
                    proc['response'] = current_time - proc['arrival']
                
                exec_time = min(quantum, proc['remaining'])
                proc['remaining'] -= exec_time
                current_time += exec_time
                
                # Update wait times
                for p in proc_list:
                    if p['state'] == 'READY' and p != proc:
                        p['wait'] += exec_time
                
                if proc['remaining'] == 0:
                    proc['state'] = 'COMPLETED'
                    proc['completion'] = current_time
                    proc['turnaround'] = proc['completion'] - proc['arrival']
                    completed += 1
                else:
                    queue.append(proc)
        
        elif algorithm == "FCFS":
            # FCFS
            proc_list.sort(key=lambda x: x['arrival'])
            for proc in proc_list:
                if current_time < proc['arrival']:
                    current_time = proc['arrival']
                
                if current_proc != proc:
                    context_switches += 1
                    switch_log.append({
                        'time': current_time,
                        'from': current_proc['name'] if current_proc else 'IDLE',
                        'to': proc['name']
                    })
                    current_proc = proc
                
                proc['response'] = current_time - proc['arrival']
                proc['wait'] = current_time - proc['arrival']
                current_time += proc['burst']
                proc['completion'] = current_time
                proc['turnaround'] = proc['completion'] - proc['arrival']
                proc['state'] = 'COMPLETED'
        
        elif algorithm == "PRIORITY":
            # Priority Scheduling
            while completed < n:
                ready = [p for p in proc_list if p['arrival'] <= current_time and p['remaining'] > 0]
                if not ready:
                    current_time += 1
                    continue
                
                proc = min(ready, key=lambda x: x['priority'])
                
                if current_proc != proc:
                    context_switches += 1
                    switch_log.append({
                        'time': current_time,
                        'from': current_proc['name'] if current_proc else 'IDLE',
                        'to': proc['name']
                    })
                    current_proc = proc
                
                if proc['response'] == -1:
                    proc['response'] = current_time - proc['arrival']
                
                proc['remaining'] -= 1
                current_time += 1
                
                # Update wait times
                for p in proc_list:
                    if p != proc and p['arrival'] <= current_time and p['remaining'] > 0:
                        p['wait'] += 1
                
                if proc['remaining'] == 0:
                    proc['state'] = 'COMPLETED'
                    proc['completion'] = current_time
                    proc['turnaround'] = proc['completion'] - proc['arrival']
                    completed += 1
        
        return {
            'processes': proc_list,
            'switches': switch_log,
            'context_switches': context_switches,
            'total_time': current_time,
            'algorithm': algorithm
        }
    
    def save_simulation_results(self, result):
        """Save results to CSV files"""
        # Process data
        df_proc = pd.DataFrame(result['processes'])
        df_proc = df_proc.rename(columns={
            'pid': 'PID',
            'name': 'Process Name',
            'arrival': 'Arrival Time',
            'burst': 'Burst Time',
            'completion': 'Completion Time',
            'turnaround': 'Turnaround Time',
            'wait': 'Wait Time',
            'response': 'Response Time',
            'priority': 'Priority',
            'state': 'State'
        })
        df_proc = df_proc[['PID', 'Process Name', 'Arrival Time', 'Burst Time', 
                           'Completion Time', 'Turnaround Time', 'Wait Time', 
                           'Response Time', 'Priority', 'State']]
        df_proc.to_csv('context_switch_log.csv', index=False)
        
        # Switch data
        if result['switches']:
            df_switch = pd.DataFrame(result['switches'])
            df_switch.columns = ['Time', 'From Process', 'To Process']
            df_switch.to_csv('context_switches.csv', index=False)
    
    def load_data_from_memory(self, result):
        """Load data from simulation result"""
        df_proc = pd.DataFrame(result['processes'])
        self.process_data = pd.DataFrame({
            'PID': df_proc['pid'],
            'Process Name': df_proc['name'],
            'Arrival Time': df_proc['arrival'],
            'Burst Time': df_proc['burst'],
            'Completion Time': df_proc['completion'],
            'Turnaround Time': df_proc['turnaround'],
            'Wait Time': df_proc['wait'],
            'Response Time': df_proc['response'],
            'Priority': df_proc['priority'],
            'State': df_proc['state']
        })
        
        if result['switches']:
            self.switch_data = pd.DataFrame(result['switches'])
        
        self.update_display()
    
    def load_data(self):
        """Load data from CSV files"""
        try:
            if os.path.exists('context_switch_log.csv'):
                self.process_data = pd.read_csv('context_switch_log.csv')
            else:
                filename = filedialog.askopenfilename(
                    title="Select Process Log CSV",
                    filetypes=[("CSV files", "*.csv")]
                )
                if not filename:
                    return
                self.process_data = pd.read_csv(filename)
            
            if os.path.exists('context_switches.csv'):
                self.switch_data = pd.read_csv('context_switches.csv')
            
            self.update_display()
            messagebox.showinfo("Success", "Data loaded successfully!")
            self.status_bar.config(text="✓ Data loaded from CSV")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data:\n{str(e)}")
    
    def clear_data(self):
        """Clear all data and visualizations"""
        self.process_data = None
        self.switch_data = None
        
        for widget in self.gantt_frame.winfo_children():
            widget.destroy()
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for key in self.stats_labels:
            self.stats_labels[key].config(text="--")
        
        self.status_bar.config(text="Data cleared")
    
    def update_display(self):
        if self.process_data is None:
            return
        
        self.update_statistics()
        self.update_process_table()
        self.create_gantt_chart()
        self.create_performance_graphs()
    
    def update_statistics(self):
        df = self.process_data
        
        total_proc = len(df)
        context_switches = len(self.switch_data) if self.switch_data is not None else 0
        avg_wait = df['Wait Time'].mean()
        avg_turnaround = df['Turnaround Time'].mean()
        
        total_burst = df['Burst Time'].sum()
        total_time = df['Completion Time'].max()
        cpu_util = (total_burst / total_time * 100) if total_time > 0 else 0
        throughput = total_proc / total_time if total_time > 0 else 0
        
        self.stats_labels['total_proc'].config(text=str(total_proc))
        self.stats_labels['context_switches'].config(text=str(context_switches))
        self.stats_labels['avg_wait'].config(text=f"{avg_wait:.2f}")
        self.stats_labels['avg_turnaround'].config(text=f"{avg_turnaround:.2f}")
        self.stats_labels['cpu_util'].config(text=f"{cpu_util:.1f}%")
        self.stats_labels['throughput'].config(text=f"{throughput:.3f}")
    
    def update_process_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for _, row in self.process_data.iterrows():
            values = (
                row['PID'],
                row['Process Name'],
                row['Arrival Time'],
                row['Burst Time'],
                row['Completion Time'],
                row['Turnaround Time'],
                row['Wait Time'],
                row['Response Time'],
                row['Priority'],
                row['State']
            )
            
            tag = 'completed' if row['State'] == 'COMPLETED' else ''
            self.tree.insert('', tk.END, values=values, tags=(tag,))
    
    def create_gantt_chart(self):
        for widget in self.gantt_frame.winfo_children():
            widget.destroy()
        
        fig = Figure(figsize=(12, 6), facecolor='#1e293b')
        ax = fig.add_subplot(111, facecolor='#334155')
        
        df = self.process_data.sort_values('Arrival Time')
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(df)))
        
        for i, (_, proc) in enumerate(df.iterrows()):
            start_time = proc['Completion Time'] - proc['Burst Time']
            ax.barh(proc['Process Name'], 
                   proc['Burst Time'],
                   left=start_time,
                   color=colors[i],
                   edgecolor='white',
                   linewidth=2)
            
            ax.text(start_time + proc['Burst Time'] / 2,
                   i, 
                   f"{proc['Process Name']}\n{proc['Burst Time']}",
                   ha='center', va='center',
                   fontsize=9, fontweight='bold')
        
        ax.set_xlabel('Time Units', fontsize=12, color='white', fontweight='bold')
        ax.set_ylabel('Processes', fontsize=12, color='white', fontweight='bold')
        ax.set_title('Gantt Chart - Process Execution Timeline', 
                    fontsize=14, color='#60a5fa', fontweight='bold', pad=20)
        
        ax.tick_params(colors='white', labelsize=10)
        ax.grid(True, alpha=0.3, color='white', linestyle='--')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.gantt_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def create_performance_graphs(self):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        fig = Figure(figsize=(14, 8), facecolor='#1e293b')
        
        df = self.process_data
        
        # Wait Time Chart
        ax1 = fig.add_subplot(221, facecolor='#334155')
        ax1.bar(df['Process Name'], df['Wait Time'], color='#fbbf24', 
                edgecolor='white', linewidth=1.5)
        ax1.set_title('Wait Time per Process', fontsize=12, color='#60a5fa', 
                     fontweight='bold')
        ax1.set_xlabel('Process', fontsize=10, color='white')
        ax1.set_ylabel('Wait Time', fontsize=10, color='white')
        ax1.tick_params(colors='white', labelsize=8)
        ax1.grid(True, alpha=0.3, color='white', linestyle='--')
        
        # Turnaround Time Chart
        ax2 = fig.add_subplot(222, facecolor='#334155')
        ax2.bar(df['Process Name'], df['Turnaround Time'], color='#34d399', 
                edgecolor='white', linewidth=1.5)
        ax2.set_title('Turnaround Time per Process', fontsize=12, color='#60a5fa', 
                     fontweight='bold')
        ax2.set_xlabel('Process', fontsize=10, color='white')
        ax2.set_ylabel('Turnaround Time', fontsize=10, color='white')
        ax2.tick_params(colors='white', labelsize=8)
        ax2.grid(True, alpha=0.3, color='white', linestyle='--')
        
        # Response Time Chart
        ax3 = fig.add_subplot(223, facecolor='#334155')
        ax3.bar(df['Process Name'], df['Response Time'], color='#8b5cf6', 
                edgecolor='white', linewidth=1.5)
        ax3.set_title('Response Time per Process', fontsize=12, color='#60a5fa', 
                     fontweight='bold')
        ax3.set_xlabel('Process', fontsize=10, color='white')
        ax3.set_ylabel('Response Time', fontsize=10, color='white')
        ax3.tick_params(colors='white', labelsize=8)
        ax3.grid(True, alpha=0.3, color='white', linestyle='--')
        
        # Comparison Chart
        ax4 = fig.add_subplot(224, facecolor='#334155')
        x = np.arange(len(df))
        width = 0.25
        
        ax4.bar(x - width, df['Wait Time'], width, label='Wait Time', color='#fbbf24')
        ax4.bar(x, df['Turnaround Time'], width, label='Turnaround Time', color='#34d399')
        ax4.bar(x + width, df['Response Time'], width, label='Response Time', color='#8b5cf6')
        
        ax4.set_title('Performance Comparison', fontsize=12, color='#60a5fa', 
                     fontweight='bold')
        ax4.set_xlabel('Process', fontsize=10, color='white')
        ax4.set_ylabel('Time Units', fontsize=10, color='white')
        ax4.set_xticks(x)
        ax4.set_xticklabels(df['Process Name'], rotation=45, ha='right')
        ax4.legend(facecolor='#1e293b', edgecolor='white', labelcolor='white')
        ax4.tick_params(colors='white', labelsize=8)
        ax4.grid(True, alpha=0.3, color='white', linestyle='--')
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, self.graph_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = ContextSwitchVisualizer(root)
    root.mainloop()