from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QRadioButton, QButtonGroup,
    QTreeWidget, QTreeWidgetItem, QDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt6.QtGui import QColor, QDesktopServices

import os
from collections import defaultdict

from scanner.temp_scanner import scan_temp
from scanner.deep_scanner import scan_directory
from cleaner.remover import remove_path
from core.scan_modes import ScanMode


APP_NAME = "Echo Deep Cleaner"
APP_VERSION = "1.0.1"
SITE_URL = "https://echotechnology-dev.github.io/"


BTN_STYLE = """
QPushButton {
    background-color: #2563eb;
    color: white;
    font-size: 12px;
    font-weight: 500;
    border-radius: 8px;
    padding: 6px 12px;
}
QPushButton:hover { background-color: #1d4ed8; }
QPushButton:pressed { background-color: #1e40af; }
QPushButton:disabled { background-color: #9ca3af; }
"""


# ================= REPORT =================

class ReportDialog(QDialog):
    def __init__(self, summary_lines, removed, skipped):
        super().__init__()
        self.setWindowTitle("Cleanup completed")
        self.setFixedSize(420, 320)

        layout = QVBoxLayout()

        title = QLabel("Cleanup completed")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:16px;font-weight:600;")

        summary = QLabel("\n".join(summary_lines))
        summary.setWordWrap(True)
        summary.setStyleSheet("font-size:12px;")

        totals = QLabel(
            f"\nRemoved: {removed} items\n"
            f"Skipped: {skipped} items"
        )
        totals.setAlignment(Qt.AlignmentFlag.AlignCenter)
        totals.setStyleSheet("font-size:12px;font-weight:500;")

        note = QLabel("Some files may be locked or in use.")
        note.setAlignment(Qt.AlignmentFlag.AlignCenter)
        note.setStyleSheet("color:#777;font-size:11px;")

        ok_btn = QPushButton("OK")
        ok_btn.setFixedSize(100, 34)
        ok_btn.setStyleSheet(BTN_STYLE)
        ok_btn.clicked.connect(self.accept)

        layout.addWidget(title)
        layout.addWidget(summary)
        layout.addWidget(totals)
        layout.addWidget(note)
        layout.addStretch()
        layout.addWidget(ok_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)


# ================= ABOUT =================

class AboutDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("About")
        self.setFixedSize(480, 300)

        layout = QVBoxLayout()

        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:20px;font-weight:600;")

        version = QLabel(f"Version {APP_VERSION}")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet("color:#888;font-size:11px;")

        desc = QLabel(
            "Free Windows utility by Echo Technology.\n\n"
            "Safe & Deep scan modes.\n"
            "Deep mode may remove application data.\n\n"
            "No telemetry • Offline only"
        )
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)

        site_btn = QPushButton("🌐 Echo Technology Website")
        site_btn.setFixedSize(220, 36)
        site_btn.setStyleSheet(BTN_STYLE)
        site_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(SITE_URL))
        )

        layout.addWidget(title)
        layout.addWidget(version)
        layout.addWidget(desc)
        layout.addStretch()
        layout.addWidget(site_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)


# ================= SCAN WORKER =================

class ScanWorker(QThread):
    folder_found = pyqtSignal(dict)
    status = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, mode):
        super().__init__()
        self.mode = mode

    def run(self):
        groups = defaultdict(list)

        self.status.emit("Scanning TEMP...")
        for item in scan_temp():
            groups[os.path.dirname(item["path"])].append(item)

        if self.mode == ScanMode.DEEP:
            self.status.emit("Scanning user data (Deep mode)...")
            for base in (
                os.getenv("LOCALAPPDATA"),
                os.getenv("APPDATA"),
                os.getenv("PROGRAMDATA")
            ):
                if not base:
                    continue
                for item in scan_directory(base):
                    groups[os.path.dirname(item["path"])].append(item)

        for folder, files in groups.items():
            self.folder_found.emit({
                "folder": folder,
                "files": files,
                "size": round(sum(f["size"] for f in files), 2),
                "count": len(files),
                "risk": "Safe" if self.mode == ScanMode.SAFE else "Review"
            })

        self.finished.emit()


