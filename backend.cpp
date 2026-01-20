#include <iostream>
#include <fstream>
#include <vector>
#include <queue>
#include <algorithm>
#include <iomanip>
#include <sstream>
#include <ctime>
#include <cstdlib>
#include <string>

#ifdef _WIN32
#include <windows.h>
#include <tlhelp32.h>
#include <psapi.h>
#else
#include <unistd.h>
#include <sys/types.h>
#include <dirent.h>
#endif

using namespace std;

// Process structure
struct Process {
    int pid;
    string name;
    int arrivalTime;
    int burstTime;
    int remainingTime;
    int waitTime;
    int turnaroundTime;
    int completionTime;
    int responseTime;
    int priority;
    string state; // NEW, READY, RUNNING, COMPLETED
    
    Process(int p, string n, int at, int bt, int pr = 3) 
        : pid(p), name(n), arrivalTime(at), burstTime(bt), 
          remainingTime(bt), waitTime(0), turnaroundTime(0),
          completionTime(0), responseTime(-1), priority(pr), state("NEW") {}
};

// Context Switch Event for logging
struct ContextSwitchEvent {
    int time;
    int fromPID;
    int toPID;
    string fromProcess;
    string toProcess;
    string reason;
};

class ProcessScheduler {
private:
    vector<Process> processes;
    vector<ContextSwitchEvent> switchLog;
    queue<int> readyQueue;
    int currentTime;
    int timeQuantum;
    int contextSwitches;
    Process* currentProcess;
    string algorithm;
    
public:
    ProcessScheduler(int quantum = 2, string algo = "RR") 
        : currentTime(0), timeQuantum(quantum), contextSwitches(0), 
          currentProcess(nullptr), algorithm(algo) {}
    
    // Add process to scheduler
    void addProcess(Process p) {
        processes.push_back(p);
    }
    
    // Get system processes (Windows)
    #ifdef _WIN32
    void fetchSystemProcesses(int count = 10) {
        HANDLE hSnapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
        if (hSnapshot == INVALID_HANDLE_VALUE) {
            cout << "Failed to get process snapshot!\n";
            return;
        }
        
        PROCESSENTRY32 pe32;
        pe32.dwSize = sizeof(PROCESSENTRY32);
        
        int added = 0;
        int arrivalTime = 0;
        
        if (Process32First(hSnapshot, &pe32)) {
            do {
                if (added >= count) break;
                
                // Generate random burst time (simulation)
                int burstTime = (rand() % 10) + 3;
                int priority = (rand() % 5) + 1;
                
                // Convert TCHAR to string properly
                string processName;
                #ifdef UNICODE
                    int size = WideCharToMultiByte(CP_UTF8, 0, pe32.szExeFile, -1, NULL, 0, NULL, NULL);
                    processName.resize(size - 1);
                    WideCharToMultiByte(CP_UTF8, 0, pe32.szExeFile, -1, &processName[0], size, NULL, NULL);
                #else
                    processName = string(pe32.szExeFile);
                #endif
                
                if (!processName.empty()) {
                    Process p(pe32.th32ProcessID, processName, arrivalTime, burstTime, priority);
                    addProcess(p);
                    arrivalTime += (rand() % 3);
                    added++;
                }
            } while (Process32Next(hSnapshot, &pe32));
        }
        
        CloseHandle(hSnapshot);
        cout << "Fetched " << added << " system processes successfully!\n";
    }
    #else
    // Linux process fetching
    void fetchSystemProcesses(int count = 10) {
        DIR* dir = opendir("/proc");
        if (!dir) {
            cout << "Failed to open /proc directory!\n";
            return;
        }
        
        struct dirent* entry;
        int added = 0;
        int arrivalTime = 0;
        
        while ((entry = readdir(dir)) && added < count) {
            if (entry->d_type == DT_DIR) {
                int pid = atoi(entry->d_name);
                if (pid > 0) {
                    string cmdPath = "/proc/" + string(entry->d_name) + "/comm";
                    ifstream cmdFile(cmdPath);
                    string processName;
                    
                    if (cmdFile.is_open()) {
                        getline(cmdFile, processName);
                        cmdFile.close();
                        
                        int burstTime = (rand() % 10) + 3;
                        int priority = (rand() % 5) + 1;
                        
                        Process p(pid, processName, arrivalTime, burstTime, priority);
                        addProcess(p);
                        
                        arrivalTime += (rand() % 3);
                        added++;
                    }
                }
            }
        }
        closedir(dir);
        cout << "Fetched " << added << " system processes successfully!\n";
    }
    #endif
    
