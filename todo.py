# A feature-rich GUI to-do list application with a tabbed interface
import customtkinter
import json
import os
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, date
from functools import partial

# --- Appearance Settings ---
customtkinter.set_appearance_mode("light")
customtkinter.set_default_color_theme("green") # Complements the new color scheme

class EditTaskDialog(customtkinter.CTkToplevel):
    def __init__(self, parent, task_info):
        super().__init__(parent)
        self.parent = parent
        self.task_info = task_info

        self.title("Edit Task")
        self.geometry("400x250")
        self.transient(parent)
        self.grab_set()

        self.setup_ui()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)

        self.entry_task = customtkinter.CTkEntry(self, font=self.parent.normal_font, width=350)
        self.entry_task.grid(row=0, column=0, padx=20, pady=10, columnspan=2)
        self.entry_task.insert(0, self.task_info['text'])

        self.priority_menu = customtkinter.CTkOptionMenu(self, values=["Low", "Medium", "High"], font=self.parent.normal_font)
        self.priority_menu.grid(row=1, column=0, padx=20, pady=10, sticky="w")
        self.priority_menu.set(self.task_info['priority'])

        self.due_date_entry = DateEntry(self, width=12, background='#E0E0E0', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', font=self.parent.date_font)
        self.due_date_entry.grid(row=1, column=1, padx=20, pady=10, sticky="e")
        self.due_date_entry.set_date(datetime.strptime(self.task_info['due_date'], "%Y-%m-%d"))

        save_button = customtkinter.CTkButton(self, text="Save", command=self.save_changes, font=self.parent.button_font)
        save_button.grid(row=2, column=0, padx=20, pady=20, sticky="ew")

        cancel_button = customtkinter.CTkButton(self, text="Cancel", command=self.destroy, font=self.parent.button_font, fg_color="gray")
        cancel_button.grid(row=2, column=1, padx=20, pady=20, sticky="ew")

    def save_changes(self):
        new_text = self.entry_task.get()
        if not new_text:
            messagebox.showwarning("Input Error", "Task text cannot be empty.", parent=self)
            return
        self.task_info['text'] = new_text
        self.task_info['priority'] = self.priority_menu.get()
        self.task_info['due_date'] = self.due_date_entry.get_date().strftime("%Y-%m-%d")
        self.parent.refresh_task_lists()
        self.parent.save_tasks()
        self.destroy()

class TodoApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Tabbed To-Do List")
        self.geometry("800x700")
        self.resizable(False, False)

        self.tasks_file = "tasks.json"
        self.font_family = "Century Gothic"
        self.tasks = []
        self.setup_fonts()
        self.setup_ui()
        self.load_tasks()

    def setup_fonts(self):
        self.normal_font = customtkinter.CTkFont(family=self.font_family, size=15)
        self.strikethrough_font = customtkinter.CTkFont(family=self.font_family, size=15, overstrike=True)
        self.button_font = customtkinter.CTkFont(family=self.font_family, size=12, weight="bold")
        self.tab_font = customtkinter.CTkFont(family=self.font_family, size=16, weight="bold")
        self.date_font = (self.font_family, 14) # Font for tkcalendar

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Input Frame ---
        self.input_frame = customtkinter.CTkFrame(self, corner_radius=0)
        self.input_frame.grid(row=0, column=0, padx=0, pady=0, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.entry_task = customtkinter.CTkEntry(self.input_frame, placeholder_text="Enter a new task...", height=40, font=self.normal_font, corner_radius=0, border_width=0)
        self.entry_task.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="ew")
        self.priority_menu = customtkinter.CTkOptionMenu(self.input_frame, values=["Low", "Medium", "High"], font=self.normal_font, height=40)
        self.priority_menu.grid(row=0, column=1, padx=5, pady=10)
        self.priority_menu.set("Medium")
        self.due_date_entry = DateEntry(self.input_frame, width=12, background='#E0E0E0', foreground='black', borderwidth=2, date_pattern='yyyy-mm-dd', font=self.date_font)
        self.due_date_entry.grid(row=0, column=2, padx=5, pady=10)
        self.add_button = customtkinter.CTkButton(self.input_frame, text="Add Task", command=self.add_task, height=40, font=self.button_font)
        self.add_button.grid(row=0, column=3, padx=(5, 10), pady=10)

        # --- Tab View for Task Lists ---
        self.tab_view = customtkinter.CTkTabview(self, corner_radius=10)
        # Workaround to set tab font, as it's not a direct constructor argument
        self.tab_view._segmented_button.configure(font=self.tab_font)
        self.tab_view.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.tab_view.add("📝 Upcoming")
        self.tab_view.add("❗ Overdue")
        self.tab_view.add("✅ Completed")

        # --- Create Scrollable Frames inside each tab ---
        self.upcoming_frame = customtkinter.CTkScrollableFrame(self.tab_view.tab("📝 Upcoming"), corner_radius=0, fg_color="transparent")
        self.upcoming_frame.pack(fill="both", expand=True)

        self.overdue_frame = customtkinter.CTkScrollableFrame(self.tab_view.tab("❗ Overdue"), corner_radius=0, fg_color="transparent")
        self.overdue_frame.pack(fill="both", expand=True)

        self.completed_frame = customtkinter.CTkScrollableFrame(self.tab_view.tab("✅ Completed"), corner_radius=0, fg_color="transparent")
        self.completed_frame.pack(fill="both", expand=True)

    def add_task(self):
        task_text = self.entry_task.get()
        if not task_text:
            messagebox.showwarning("Input Error", "Please enter a task.")
            return

        task_info = {
            'id': datetime.now().timestamp(),
            'text': task_text,
            'priority': self.priority_menu.get(),
            'due_date': self.due_date_entry.get_date().strftime("%Y-%m-%d"),
            'completed': False
        }
        self.tasks.append(task_info)
        self.entry_task.delete(0, "end")
        self.refresh_task_lists()
        self.save_tasks()

    def render_task(self, task_info, parent_frame):
        task_frame = customtkinter.CTkFrame(parent_frame, corner_radius=5)
        task_frame.pack(fill="x", padx=5, pady=5)

        checkbox = customtkinter.CTkCheckBox(task_frame, text=task_info['text'], font=self.normal_font, command=partial(self.toggle_task_completion, task_info))
        checkbox.pack(side="left", padx=10, pady=10, expand=True, fill="x")
        if task_info['completed']: checkbox.select()

        delete_button = customtkinter.CTkButton(task_frame, text="Del", width=40, font=self.button_font, fg_color="#D32F2F", hover_color="#B71C1C", command=partial(self.delete_task, task_info))
        delete_button.pack(side="right", padx=(5,10), pady=10)
        edit_button = customtkinter.CTkButton(task_frame, text="Edit", width=40, font=self.button_font, command=partial(self.edit_task, task_info))
        edit_button.pack(side="right", padx=5, pady=10)

        priority_colors = {"High": "#FF6347", "Medium": "#FFA500", "Low": "#20B2AA"} # Coral, Orange, LightSeaGreen
        priority_label = customtkinter.CTkLabel(task_frame, text=task_info['priority'], text_color=priority_colors.get(task_info['priority'], "white"), font=self.normal_font)
        priority_label.pack(side="right", padx=10, pady=10)

        due_date_label = customtkinter.CTkLabel(task_frame, text=f"Due: {task_info['due_date']}", font=self.normal_font)
        due_date_label.pack(side="right", padx=10, pady=10)

        self.update_task_appearance(checkbox, due_date_label, task_info)

    def update_task_appearance(self, checkbox, due_date_label, task_info):
        is_completed = task_info['completed']
        font = self.strikethrough_font if is_completed else self.normal_font
        default_text_color = customtkinter.ThemeManager.theme["CTkLabel"]["text_color"]
        completed_color = "#2E8B57" # SeaGreen

        checkbox.configure(font=font)
        if is_completed:
            checkbox.configure(text_color=completed_color)
        else:
            checkbox.configure(text_color=default_text_color)

        due_date_obj = datetime.strptime(task_info['due_date'], "%Y-%m-%d").date()
        is_overdue = due_date_obj < date.today()

        if not is_completed and is_overdue:
            due_date_label.configure(text_color="#E53935") # Overdue color remains red
        else:
            due_date_label.configure(text_color=default_text_color)

    def toggle_task_completion(self, task_info):
        task_info['completed'] = not task_info['completed']
        self.refresh_task_lists()
        self.save_tasks()

    def delete_task(self, task_to_delete):
        if messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete the task: \n'{task_to_delete['text']}'?"):
            self.tasks = [t for t in self.tasks if t['id'] != task_to_delete['id']]
            self.refresh_task_lists()
            self.save_tasks()

    def edit_task(self, task_info):
        EditTaskDialog(self, task_info)

    def refresh_task_lists(self):
        for frame in [self.upcoming_frame, self.overdue_frame, self.completed_frame]:
            for widget in frame.winfo_children():
                widget.destroy()

        priority_map = {"High": 2, "Medium": 1, "Low": 0}

        completed_tasks = [t for t in self.tasks if t['completed']]
        active_tasks = [t for t in self.tasks if not t['completed']]
        overdue_tasks = [t for t in active_tasks if datetime.strptime(t['due_date'], "%Y-%m-%d").date() < date.today()]
        upcoming_tasks = [t for t in active_tasks if t not in overdue_tasks]
        
        upcoming_tasks.sort(key=lambda t: priority_map.get(t['priority'], 0), reverse=True)

        for task in upcoming_tasks:
            self.render_task(task, self.upcoming_frame)
        for task in overdue_tasks:
            self.render_task(task, self.overdue_frame)
        for task in completed_tasks:
            self.render_task(task, self.completed_frame)

    def save_tasks(self):
        with open(self.tasks_file, 'w') as f:
            json.dump(self.tasks, f, indent=4)

    def load_tasks(self):
        if not os.path.exists(self.tasks_file):
            return
        try:
            with open(self.tasks_file, 'r') as f:
                self.tasks = json.load(f)
            for task in self.tasks:
                if 'id' not in task:
                    task['id'] = datetime.now().timestamp()
        except (json.JSONDecodeError, FileNotFoundError):
            self.tasks = []
        self.refresh_task_lists()

if __name__ == "__main__":
    app = TodoApp()
    app.mainloop()
