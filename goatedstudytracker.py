from PyQt5 import QtWidgets, QtCore, QtGui
import sys
import csv
from datetime import datetime
import os
import json
from PyQt5 import QtMultimedia

FILE_NAME = os.path.join(os.path.expanduser("~"), "study_log.csv")
JOURNAL_FILE = os.path.join(os.path.expanduser("~"), "journal_entries.csv")

PASTEL_DARK_BG = "#23243a"
PASTEL_DARK_PANEL = "#2d2e4a"
PASTEL_ACCENT = "#a3bffa"
PASTEL_GREEN = "#b8e1dd"
PASTEL_RED = "#ffb3ba"
PASTEL_PURPLE = "#d6b8ff"
PASTEL_YELLOW = "#fff5ba"
PASTEL_TEXT = "#e6e6e6"
PASTEL_OUTLINE = "#4e4e6e"

CONFIG_FILE = os.path.join(os.path.expanduser("~"), "goatedstudytracker_config.json")

def get_default_data_dir():
    return os.path.expanduser("~")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return None

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

class JournalEntry:
    def __init__(self, date, time, content, attachments, title=None):
        self.date = date
        self.time = time
        self.content = content
        self.attachments = attachments  # List of file paths
        self.title = title if title else f"{date} {time}"

class StudyTrackerApp(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📘 Goated Study Tracker")
        self.setGeometry(100, 100, 1100, 750)
        self.setStyleSheet(f"background-color: {PASTEL_DARK_BG}; color: {PASTEL_TEXT};")
        self.data_dir = self.get_or_choose_data_dir()
        self.FILE_NAME = os.path.join(self.data_dir, "study_log.csv")
        self.JOURNAL_FILE = os.path.join(self.data_dir, "journal_entries.csv")
        self.SUBJECTS_FILE = os.path.join(self.data_dir, "subjects.json")
        self.subjects = self.load_subjects()
        self.data = self.load_data()
        self.journal_entries = self.load_journal()
        self.init_ui()
        self.refresh_log()
        self.refresh_journal_list()

    def get_or_choose_data_dir(self):
        config = load_config()
        if config and "data_dir" in config and os.path.isdir(config["data_dir"]):
            return config["data_dir"]
        # Ask user to pick a folder
        msg = QtWidgets.QMessageBox()
        msg.setWindowTitle("Choose Data Folder")
        msg.setText("Choose a folder to store your study tracker data files. You can change this later from the menu.")
        msg.setIcon(QtWidgets.QMessageBox.Question)
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
        msg.exec_()
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Data Folder", get_default_data_dir())
        if not folder:
            folder = get_default_data_dir()
        save_config({"data_dir": folder})
        return folder

    def change_data_dir(self):
        folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select New Data Folder", self.data_dir)
        if folder:
            save_config({"data_dir": folder})
            QtWidgets.QMessageBox.information(self, "Restart Required", "Please restart the app to use the new data folder.")

    def load_subjects(self):
        default_subjects = ["Physics", "Chemistry", "Biology"]
        if os.path.exists(self.SUBJECTS_FILE):
            try:
                with open(self.SUBJECTS_FILE, "r") as f:
                    subjects = json.load(f)
                if isinstance(subjects, list) and all(isinstance(s, str) for s in subjects):
                    return subjects
            except Exception:
                pass
        return default_subjects

    def save_subjects(self):
        try:
            with open(self.SUBJECTS_FILE, "w") as f:
                json.dump(self.subjects, f)
        except Exception:
            pass

    def add_subject_dialog(self):
        text, ok = QtWidgets.QInputDialog.getText(self, "Add Subject", "Enter new subject name:")
        if ok:
            new_subject = text.strip()
            if not new_subject:
                QtWidgets.QMessageBox.warning(self, "Invalid Subject", "Subject name cannot be empty.")
                return
            if new_subject in self.subjects:
                QtWidgets.QMessageBox.information(self, "Duplicate Subject", f'"{new_subject}" is already in the list.')
                return
            self.subjects.append(new_subject)
            self.subject_entry.addItem(new_subject)
            self.subject_entry.setCurrentText(new_subject)
            self.save_subjects()

    def load_data(self):
        if not os.path.exists(self.FILE_NAME):
            with open(self.FILE_NAME, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Time", "Subject", "Notes", "XP", "Time Studied (min)"])
        sessions = []
        with open(self.FILE_NAME, "r") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                sessions.append(row)
        return sessions

    def save_data(self):
        with open(self.FILE_NAME, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Time", "Subject", "Notes", "XP", "Time Studied (min)"])
            for row in self.data:
                writer.writerow(row)

    def load_journal(self):
        entries = []
        if not os.path.exists(self.JOURNAL_FILE):
            with open(self.JOURNAL_FILE, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(["Date", "Time", "Content", "Attachments", "Title"])
        with open(self.JOURNAL_FILE, "r") as file:
            reader = csv.reader(file)
            next(reader)
            for row in reader:
                if len(row) == 5:
                    date, time, content, attachments, title = row
                else:
                    date, time, content, attachments = row
                    title = None
                attachments = attachments.split("||") if attachments else []
                entries.append(JournalEntry(date, time, content, attachments, title))
        return entries

    def save_journal(self):
        with open(self.JOURNAL_FILE, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["Date", "Time", "Content", "Attachments", "Title"])
            for entry in self.journal_entries:
                writer.writerow([entry.date, entry.time, entry.content, "||".join(entry.attachments), entry.title])

    def calculate_level(self, xp):
        level = 0
        needed = 1000
        while xp >= needed:
            xp -= needed
            level += 1
            needed = 1000 + 1000 * level
        return level, xp, needed

    def init_ui(self):
        self.tabs = QtWidgets.QTabWidget(self)
        self.tabs.setStyleSheet(f"QTabWidget::pane {{ background: {PASTEL_DARK_BG}; }} QTabBar::tab {{ background: {PASTEL_DARK_PANEL}; color: {PASTEL_TEXT}; border-radius: 8px; padding: 8px 24px; font-size: 15px; min-width: 120px; min-height: 32px; }} QTabBar::tab:selected {{ background: {PASTEL_ACCENT}; color: {PASTEL_DARK_BG}; }}")
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.tabs)
        # Study Tracker Tab
        tracker_widget = QtWidgets.QWidget()
        tracker_layout = QtWidgets.QVBoxLayout(tracker_widget)
        # XP & Level
        xp_level_layout = QtWidgets.QHBoxLayout()
        self.level_label = QtWidgets.QLabel()
        self.level_label.setFont(QtGui.QFont("Arial", 16, QtGui.QFont.Bold))
        self.xp_label = QtWidgets.QLabel()
        self.xp_label.setFont(QtGui.QFont("Arial", 14))
        xp_level_layout.addWidget(self.level_label)
        xp_level_layout.addWidget(self.xp_label)
        xp_level_layout.addStretch()
        # Add settings cog icon button (top right)
        cog_btn = QtWidgets.QPushButton()
        cog_btn.setIcon(QtGui.QIcon.fromTheme("preferences-system"))
        if cog_btn.icon().isNull():
            # fallback to unicode cog
            cog_btn.setText("\u2699")
        cog_btn.setFixedSize(36, 36)
        cog_btn.setStyleSheet(f"background: transparent; color: {PASTEL_ACCENT}; font-size: 22px;")
        cog_btn.setToolTip("Settings")
        cog_btn.clicked.connect(self.open_settings_window)
        xp_level_layout.addWidget(cog_btn)
        tracker_layout.addLayout(xp_level_layout)
        # XP Progress Bar
        self.xp_bar = QtWidgets.QProgressBar()
        self.xp_bar.setFixedHeight(28)
        self.xp_bar.setStyleSheet(f"QProgressBar {{background: {PASTEL_DARK_PANEL}; border-radius: 8px;}} QProgressBar::chunk {{background: {PASTEL_GREEN}; border-radius: 8px;}}")
        tracker_layout.addWidget(self.xp_bar)
        # Entry Form
        entry_group = QtWidgets.QGroupBox()
        entry_group.setStyleSheet(f"QGroupBox {{background: {PASTEL_DARK_PANEL}; border-radius: 8px;}}");
        entry_layout = QtWidgets.QGridLayout(entry_group)
        entry_layout.addWidget(QtWidgets.QLabel("Subject:"), 0, 0)
        self.subject_entry = QtWidgets.QComboBox()
        self.subject_entry.addItems(self.subjects)
        entry_layout.addWidget(self.subject_entry, 0, 1)
        # Add subject button
        add_subject_btn = QtWidgets.QPushButton("+")
        add_subject_btn.setFixedWidth(28)
        add_subject_btn.setStyleSheet(f"background: {PASTEL_ACCENT}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px;")
        add_subject_btn.setToolTip("Add a new subject")
        add_subject_btn.clicked.connect(self.add_subject_dialog)
        entry_layout.addWidget(add_subject_btn, 0, 2)
        entry_layout.addWidget(QtWidgets.QLabel("Notes:"), 0, 3)
        self.notes_entry = QtWidgets.QLineEdit()
        entry_layout.addWidget(self.notes_entry, 0, 4)
        entry_layout.addWidget(QtWidgets.QLabel("XP:"), 0, 5)
        self.xp_entry = QtWidgets.QLineEdit()
        self.xp_entry.setFixedWidth(60)
        entry_layout.addWidget(self.xp_entry, 0, 6)
        entry_layout.addWidget(QtWidgets.QLabel("Time Studied (min):"), 0, 7)
        self.time_entry = QtWidgets.QLineEdit()
        self.time_entry.setFixedWidth(60)
        entry_layout.addWidget(self.time_entry, 0, 8)
        log_btn = QtWidgets.QPushButton("Log Study")
        log_btn.setStyleSheet(f"background: {PASTEL_GREEN}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 16px;")
        log_btn.clicked.connect(self.log_study)
        entry_layout.addWidget(log_btn, 0, 9)
        tracker_layout.addWidget(entry_group)
        # Filter & Sort
        filter_layout = QtWidgets.QHBoxLayout()
        filter_layout.addWidget(QtWidgets.QLabel("Filter by Subject:"))
        self.filter_entry = QtWidgets.QLineEdit()
        self.filter_entry.textChanged.connect(self.refresh_log)
        filter_layout.addWidget(self.filter_entry)
        sort_btn = QtWidgets.QPushButton("Sort by Subject")
        sort_btn.setStyleSheet(f"background: {PASTEL_PURPLE}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 16px;")
        sort_btn.clicked.connect(self.sort_by_subject)
        filter_layout.addWidget(sort_btn)
        filter_layout.addStretch()
        tracker_layout.addLayout(filter_layout)
        # Log Table
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Date", "Time", "Subject", "Notes", "XP", "Time Studied (min)"])
        self.table.setStyleSheet(f"QTableWidget {{background: {PASTEL_DARK_PANEL}; color: {PASTEL_TEXT}; border-radius: 8px;}} QHeaderView::section {{background: {PASTEL_ACCENT}; color: {PASTEL_DARK_BG}; font-weight: bold;}}")
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.doubleClicked.connect(self.enlarge_notes)
        tracker_layout.addWidget(self.table)
        # Delete Button
        del_btn = QtWidgets.QPushButton("Delete Selected")
        del_btn.setStyleSheet(f"background: {PASTEL_RED}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 16px;")
        del_btn.clicked.connect(self.delete_selected)
        tracker_layout.addWidget(del_btn)
        # Graph Button
        graph_btn = QtWidgets.QPushButton("Show Study Time Graph")
        graph_btn.setStyleSheet(f"background: {PASTEL_YELLOW}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 16px;")
        graph_btn.clicked.connect(self.show_graph)
        tracker_layout.addWidget(graph_btn)
        self.tabs.addTab(tracker_widget, "Study Tracker")
        # Journal Tab
        journal_widget = QtWidgets.QWidget()
        journal_layout = QtWidgets.QVBoxLayout(journal_widget)
        # Calendar Tree View for Journal
        self.journal_tree = QtWidgets.QTreeWidget()
        self.journal_tree.setHeaderHidden(True)
        self.journal_tree.setStyleSheet(
            f"""
            QTreeWidget {{background: {PASTEL_DARK_PANEL}; color: {PASTEL_TEXT}; border-radius: 8px; font-size: 15px;}}
            QTreeWidget::item {{ border: 1px solid {PASTEL_OUTLINE}; border-radius: 6px; margin: 4px; padding: 6px; }}
            QTreeWidget::item:selected {{ background: {PASTEL_ACCENT}; color: {PASTEL_DARK_BG}; border: 2px solid {PASTEL_OUTLINE}; }}
            """
        )
        self.journal_tree.itemSelectionChanged.connect(self.display_journal_entry)
        journal_layout.addWidget(self.journal_tree, 2)
        # Rich Text Editor + Toolbar
        editor_layout = QtWidgets.QVBoxLayout()
        self.journal_toolbar = QtWidgets.QToolBar()
        self.journal_toolbar.setStyleSheet(f"QToolBar {{background: {PASTEL_DARK_PANEL}; border-radius: 8px;}} QToolButton {{font-size: 15px; min-width: 32px; min-height: 32px; padding: 4px 10px;}}")
        # Toolbar actions
        bold_action = QtWidgets.QAction("Bold", self)
        bold_action.setShortcut("Ctrl+B")
        bold_action.triggered.connect(lambda: self.journal_editor.setFontWeight(QtGui.QFont.Bold if self.journal_editor.fontWeight() != QtGui.QFont.Bold else QtGui.QFont.Normal))
        italic_action = QtWidgets.QAction("Italic", self)
        italic_action.setShortcut("Ctrl+I")
        italic_action.triggered.connect(lambda: self.journal_editor.setFontItalic(not self.journal_editor.fontItalic()))
        underline_action = QtWidgets.QAction("Underline", self)
        underline_action.setShortcut("Ctrl+U")
        underline_action.triggered.connect(lambda: self.journal_editor.setFontUnderline(not self.journal_editor.fontUnderline()))
        checklist_action = QtWidgets.QAction("Checklist", self)
        checklist_action.setToolTip("Insert Checklist Item")
        checklist_action.triggered.connect(self.insert_checklist_item)
        font_box = QtWidgets.QFontComboBox()
        font_box.setCurrentFont(QtGui.QFont("Arial"))
        font_box.currentFontChanged.connect(lambda f: self.journal_editor.setCurrentFont(f))
        size_box = QtWidgets.QComboBox()
        for s in [10, 12, 14, 16, 18, 20, 24, 28]:
            size_box.addItem(str(s))
        size_box.setCurrentText("15")
        size_box.currentTextChanged.connect(lambda s: self.journal_editor.setFontPointSize(int(s)))
        self.journal_toolbar.addAction(bold_action)
        self.journal_toolbar.addAction(italic_action)
        self.journal_toolbar.addAction(underline_action)
        self.journal_toolbar.addAction(checklist_action)
        self.journal_toolbar.addWidget(font_box)
        self.journal_toolbar.addWidget(size_box)
        editor_layout.addWidget(self.journal_toolbar)
        self.journal_editor = QtWidgets.QTextEdit()
        self.journal_editor.setStyleSheet(f"background: {PASTEL_DARK_BG}; color: {PASTEL_TEXT}; border-radius: 8px; font-size: 15px;")
        self.journal_editor.setFont(QtGui.QFont("Arial", 15))
        editor_layout.addWidget(self.journal_editor)
        journal_layout.addLayout(editor_layout, 5)
        # Attachments
        attach_layout = QtWidgets.QHBoxLayout()
        self.attach_btn = QtWidgets.QPushButton("Add Attachment")
        self.attach_btn.setStyleSheet(f"background: {PASTEL_ACCENT}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 16px; font-size: 15px;")
        self.attach_btn.clicked.connect(self.add_attachment)
        attach_layout.addWidget(self.attach_btn)
        self.attachment_label = QtWidgets.QLabel("")
        self.attachment_label.setStyleSheet(f"color: {PASTEL_GREEN}; font-size: 13px;")
        attach_layout.addWidget(self.attachment_label)
        attach_layout.addStretch()
        journal_layout.addLayout(attach_layout)
        # Save/Add/Delete/Rename Entry Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        save_journal_btn = QtWidgets.QPushButton("Add Journal Entry")
        save_journal_btn.setStyleSheet(f"background: {PASTEL_GREEN}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 16px; font-size: 15px;")
        save_journal_btn.clicked.connect(self.add_journal_entry)
        btn_layout.addWidget(save_journal_btn)
        del_journal_btn = QtWidgets.QPushButton("Delete Entry")
        del_journal_btn.setStyleSheet(f"background: {PASTEL_RED}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 16px; font-size: 15px;")
        del_journal_btn.clicked.connect(self.delete_journal_entry)
        btn_layout.addWidget(del_journal_btn)
        rename_journal_btn = QtWidgets.QPushButton("Rename Entry")
        rename_journal_btn.setStyleSheet(f"background: {PASTEL_PURPLE}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 16px; font-size: 15px;")
        rename_journal_btn.clicked.connect(self.rename_journal_entry)
        btn_layout.addWidget(rename_journal_btn)
        btn_layout.addStretch()
        journal_layout.addLayout(btn_layout)
        self.tabs.addTab(journal_widget, "Journal")
        # Break Timer Tab
        break_widget = QtWidgets.QWidget()
        break_layout = QtWidgets.QVBoxLayout(break_widget)
        break_layout.setAlignment(QtCore.Qt.AlignTop)
        # Title label above group
        timer_title = QtWidgets.QLabel("Break Timer")
        timer_title.setFont(QtGui.QFont("Arial", 22, QtGui.QFont.Bold))
        timer_title.setStyleSheet(f"color: {PASTEL_ACCENT}; margin-bottom: 8px;")
        timer_title.setAlignment(QtCore.Qt.AlignCenter)
        break_layout.addWidget(timer_title)
        timer_group = QtWidgets.QGroupBox()
        timer_group.setStyleSheet(f"QGroupBox {{background: {PASTEL_DARK_PANEL}; border-radius: 8px; font-size: 18px; color: {PASTEL_TEXT}; margin-top: 0px;}}")
        timer_layout = QtWidgets.QGridLayout(timer_group)
        # Time input row (minutes and seconds)
        timer_layout.addWidget(QtWidgets.QLabel("Set break duration:"), 0, 0)
        time_input_layout = QtWidgets.QHBoxLayout()
        self.break_minutes = QtWidgets.QSpinBox()
        self.break_minutes.setRange(0, 180)
        self.break_minutes.setValue(5)
        self.break_minutes.setStyleSheet(f"background: {PASTEL_DARK_BG}; color: {PASTEL_TEXT}; font-size: 16px;")
        time_input_layout.addWidget(self.break_minutes)
        time_input_layout.addWidget(QtWidgets.QLabel("min"))
        self.break_seconds = QtWidgets.QSpinBox()
        self.break_seconds.setRange(0, 59)
        self.break_seconds.setValue(0)
        self.break_seconds.setStyleSheet(f"background: {PASTEL_DARK_BG}; color: {PASTEL_TEXT}; font-size: 16px;")
        time_input_layout.addWidget(self.break_seconds)
        time_input_layout.addWidget(QtWidgets.QLabel("sec"))
        time_input_layout.addStretch()
        timer_layout.addLayout(time_input_layout, 0, 1)
        # Timer display
        self.timer_label = QtWidgets.QLabel("00:00")
        self.timer_label.setFont(QtGui.QFont("Arial", 36, QtGui.QFont.Bold))
        self.timer_label.setAlignment(QtCore.Qt.AlignCenter)
        self.timer_label.setStyleSheet(f"color: {PASTEL_ACCENT};")
        timer_layout.addWidget(self.timer_label, 1, 0, 1, 2)
        # Start/Stop/Reset buttons
        btn_layout = QtWidgets.QHBoxLayout()
        self.start_btn = QtWidgets.QPushButton("Start")
        self.start_btn.setStyleSheet(f"background: {PASTEL_GREEN}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 24px; font-size: 16px;")
        self.start_btn.clicked.connect(self.start_break_timer)
        btn_layout.addWidget(self.start_btn)
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.stop_btn.setStyleSheet(f"background: {PASTEL_RED}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 24px; font-size: 16px;")
        self.stop_btn.clicked.connect(self.stop_break_timer)
        btn_layout.addWidget(self.stop_btn)
        self.reset_btn = QtWidgets.QPushButton("Reset")
        self.reset_btn.setStyleSheet(f"background: {PASTEL_PURPLE}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; padding: 6px 24px; font-size: 16px;")
        self.reset_btn.clicked.connect(self.reset_break_timer)
        btn_layout.addWidget(self.reset_btn)
        timer_layout.addLayout(btn_layout, 2, 0, 1, 2)
        # Alarm sound selection
        alarm_layout = QtWidgets.QHBoxLayout()
        alarm_layout.addWidget(QtWidgets.QLabel("Alarm Sound:"))
        self.alarm_path = self.get_alarm_path()
        alarm_basename = os.path.basename(self.alarm_path) if self.alarm_path else "(System Beep)"
        self.alarm_label = QtWidgets.QLabel(alarm_basename)
        self.alarm_label.setStyleSheet(f"color: {PASTEL_GREEN}; font-size: 15px;")
        alarm_layout.addWidget(self.alarm_label)
        choose_alarm_btn = QtWidgets.QPushButton("Choose Sound")
        choose_alarm_btn.setStyleSheet(f"background: {PASTEL_ACCENT}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; font-size: 15px;")
        choose_alarm_btn.clicked.connect(self.choose_alarm_sound)
        alarm_layout.addWidget(choose_alarm_btn)
        alarm_layout.addStretch()
        timer_layout.addLayout(alarm_layout, 3, 0, 1, 2)
        break_layout.addWidget(timer_group)
        self.tabs.addTab(break_widget, "Break Timer")
        # Timer logic
        self.break_timer = QtCore.QTimer(self)
        self.break_timer.timeout.connect(self.update_break_timer)
        self.break_time_left = 0
        self.break_alarm_player = None
        self.setLayout(main_layout)
        self.update_xp_display()
        self.current_attachments = []

        self.menu_bar = QtWidgets.QMenuBar(self)
        settings_menu = self.menu_bar.addMenu("Settings")
        change_folder_action = QtWidgets.QAction("Change Data Folder...", self)
        change_folder_action.triggered.connect(self.change_data_dir)
        settings_menu.addAction(change_folder_action)

    def get_alarm_path(self):
        # Default alarm sound (bundled with app or fallback to system beep)
        config = load_config() or {}
        alarm_path = config.get("alarm_sound")
        if alarm_path and os.path.exists(alarm_path):
            return alarm_path
        # Try to use a default sound in the app directory
        default_path = os.path.join(os.path.dirname(__file__), "default_alarm.wav")
        if os.path.exists(default_path):
            return default_path
        return None  # Will use system beep if not found

    def choose_alarm_sound(self):
        file, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose Alarm Sound", self.data_dir, "Audio Files (*.wav *.mp3 *.ogg)")
        if file:
            self.alarm_path = file
            self.alarm_label.setText(os.path.basename(file))
            config = load_config() or {}
            config["alarm_sound"] = file
            save_config(config)

    def start_break_timer(self):
        self.break_time_left = self.break_minutes.value() * 60 + self.break_seconds.value()
        self.update_break_timer_label()
        self.break_timer.start(1000)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.reset_btn.setEnabled(True)

    def stop_break_timer(self):
        self.break_timer.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.reset_btn.setEnabled(True)
        # Stop alarm if playing
        if self.break_alarm_player:
            self.break_alarm_player.stop()
        if hasattr(self, 'alarm_loop_timer') and self.alarm_loop_timer:
            self.alarm_loop_timer.stop()
            self.alarm_loop_timer = None

    def reset_break_timer(self):
        self.break_timer.stop()
        self.break_time_left = self.break_minutes.value() * 60 + self.break_seconds.value()
        self.update_break_timer_label()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.reset_btn.setEnabled(True)
        # Stop alarm if playing
        if self.break_alarm_player:
            self.break_alarm_player.stop()
        if hasattr(self, 'alarm_loop_timer') and self.alarm_loop_timer:
            self.alarm_loop_timer.stop()
            self.alarm_loop_timer = None

    def update_break_timer(self):
        if self.break_time_left > 0:
            self.break_time_left -= 1
            self.update_break_timer_label()
        else:
            self.break_timer.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.reset_btn.setEnabled(True)
            self.play_alarm_sound()

    def update_break_timer_label(self):
        mins = self.break_time_left // 60
        secs = self.break_time_left % 60
        self.timer_label.setText(f"{mins:02d}:{secs:02d}")

    def play_alarm_sound(self):
        # Stop any previous alarm
        if hasattr(self, 'alarm_loop_timer') and self.alarm_loop_timer:
            self.alarm_loop_timer.stop()
            self.alarm_loop_timer = None
        if self.break_alarm_player:
            self.break_alarm_player.stop()
        if self.alarm_path and os.path.exists(self.alarm_path):
            self.break_alarm_player = QtMultimedia.QMediaPlayer()
            url = QtCore.QUrl.fromLocalFile(self.alarm_path)
            content = QtMultimedia.QMediaContent(url)
            self.break_alarm_player.setMedia(content)
            self.break_alarm_player.setVolume(100)
            self.break_alarm_player.play()
            # Use a QTimer to repeat the sound every 0.5 seconds
            self.alarm_loop_timer = QtCore.QTimer(self)
            self.alarm_loop_timer.timeout.connect(self._replay_alarm_sound)
            self.alarm_loop_timer.start(500)
        else:
            QtWidgets.QApplication.beep()
            self.alarm_loop_timer = None

    def _replay_alarm_sound(self):
        if self.break_alarm_player:
            self.break_alarm_player.stop()
            self.break_alarm_player.play()

    def log_study(self):
        subject = self.subject_entry.currentText()
        notes = self.notes_entry.text().strip()
        try:
            xp = int(self.xp_entry.text())
            time_studied = int(self.time_entry.text())
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Invalid Input", "XP and Time Studied must be numbers.")
            return
        if not subject:
            QtWidgets.QMessageBox.warning(self, "Missing Subject", "Please enter a subject.")
            return
        now = datetime.now()
        session = [
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M"),
            subject,
            notes,
            str(xp),
            str(time_studied)
        ]
        self.data.append(session)
        self.save_data()
        self.subject_entry.setCurrentIndex(0)
        self.notes_entry.clear()
        self.xp_entry.clear()
        self.time_entry.clear()
        self.update_xp_display()
        self.refresh_log()

    def refresh_log(self):
        filter_text = self.filter_entry.text().lower()
        self.table.setRowCount(0)
        for session in self.data:
            if filter_text in session[2].lower():
                row_pos = self.table.rowCount()
                self.table.insertRow(row_pos)
                for i, value in enumerate(session):
                    item = QtWidgets.QTableWidgetItem(value)
                    item.setForeground(QtGui.QColor(PASTEL_TEXT))
                    self.table.setItem(row_pos, i, item)
        self.update_xp_display()

    def update_xp_display(self):
        total_xp = sum(int(row[4]) for row in self.data)
        level, xp_in_level, required = self.calculate_level(total_xp)
        self.level_label.setText(f"Level: {level}")
        self.xp_label.setText(f"XP: {xp_in_level} / {required}")
        self.xp_bar.setMaximum(required)
        self.xp_bar.setValue(xp_in_level)

    def sort_by_subject(self):
        self.data.sort(key=lambda x: x[2].lower())
        self.refresh_log()

    def delete_selected(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return
        rows_to_delete = sorted([s.row() for s in selected], reverse=True)
        for row in rows_to_delete:
            del self.data[row]
        self.save_data()
        self.refresh_log()

    def enlarge_notes(self, index):
        row = index.row()
        session = self.data[row]
        notes = session[3]
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle(f"Notes for {session[2]} ({session[0]} {session[1]})")
        dlg.setStyleSheet(f"background: {PASTEL_DARK_BG}; color: {PASTEL_TEXT};")
        layout = QtWidgets.QVBoxLayout(dlg)
        notes_edit = QtWidgets.QTextEdit()
        notes_edit.setText(notes)
        notes_edit.setReadOnly(True)
        notes_edit.setFont(QtGui.QFont("Arial", 14))
        layout.addWidget(notes_edit)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.resize(600, 300)
        dlg.exec_()

    def show_graph(self):
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            QtWidgets.QMessageBox.warning(self, "Missing Library", "matplotlib is required for the graph. Please install it with 'pip install matplotlib'.")
            return
        from collections import defaultdict
        date_to_time = defaultdict(int)
        for session in self.data:
            date = session[0]
            try:
                mins = int(session[5])
            except Exception:
                mins = 0
            date_to_time[date] += mins
        if not date_to_time:
            QtWidgets.QMessageBox.information(self, "No Data", "No study sessions to plot.")
            return
        dates = sorted(date_to_time.keys())
        times = [date_to_time[d] for d in dates]
        plt.figure(figsize=(8,4))
        plt.plot(dates, times, marker='o', color=PASTEL_GREEN)
        plt.title('Time Studied per Day')
        plt.xlabel('Date')
        plt.ylabel('Time Studied (min)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()

    # --- Journal Methods ---
    def refresh_journal_list(self):
        self.journal_tree.clear()
        # Group entries by year > month > day
        groups = {}
        for idx, entry in enumerate(self.journal_entries):
            y, m, d = entry.date.split("-")
            groups.setdefault(y, {}).setdefault(m, {}).setdefault(d, []).append((idx, entry))
        for y in sorted(groups.keys(), reverse=True):
            y_item = QtWidgets.QTreeWidgetItem([y])
            self.journal_tree.addTopLevelItem(y_item)
            for m in sorted(groups[y].keys(), reverse=True):
                m_item = QtWidgets.QTreeWidgetItem([datetime.strptime(m, "%m").strftime("%B")])
                y_item.addChild(m_item)
                for d in sorted(groups[y][m].keys(), reverse=True):
                    d_item = QtWidgets.QTreeWidgetItem([d])
                    m_item.addChild(d_item)
                    for idx, entry in groups[y][m][d]:
                        e_item = QtWidgets.QTreeWidgetItem([entry.title])
                        e_item.setData(0, QtCore.Qt.UserRole, idx)
                        d_item.addChild(e_item)
        self.journal_tree.expandToDepth(2)

    def display_journal_entry(self):
        selected = self.journal_tree.selectedItems()
        if not selected:
            self.journal_editor.clear()
            self.attachment_label.setText("")
            self.current_attachments = []
            return
        item = selected[0]
        # Only leaf nodes (entries) have UserRole data
        idx = item.data(0, QtCore.Qt.UserRole)
        if idx is None:
            self.journal_editor.clear()
            self.attachment_label.setText("")
            self.current_attachments = []
            return
        entry = self.journal_entries[idx]
        self.journal_editor.setHtml(entry.content)
        if entry.attachments:
            links = []
            for path in entry.attachments:
                name = os.path.basename(path)
                links.append(f'<a href="file://{path}">{name}</a>')
            self.attachment_label.setText("Attachments: " + " | ".join(links))
        else:
            self.attachment_label.setText("")
        self.current_attachments = entry.attachments[:]

    def add_journal_entry(self):
        content = self.journal_editor.toHtml()
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M")
        attachments = self.current_attachments[:]
        entry = JournalEntry(date, time, content, attachments)
        self.journal_entries.append(entry)
        self.save_journal()
        self.refresh_journal_list()
        self.journal_editor.clear()
        self.attachment_label.setText("")
        self.current_attachments = []

    def delete_journal_entry(self):
        selected = self.journal_tree.selectedItems()
        if not selected:
            return
        item = selected[0]
        idx = item.data(0, QtCore.Qt.UserRole)
        if idx is not None and 0 <= idx < len(self.journal_entries):
            del self.journal_entries[idx]
            self.save_journal()
            self.refresh_journal_list()
            self.journal_editor.clear()
            self.attachment_label.setText("")
            self.current_attachments = []

    def rename_journal_entry(self):
        selected = self.journal_tree.selectedItems()
        if not selected:
            return
        item = selected[0]
        idx = item.data(0, QtCore.Qt.UserRole)
        if idx is not None and 0 <= idx < len(self.journal_entries):
            new_title, ok = QtWidgets.QInputDialog.getText(self, "Rename Entry", "New title:", text=self.journal_entries[idx].title)
            if ok and new_title.strip():
                self.journal_entries[idx].title = new_title.strip()
                self.save_journal()
                self.refresh_journal_list()

    def add_attachment(self):
        files, _ = QtWidgets.QFileDialog.getOpenFileNames(self, "Select Attachments")
        if files:
            self.current_attachments.extend(files)
            links = []
            for path in self.current_attachments:
                name = os.path.basename(path)
                links.append(f'<a href="file://{path}">{name}</a>')
            self.attachment_label.setText("Attachments: " + " | ".join(links))

    def insert_checklist_item(self):
        cursor = self.journal_editor.textCursor()
        cursor.insertHtml('<span style="font-size:18px;">&#x2610;</span> ')
        self.journal_editor.setTextCursor(cursor)

    def open_settings_window(self):
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Settings")
        dlg.setStyleSheet(f"background: {PASTEL_DARK_BG}; color: {PASTEL_TEXT};")
        layout = QtWidgets.QVBoxLayout(dlg)
        # Data folder section
        folder_group = QtWidgets.QGroupBox()
        folder_group.setTitle("")
        folder_group.setStyleSheet(f"QGroupBox {{background: {PASTEL_DARK_PANEL}; border-radius: 8px; margin-top: 12px; border: none;}}")
        folder_layout = QtWidgets.QGridLayout(folder_group)
        folder_label_lbl = QtWidgets.QLabel("Data Folder:")
        folder_label_lbl.setStyleSheet(f"color: {PASTEL_TEXT}; font-size: 15px; padding-right: 8px;")
        folder_layout.addWidget(folder_label_lbl, 0, 0, QtCore.Qt.AlignLeft)
        folder_label = QtWidgets.QLineEdit(self.data_dir)
        folder_label.setReadOnly(True)
        folder_label.setStyleSheet(f"background: {PASTEL_DARK_BG}; color: {PASTEL_GREEN}; font-size: 15px; border: none; padding: 6px 8px; border-radius: 6px;")
        folder_layout.addWidget(folder_label, 0, 1)
        change_btn = QtWidgets.QPushButton("Change...")
        change_btn.setStyleSheet(f"background: {PASTEL_ACCENT}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; font-size: 15px; padding: 6px 16px;")
        def change_folder():
            folder = QtWidgets.QFileDialog.getExistingDirectory(self, "Select New Data Folder", self.data_dir)
            if folder:
                save_config({"data_dir": folder})
                folder_label.setText(folder)
                QtWidgets.QMessageBox.information(self, "Restart Required", "Please restart the app to use the new data folder.")
        change_btn.clicked.connect(change_folder)
        folder_layout.addWidget(change_btn, 0, 2)
        layout.addWidget(folder_group)
        # Alarm sound section
        alarm_group = QtWidgets.QGroupBox()
        alarm_group.setTitle("")
        alarm_group.setStyleSheet(f"QGroupBox {{background: {PASTEL_DARK_PANEL}; border-radius: 8px; margin-top: 12px; border: none;}}")
        alarm_layout = QtWidgets.QGridLayout(alarm_group)
        alarm_label_lbl = QtWidgets.QLabel("Break Timer Alarm Sound:")
        alarm_label_lbl.setStyleSheet(f"color: {PASTEL_TEXT}; font-size: 15px; padding-right: 8px;")
        alarm_layout.addWidget(alarm_label_lbl, 0, 0, QtCore.Qt.AlignLeft)
        alarm_basename = os.path.basename(self.alarm_path) if self.alarm_path else "(System Beep)"
        alarm_label = QtWidgets.QLineEdit(alarm_basename)
        alarm_label.setReadOnly(True)
        alarm_label.setStyleSheet(f"background: {PASTEL_DARK_BG}; color: {PASTEL_GREEN}; font-size: 15px; border: none; padding: 6px 8px; border-radius: 6px;")
        alarm_layout.addWidget(alarm_label, 0, 1)
        choose_alarm_btn = QtWidgets.QPushButton("Choose Sound")
        choose_alarm_btn.setStyleSheet(f"background: {PASTEL_ACCENT}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; font-size: 15px; padding: 6px 16px;")
        def choose_alarm():
            file, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Choose Alarm Sound", self.data_dir, "Audio Files (*.wav *.mp3 *.ogg)")
            if file:
                self.alarm_path = file
                alarm_label.setText(os.path.basename(file))
                config = load_config() or {}
                config["alarm_sound"] = file
                save_config(config)
        choose_alarm_btn.clicked.connect(choose_alarm)
        alarm_layout.addWidget(choose_alarm_btn, 0, 2)
        layout.addWidget(alarm_group)
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.setStyleSheet(f"background: {PASTEL_PURPLE}; color: {PASTEL_DARK_BG}; font-weight: bold; border-radius: 6px; font-size: 15px; padding: 6px 24px;")
        close_btn.setFixedWidth(120)
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=QtCore.Qt.AlignRight)
        dlg.setLayout(layout)
        dlg.setMinimumWidth(480)
        dlg.exec_()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = StudyTrackerApp()
    window.show()
    sys.exit(app.exec_())
