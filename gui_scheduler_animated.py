import tkinter as tk
from tkinter import ttk, messagebox
from scheduler_code import Process, ProcessScheduler, generate_random_processes
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random, threading, time


class SchedulerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Heap-Based CPU Scheduler (Final Enhanced GUI)")
        self.root.geometry("1280x900")
        self.root.configure(bg="#eaf0f6")

        self.processes = []
        self.running = False
        self.paused = False
        self.speed = 1.0

        # ======================= TITLE ============================
        title = tk.Label(root, text="Heap-Based CPU Scheduler - Animated Gantt Chart with Idle Time",
                         font=("Segoe UI", 20, "bold"), bg="#003366", fg="white", pady=10)
        title.pack(fill="x")

        # ======================= INPUT AREA ======================
        frame_top = tk.Frame(root, bg="#eaf0f6", pady=5)
        frame_top.pack(pady=5)

        style_lbl = dict(bg="#eaf0f6", font=("Segoe UI", 10, "bold"))
        tk.Label(frame_top, text="PID", **style_lbl).grid(row=0, column=0, padx=5)
        tk.Label(frame_top, text="Arrival", **style_lbl).grid(row=0, column=1, padx=5)
        tk.Label(frame_top, text="Burst", **style_lbl).grid(row=0, column=2, padx=5)
        tk.Label(frame_top, text="Priority", **style_lbl).grid(row=0, column=3, padx=5)
        tk.Label(frame_top, text="Type", **style_lbl).grid(row=0, column=4, padx=5)

        self.pid = tk.Entry(frame_top, width=8, justify="center")
        self.arrival = tk.Entry(frame_top, width=8, justify="center")
        self.burst = tk.Entry(frame_top, width=8, justify="center")
        self.priority = tk.Entry(frame_top, width=8, justify="center")
        self.ptype = ttk.Combobox(frame_top, values=["CPU", "I/O"], width=7, justify="center")
        self.ptype.current(0)

        self.pid.grid(row=1, column=0, padx=3)
        self.arrival.grid(row=1, column=1, padx=3)
        self.burst.grid(row=1, column=2, padx=3)
        self.priority.grid(row=1, column=3, padx=3)
        self.ptype.grid(row=1, column=4, padx=3)

        tk.Button(frame_top, text="Add Process", command=self.add_process,
                  bg="#0066cc", fg="white", font=("Segoe UI", 9, "bold")).grid(row=1, column=5, padx=8)
        tk.Button(frame_top, text="Generate Random (5)", command=self.generate_random,
                  bg="#009933", fg="white", font=("Segoe UI", 9, "bold")).grid(row=1, column=6, padx=8)

        # ======================= MODE/ALGO + CONTROLS =====================
        frame_options = tk.Frame(root, bg="#eaf0f6", pady=10)
        frame_options.pack()

        tk.Label(frame_options, text="Mode:", bg="#eaf0f6", font=("Segoe UI", 10, "bold")).grid(row=0, column=0, padx=5)
        self.mode = ttk.Combobox(frame_options, values=["preemptive", "non-preemptive"], width=15, justify="center")
        self.mode.current(0)
        self.mode.grid(row=0, column=1, padx=5)

        tk.Label(frame_options, text="Algorithm:", bg="#eaf0f6", font=("Segoe UI", 10, "bold")).grid(row=0, column=2, padx=5)
        self.algorithm = ttk.Combobox(frame_options, values=["priority", "sjf", "fcfs"], width=15, justify="center")
        self.algorithm.current(0)
        self.algorithm.grid(row=0, column=3, padx=5)

        tk.Button(frame_options, text="Run Scheduler (Animated)", command=self.run_scheduler_thread,
                  bg="#004080", fg="white", font=("Segoe UI", 10, "bold")).grid(row=0, column=4, padx=10)
        self.pause_btn = tk.Button(frame_options, text="Pause", command=self.toggle_pause,
                                   bg="#ff9933", fg="white", font=("Segoe UI", 10, "bold"))
        self.pause_btn.grid(row=0, column=5, padx=10)

        # Animation Speed Control
        tk.Label(frame_options, text="Speed:", bg="#eaf0f6", font=("Segoe UI", 10, "bold")).grid(row=0, column=6, padx=5)
        self.speed_slider = ttk.Scale(frame_options, from_=0.5, to=3.0, orient="horizontal", value=1.0,
                                      command=self.update_speed)
        self.speed_slider.grid(row=0, column=7, padx=5)
        tk.Label(frame_options, text="x", bg="#eaf0f6", font=("Segoe UI", 10, "bold")).grid(row=0, column=8)

        # ======================= RESULTS TABLE =====================
        table_frame = tk.Frame(root, bg="#eaf0f6", pady=10)
        table_frame.pack(pady=5, fill="x")

        style = ttk.Style()
        style.theme_use("default")

        style.configure("mystyle.Treeview",
                        font=("Segoe UI", 10),
                        rowheight=26,
                        background="white",
                        fieldbackground="white",
                        bordercolor="#004080",
                        borderwidth=1)

        # --- Clearly visible colored headings ---
        style.configure("mystyle.Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background="#00509E",
                        foreground="white",
                        relief="raised")
        style.map("mystyle.Treeview.Heading",
                  background=[("active", "#0073E6")],
                  relief=[("pressed", "sunken")])

        # --- Table Frame with Border ---
        border_frame = tk.Frame(table_frame, bg="#004080", bd=2, relief="ridge")
        border_frame.pack(padx=40, pady=5, fill="x")

        # --- Treeview Table ---
        self.tree = ttk.Treeview(border_frame,
                                 style="mystyle.Treeview",
                                 columns=("PID", "Type", "Arrival", "Burst", "Priority",
                                          "Start", "Finish", "Waiting", "Turnaround", "Response"),
                                 show="headings", height=10)

        for col in self.tree["columns"]:
            self.tree.heading(col, text=col, anchor="center")
            self.tree.column(col, anchor="center", width=100)

        # --- Scrollbar ---
        yscroll = ttk.Scrollbar(border_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        yscroll.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)

        # ======================= GANTT CHART ======================
        self.fig, self.ax = plt.subplots(figsize=(10, 3))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(pady=10)

        # ======================= METRICS LABEL ====================
        self.metrics = tk.Label(root, text="", font=("Segoe UI", 11, "bold"), bg="#eaf0f6", fg="#003366")
        self.metrics.pack(pady=10)

    # =============================================================
    #                    FUNCTIONAL METHODS
    # =============================================================
    def update_speed(self, val):
        self.speed = float(val)

    def add_process(self):
        try:
            pid = self.pid.get().strip()
            if not pid:
                raise ValueError
            arrival = int(self.arrival.get())
            burst = int(self.burst.get())
            priority = int(self.priority.get())
            ptype = self.ptype.get()
            self.processes.append(Process(pid, arrival, burst, priority, ptype))
            messagebox.showinfo("Success", f"Process {pid} added successfully.")
            self.pid.delete(0, tk.END)
            self.arrival.delete(0, tk.END)
            self.burst.delete(0, tk.END)
            self.priority.delete(0, tk.END)
        except ValueError:
            messagebox.showerror("Error", "Enter valid values (PID text, others numeric).")

    def generate_random(self):
        self.processes = generate_random_processes(5)
        messagebox.showinfo("Generated", "5 random processes created successfully!")

    def toggle_pause(self):
        if not self.running:
            return
        self.paused = not self.paused
        self.pause_btn.config(text="Resume" if self.paused else "Pause",
                              bg="#28a745" if self.paused else "#ff9933")

    def run_scheduler_thread(self):
        if self.running:
            return
        t = threading.Thread(target=self.run_scheduler_animated)
        t.start()

    def run_scheduler_animated(self):
        if not self.processes:
            messagebox.showerror("Error", "No processes! Add or generate first.")
            return

        self.running = True
        scheduler = ProcessScheduler(self.processes, mode=self.mode.get(), algorithm=self.algorithm.get())
        scheduler.schedule()

        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in scheduler.completed:
            self.tree.insert("", "end",
                             values=(p.pid, p.process_type, p.arrival, p.burst,
                                     p.priority, p.start, p.finish, p.waiting,
                                     p.turnaround, p.response_time))

        self.animate_gantt_chart(scheduler)

        # Display metrics
        n = len(scheduler.completed)
        avg_wait = sum(p.waiting for p in scheduler.completed) / n
        avg_turn = sum(p.turnaround for p in scheduler.completed) / n
        self.metrics.config(text=f"CPU Utilization: {scheduler.cpu_utilization:.2f}%   |   "
                                 f"Avg Waiting: {avg_wait:.2f}   |   Avg Turnaround: {avg_turn:.2f}   |   "
                                 f"Context Switches: {scheduler.context_switches}")
        self.running = False

    # =============================================================
    #                      ANIMATION LOGIC
    # =============================================================
    def animate_gantt_chart(self, scheduler):
        self.ax.clear()
        self.ax.set_title("Animated Gantt Chart with CPU Idle Time", fontsize=11)
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Processes / CPU")

        colors = {}
        y_process = 10
        y_cpu = 5
        current_time = 0
        base_delay = 0.15

        timeline = []
        for p in scheduler.completed:
            if p.start is not None:
                timeline.append((p.start, p.finish, p.pid))
        timeline.sort(key=lambda x: x[0])

        for start, finish, pid in timeline:
            if start > current_time:
                for t in range(current_time, start):
                    while self.paused:
                        time.sleep(0.1)
                    self.ax.barh(y_cpu, width=1, left=t, height=3, color="#d3d3d3", edgecolor="black")
                    self.ax.text(t + 0.5, y_cpu, "IDLE", ha='center', va='center', fontsize=8)
                    self.ax.set_xlim(0, finish + 2)
                    self.ax.grid(True, axis='x', linestyle='--', alpha=0.6)
                    self.canvas.draw()
                    time.sleep(base_delay / self.speed)

            if pid not in colors:
                colors[pid] = "#" + ''.join(random.choices('0123456789ABCDEF', k=6))
            for t in range(start, finish):
                while self.paused:
                    time.sleep(0.1)
                self.ax.barh(y_process, width=1, left=t, height=3, color=colors[pid], edgecolor="black")
                self.ax.text(t + 0.5, y_process, pid, ha='center', va='center', fontsize=9, color='white')
                self.ax.set_xlim(0, finish + 2)
                self.ax.grid(True, axis='x', linestyle='--', alpha=0.6)
                self.canvas.draw()
                time.sleep(base_delay / self.speed)
            current_time = finish

        self.ax.set_yticks([y_cpu, y_process])
        self.ax.set_yticklabels(["CPU (Idle)", "Processes"])
        self.canvas.draw()


# -------------------------- RUN GUI ----------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = SchedulerGUI(root)
    root.mainloop()