    // Add user-defined processes
    void addUserProcesses() {
        cout << "\n=== Add Custom Processes ===\n";
        int numProcesses;
        cout << "Enter number of processes: ";
        cin >> numProcesses;
        
        for (int i = 0; i < numProcesses; i++) {
            string name;
            int arrivalTime, burstTime, priority;
            
            cout << "\nProcess " << (i + 1) << ":\n";
            cout << "Name: ";
            cin >> name;
            cout << "Arrival Time: ";
            cin >> arrivalTime;
            cout << "Burst Time: ";
            cin >> burstTime;
            cout << "Priority (1-5): ";
            cin >> priority;
            
            Process p(1000 + i, name, arrivalTime, burstTime, priority);
            addProcess(p);
        }
    }
    
    // Context switch
    void performContextSwitch(Process* from, Process* to, string reason) {
        contextSwitches++;
        
        ContextSwitchEvent event;
        event.time = currentTime;
        event.fromPID = from ? from->pid : -1;
        event.toPID = to ? to->pid : -1;
        event.fromProcess = from ? from->name : "IDLE";
        event.toProcess = to ? to->name : "IDLE";
        event.reason = reason;
        
        switchLog.push_back(event);
        
        // Display context switch
        cout << "[Time " << currentTime << "] Context Switch: " 
             << event.fromProcess << " -> " << event.toProcess 
             << " (" << reason << ")\n";
    }
    
    // Round Robin Scheduling
    void roundRobinSchedule() {
        queue<int> readyQueue;
        int completed = 0;
        int n = processes.size();
        
        cout << "\n--- Starting Round Robin Scheduling ---\n";
        
        while (completed < n) {
            // Check for newly arrived processes
            for (int i = 0; i < n; i++) {
                if (processes[i].arrivalTime == currentTime && processes[i].state == "NEW") {
                    processes[i].state = "READY";
                    readyQueue.push(i);
                    cout << "[Time " << currentTime << "] Process " 
                         << processes[i].name << " arrived\n";
                }
            }
            
            if (readyQueue.empty()) {
                currentTime++;
                continue;
            }
            
            int idx = readyQueue.front();
            readyQueue.pop();
            
            Process* prev = currentProcess;
            currentProcess = &processes[idx];
            
            if (prev != currentProcess) {
                performContextSwitch(prev, currentProcess, "TIME_QUANTUM");
            }
            
            currentProcess->state = "RUNNING";
            
            if (currentProcess->responseTime == -1) {
                currentProcess->responseTime = currentTime - currentProcess->arrivalTime;
            }
            
            // Execute for time quantum or remaining time
            int execTime = min(timeQuantum, currentProcess->remainingTime);
            
            for (int t = 0; t < execTime; t++) {
                currentTime++;
                currentProcess->remainingTime--;
                
                // Update wait time for other ready processes
                for (int i = 0; i < n; i++) {
                    if (processes[i].state == "READY" && i != idx) {
                        processes[i].waitTime++;
                    }
                }
                
                // Check for new arrivals during execution
                for (int i = 0; i < n; i++) {
                    if (processes[i].arrivalTime == currentTime && processes[i].state == "NEW") {
                        processes[i].state = "READY";
                        readyQueue.push(i);
                        cout << "[Time " << currentTime << "] Process " 
                             << processes[i].name << " arrived\n";
                    }
                }
            }
            
            if (currentProcess->remainingTime == 0) {
                currentProcess->state = "COMPLETED";
                currentProcess->completionTime = currentTime;
                currentProcess->turnaroundTime = currentProcess->completionTime - currentProcess->arrivalTime;
                cout << "[Time " << currentTime << "] Process " 
                     << currentProcess->name << " completed\n";
                completed++;
            } else {
                currentProcess->state = "READY";
                readyQueue.push(idx);
            }
        }
    }
    