# ================= MAIN WINDOW =================

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1120, 760)

        self.worker = None
        self.scan_done = False

        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout()

        title = QLabel(APP_NAME)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:24px;font-weight:600;")

        subtitle = QLabel("Safe & Advanced cleanup tool")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color:#6b7280;font-size:12px;")

        main.addWidget(title)
        main.addWidget(subtitle)

        # Modes
        mode_layout = QHBoxLayout()
        self.safe_rb = QRadioButton("🟢 Safe")
        self.deep_rb = QRadioButton("🔵 Deep (Advanced)")
        self.safe_rb.setChecked(True)

        group = QButtonGroup()
        group.addButton(self.safe_rb)
        group.addButton(self.deep_rb)

        mode_layout.addWidget(self.safe_rb)
        mode_layout.addWidget(self.deep_rb)
        mode_layout.addStretch()
        main.addLayout(mode_layout)

        # Deep warning
        self.deep_warning = QLabel(
            "⚠️ Deep mode may remove application data.\n"
            "Review items carefully before deleting."
        )
        self.deep_warning.setStyleSheet(
            "color:#b45309;font-size:11px;"
        )
        self.deep_warning.setVisible(False)
        main.addWidget(self.deep_warning)

        self.deep_rb.toggled.connect(
            lambda v: self.deep_warning.setVisible(v)
        )

        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(
            ["Name", "Path", "Size (MB)", "Count", "Risk"]
        )
        self.tree.setColumnWidth(0, 260)
        self.tree.setColumnWidth(1, 420)
        self.tree.setColumnWidth(2, 110)
        self.tree.setColumnWidth(3, 80)
        self.tree.setColumnWidth(4, 80)
        self.tree.setSortingEnabled(True)
        self.tree.sortByColumn(2, Qt.SortOrder.DescendingOrder)
        self.tree.itemExpanded.connect(self.lazy_load)

        main.addWidget(self.tree)

        # Buttons
        btns = QHBoxLayout()

        self.about_btn = QPushButton("About")
        self.select_all_btn = QPushButton("Select all")
        self.unselect_all_btn = QPushButton("Unselect all")
        self.scan_btn = QPushButton("Start scan")
        self.clean_btn = QPushButton("Remove checked")

        for b in (
            self.about_btn,
            self.select_all_btn,
            self.unselect_all_btn,
            self.scan_btn,
            self.clean_btn
        ):
            b.setFixedSize(160, 38)
            b.setStyleSheet(BTN_STYLE)

        btns.addWidget(self.about_btn)
        btns.addWidget(self.select_all_btn)
        btns.addWidget(self.unselect_all_btn)
        btns.addStretch()
        btns.addWidget(self.scan_btn)
        btns.addWidget(self.clean_btn)

        main.addLayout(btns)

        self.status = QLabel("Ready")
        self.status.setStyleSheet("color:#6b7280;font-size:11px;")
        main.addWidget(self.status)

        central.setLayout(main)

        # Signals
        self.about_btn.clicked.connect(lambda: AboutDialog().exec())
        self.scan_btn.clicked.connect(self.start_scan)
        self.clean_btn.clicked.connect(self.clean_checked)
        self.select_all_btn.clicked.connect(self.select_all)
        self.unselect_all_btn.clicked.connect(self.unselect_all)

    # ---------- SCAN ----------
    def start_scan(self):
        if self.scan_done:
            self.status.setText("Please clean results before running another scan.")
            return

        self.tree.clear()
        mode = ScanMode.SAFE if self.safe_rb.isChecked() else ScanMode.DEEP

        self.status.setText("Starting scan...")
        self.scan_btn.setEnabled(False)

        self.worker = ScanWorker(mode)
        self.worker.folder_found.connect(self.add_folder)
        self.worker.status.connect(self.status.setText)
        self.worker.finished.connect(self.finish_scan)
        self.worker.start()

    def finish_scan(self):
        self.scan_done = True
        self.scan_btn.setEnabled(True)
        self.status.setText("Scan completed. Review results before cleaning.")

    # ---------- TREE ----------
    def add_folder(self, data):
        item = QTreeWidgetItem(self.tree)
        item.setText(0, os.path.basename(data["folder"]) or data["folder"])
        item.setText(1, data["folder"])
        item.setText(2, str(data["size"]))
        item.setText(3, str(data["count"]))
        item.setText(4, data["risk"])
        item.setCheckState(0, Qt.CheckState.Unchecked)

        item.setData(0, Qt.ItemDataRole.UserRole, data["files"])
        item.setChildIndicatorPolicy(QTreeWidgetItem.ChildIndicatorPolicy.ShowIndicator)

        item.setForeground(
            4, QColor("#16a34a") if data["risk"] == "Safe" else QColor("#d97706")
        )

    def lazy_load(self, item):
        if item.childCount() > 0:
            return

        files = item.data(0, Qt.ItemDataRole.UserRole)
        if not files:
            return

        for f in files:
            child = QTreeWidgetItem(item)
            child.setText(0, os.path.basename(f["path"]))
            child.setText(1, f["path"])
            child.setText(2, str(f["size"]))
            child.setCheckState(0, Qt.CheckState.Unchecked)

    # ---------- CLEAN ----------
    def clean_checked(self):
        if self.deep_rb.isChecked():
            reply = QMessageBox.warning(
                self,
                "Deep Cleanup Warning",
                "Deep cleanup may remove application data\n"
                "and affect installed programs.\n\n"
                "Delete selected items anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel
            )
            if reply != QMessageBox.StandardButton.Yes:
                self.status.setText("Cleanup cancelled.")
                return

        removed = 0
        skipped = 0
        folder_stats = {}

        root = self.tree.invisibleRootItem()

        for i in range(root.childCount()):
            folder = root.child(i)
            path = folder.text(1)
            size = float(folder.text(2))
            count = int(folder.text(3))

            folder_stats[path] = {
                "files": count,
                "size": size,
                "cleaned": False
            }

            if folder.checkState(0) == Qt.CheckState.Checked:
                ok, _ = remove_path(path)
                if ok:
                    removed += count
                    folder_stats[path]["cleaned"] = True
                else:
                    skipped += 1
                continue

            for j in range(folder.childCount()):
                file = folder.child(j)
                if file.checkState(0) == Qt.CheckState.Checked:
                    ok, _ = remove_path(file.text(1))
                    if ok:
                        removed += 1
                        folder_stats[path]["cleaned"] = True
                    else:
                        skipped += 1

        summary = ["Top cleaned locations:\n"]
        top = sorted(
            folder_stats.items(),
            key=lambda x: x[1]["size"],
            reverse=True
        )[:5]

        for path, info in top:
            mark = "✓" if info["cleaned"] else "–"
            summary.append(
                f"▸ {path}\n"
                f"  {info['files']} files | {info['size']} MB   {mark}\n"
            )

        ReportDialog(summary, removed, skipped).exec()

        self.tree.clear()
        self.scan_done = False
        self.status.setText("Cleanup finished. You can scan again.")

    # ---------- SELECT ----------
    def select_all(self):
        if self.deep_rb.isChecked():
            reply = QMessageBox.warning(
                self,
                "Select All in Deep Mode",
                "Selecting all items in Deep mode\n"
                "may remove application data.\n\n"
                "Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            root.child(i).setCheckState(0, Qt.CheckState.Checked)

    def unselect_all(self):
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            root.child(i).setCheckState(0, Qt.CheckState.Unchecked)