    // FCFS Scheduling
    void fcfsSchedule() {
        sort(processes.begin(), processes.end(), 
             [](const Process& a, const Process& b) {
                 return a.arrivalTime < b.arrivalTime;
             });
        
        cout << "\n--- Starting FCFS Scheduling ---\n";
        
        for (auto& proc : processes) {
            if (currentTime < proc.arrivalTime) {
                currentTime = proc.arrivalTime;
            }
            
            Process* prev = currentProcess;
            currentProcess = &proc;
            performContextSwitch(prev, currentProcess, "FCFS");
            
            proc.state = "RUNNING";
            proc.responseTime = currentTime - proc.arrivalTime;
            proc.waitTime = currentTime - proc.arrivalTime;
            
            currentTime += proc.burstTime;
            proc.remainingTime = 0;
            
            proc.completionTime = currentTime;
            proc.turnaroundTime = proc.completionTime - proc.arrivalTime;
            proc.state = "COMPLETED";
            
            cout << "[Time " << currentTime << "] Process " 
                 << proc.name << " completed\n";
        }
    }
    
    // Priority Scheduling
    void prioritySchedule() {
        int completed = 0;
        int n = processes.size();
        
        cout << "\n--- Starting Priority Scheduling ---\n";
        
        while (completed < n) {
            int idx = -1;
            int highestPriority = 9999;
            
            // Find highest priority ready process
            for (int i = 0; i < n; i++) {
                if (processes[i].arrivalTime <= currentTime && 
                    processes[i].remainingTime > 0 &&
                    processes[i].priority < highestPriority) {
                    highestPriority = processes[i].priority;
                    idx = i;
                }
            }
            
            if (idx == -1) {
                currentTime++;
                continue;
            }
            
            Process* prev = currentProcess;
            currentProcess = &processes[idx];
            
            if (prev != currentProcess) {
                performContextSwitch(prev, currentProcess, "PRIORITY");
            }
            
            if (currentProcess->responseTime == -1) {
                currentProcess->responseTime = currentTime - currentProcess->arrivalTime;
            }
            
            currentProcess->state = "RUNNING";
            currentTime++;
            currentProcess->remainingTime--;
            
            // Update wait time for other processes
            for (int i = 0; i < n; i++) {
                if (i != idx && processes[i].arrivalTime <= currentTime && 
                    processes[i].remainingTime > 0) {
                    processes[i].waitTime++;
                }
            }
            
            if (currentProcess->remainingTime == 0) {
                currentProcess->state = "COMPLETED";
                currentProcess->completionTime = currentTime;
                currentProcess->turnaroundTime = currentProcess->completionTime - currentProcess->arrivalTime;
                cout << "[Time " << currentTime << "] Process " 
                     << currentProcess->name << " completed\n";
                completed++;
            }
        }
    }
    
    // Start scheduling
    void startScheduling() {
        cout << "\n========================================\n";
        cout << "   Starting " << algorithm << " Scheduling\n";
        cout << "========================================\n";
        
        clock_t start = clock();
        
        if (algorithm == "RR") {
            roundRobinSchedule();
        } else if (algorithm == "FCFS") {
            fcfsSchedule();
        } else if (algorithm == "PRIORITY") {
            prioritySchedule();
        }
        
        clock_t end = clock();
        double duration = double(end - start) / CLOCKS_PER_SEC * 1000;
        
        cout << "\n========================================\n";
        cout << "Scheduling completed in " << duration << "ms\n";
        cout << "Total Context Switches: " << contextSwitches << "\n";
        cout << "========================================\n";
    }
    
    // Save results to CSV
    void saveToCSV(const string& filename = "context_switch_log.csv") {
        ofstream file(filename);
        
        if (!file.is_open()) {
            cerr << "Error opening file for writing!\n";
            return;
        }
        
        // Process details
        file << "PID,Process Name,Arrival Time,Burst Time,Completion Time,";
        file << "Turnaround Time,Wait Time,Response Time,Priority,State\n";
        
        for (const auto& p : processes) {
            file << p.pid << "," << p.name << "," << p.arrivalTime << ",";
            file << p.burstTime << "," << p.completionTime << ",";
            file << p.turnaroundTime << "," << p.waitTime << ",";
            file << p.responseTime << "," << p.priority << "," << p.state << "\n";
        }
        
        file.close();
        cout << "\n✓ Process data saved to: " << filename << "\n";
        
        // Context switch log
        ofstream switchFile("context_switches.csv");
        switchFile << "Time,From PID,From Process,To PID,To Process,Reason\n";
        
        for (const auto& event : switchLog) {
            switchFile << event.time << "," << event.fromPID << ",";
            switchFile << event.fromProcess << "," << event.toPID << ",";
            switchFile << event.toProcess << "," << event.reason << "\n";
        }
        
        switchFile.close();
        cout << "✓ Context switches saved to: context_switches.csv\n";
    }
    
    // Display statistics
    void displayStatistics() {
        cout << "\n========================================\n";
        cout << "      Scheduling Statistics\n";
        cout << "========================================\n";
        cout << fixed << setprecision(2);
        
        double avgWaitTime = 0, avgTurnaroundTime = 0, avgResponseTime = 0;
        
        for (const auto& p : processes) {
            avgWaitTime += p.waitTime;
            avgTurnaroundTime += p.turnaroundTime;
            avgResponseTime += p.responseTime;
        }
        
        int n = processes.size();
        avgWaitTime /= n;
        avgTurnaroundTime /= n;
        avgResponseTime /= n;
        
        double cpuUtilization = 0;
        for (const auto& p : processes) {
            cpuUtilization += p.burstTime;
        }
        cpuUtilization = (cpuUtilization / currentTime) * 100;
        
        cout << "Total Processes: " << n << "\n";
        cout << "Context Switches: " << contextSwitches << "\n";
        cout << "Total Time: " << currentTime << " units\n";
        cout << "CPU Utilization: " << cpuUtilization << "%\n";
        cout << "Average Wait Time: " << avgWaitTime << " units\n";
        cout << "Average Turnaround Time: " << avgTurnaroundTime << " units\n";
        cout << "Average Response Time: " << avgResponseTime << " units\n";
        cout << "Throughput: " << (double)n / currentTime << " processes/unit\n";
        cout << "========================================\n";
    }
};

int main() {
    srand(time(0));
    
    cout << "\n========================================\n";
    cout << "  CPU Context Switching Simulator\n";
    cout << "  Operating System Project\n";
    cout << "========================================\n";
    
    int choice, quantum;
    string algorithm;
    
    cout << "\nSelect Input Method:\n";
    cout << "1. Fetch System Processes\n";
    cout << "2. Enter Custom Processes\n";
    cout << "Your choice: ";
    cin >> choice;
    
    cout << "\nSelect Scheduling Algorithm:\n";
    cout << "1. Round Robin (RR)\n";
    cout << "2. First Come First Serve (FCFS)\n";
    cout << "3. Priority Scheduling\n";
    cout << "Your choice: ";
    int algoChoice;
    cin >> algoChoice;
    
    switch(algoChoice) {
        case 1: algorithm = "RR"; break;
        case 2: algorithm = "FCFS"; break;
        case 3: algorithm = "PRIORITY"; break;
        default: algorithm = "RR";
    }
    
    cout << "\nEnter Time Quantum (recommended: 2): ";
    cin >> quantum;
    
    ProcessScheduler scheduler(quantum, algorithm);
    
    if (choice == 1) {
        cout << "\nFetching system processes...\n";
        scheduler.fetchSystemProcesses(8);
    } else {
        scheduler.addUserProcesses();
    }
    
    scheduler.startScheduling();
    scheduler.displayStatistics();
    scheduler.saveToCSV();
    
    cout << "\n========================================\n";
    cout << "     Simulation Complete!\n";
    cout << "========================================\n";
    cout << "\nNow you can run the Python GUI to\n";
    cout << "visualize the results!\n\n";
    
    cout << "Press Enter to exit...";
    cin.ignore();
    cin.get();
    
    return 0;
}