# Student Name: Nakeetha Thissera
# Student ID: w23048939


from datetime import date, timedelta
import sys

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
)
from PySide6.QtCore import Signal


class Person:
    def __init__(self, name: str, prison_id: str):
        self.name = name
        self.prison_id = prison_id

    def get_basic_info(self):
        return f"Name: {self.name}, Prison ID: {self.prison_id}"


class Licensee(Person):
    def __init__(
        self,
        name: str,
        prison_id: str,
        release_date: date,
        licence_conditions=None,
        required_matching_attributes=None,
        health_and_misc_notes="",
    ):
        super().__init__(name, prison_id)
        self.status = "Pending"  # Pending / Allocated / Exited
        self.licence_conditions = licence_conditions or []
        self.required_matching_attributes = required_matching_attributes or []
        self.health_and_misc_notes = health_and_misc_notes
        self.release_date = release_date

    def change_status(self, new_status: str):
        self.status = new_status

    def calculate_time_remaining(self):
        return (self.release_date - date.today()).days

    def update_notes(self, notes: str):
        self.health_and_misc_notes = notes

    def __str__(self):
        return f"{self.name} ({self.prison_id}) - {self.status}"


class RHU:
    def __init__(
        self,
        name: str,
        capacity: int,
        cost_per_day: float,
        supported_attributes=None,
        location_flags=None,
    ):
        self.name = name
        self.capacity = capacity
        self.cost_per_day = cost_per_day
        self.supported_attributes = supported_attributes or []
        self.location_flags = location_flags or []
        self.current_licensees_list = []

    def is_space_available(self):
        return len(self.current_licensees_list) < self.capacity

    def add_licensee(self, licensee: Licensee):
        if self.is_space_available():
            self.current_licensees_list.append(licensee)
            licensee.change_status("Allocated")
            return True
        return False

    def remove_licensee(self, licensee: Licensee):
        if licensee in self.current_licensees_list:
            self.current_licensees_list.remove(licensee)
            licensee.change_status("Pending")

    def __str__(self):
        return f"{self.name} (Cap: {self.capacity}, £{self.cost_per_day}/day)"


class SystemController:
    def __init__(self):
        self.list_of_licensees: list[Licensee] = []
        self.list_of_rhus: list[RHU] = []

    def register_licensee(self, licensee: Licensee):
        self.list_of_licensees.append(licensee)

    def register_rhu(self, rhu: RHU):
        self.list_of_rhus.append(rhu)

    def move_licensee_state(self, licensee: Licensee, new_state: str):
        licensee.change_status(new_state)

    def rank_rhus_for_licensee(self, licensee: Licensee):
        scored_rhus = []

        for rhu in self.list_of_rhus:
            score = 0

            # Increase score for matching attributes
            for attr in licensee.required_matching_attributes:
                if attr in rhu.supported_attributes:
                    score += 10

            # Decrease score for conflicts
            for flag in rhu.location_flags:
                if flag in licensee.licence_conditions:
                    score -= 5

            # Apply cost penalty
            score -= rhu.cost_per_day

            scored_rhus.append((rhu, score))

        scored_rhus.sort(key=lambda x: x[1], reverse=True)
        return scored_rhus

    def detect_conflicts(self, licensee: Licensee, rhu: RHU):
        return any(
            condition in rhu.location_flags
            for condition in licensee.licence_conditions
        )


class CostCalculator:
    def __init__(self):
        self.total_cost = 0.0

    def calculate_daily_cost(self, rhu: RHU):
        return rhu.cost_per_day

    def calculate_total_cost(self, days: int, rhu: RHU):
        cost = days * rhu.cost_per_day
        self.total_cost += cost
        return cost

    def reset_costs(self):
        self.total_cost = 0.0



# GUI: Password Screen

class PasswordScreen(QWidget):
    login_success = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Password Screen")

        self.label = QLabel("Enter password:")
        self.input = QLineEdit()
        self.input.setEchoMode(QLineEdit.Password)
        self.input.setPlaceholderText("Password")

        self.button = QPushButton("Login")
        self.button.clicked.connect(self.check_password)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.input)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def check_password(self):
        if self.input.text() == "admin":  # simple hard-coded password
            self.login_success.emit()
            self.close()
        else:
            QMessageBox.warning(self, "Error", "Wrong password")
            self.input.clear()



# GUI: Cost Summary Screen

class CostSummaryScreen(QWidget):
    def __init__(self, cost_calculator: CostCalculator, controller: SystemController):
        super().__init__()
        self.setWindowTitle("Cost Summary")
        self.cost_calculator = cost_calculator
        self.controller = controller

        self.info_label = QLabel("Select an RHU in the main dashboard to estimate cost.")
        self.total_label = QLabel("Total accumulated cost: £0.00")

        self.days_input = QLineEdit()
        self.days_input.setPlaceholderText("Number of days")

        self.calculate_button = QPushButton("Calculate for selected RHU")
        self.calculate_button.clicked.connect(self.calculate_for_selected_rhu)

        layout = QVBoxLayout()
        layout.addWidget(self.info_label)
        layout.addWidget(self.days_input)
        layout.addWidget(self.calculate_button)
        layout.addWidget(self.total_label)
        self.setLayout(layout)

        self.current_rhu: RHU | None = None

    def set_current_rhu(self, rhu: RHU | None):
        self.current_rhu = rhu
        if rhu:
            self.info_label.setText(f"Selected RHU: {rhu.name} (£{rhu.cost_per_day}/day)")
        else:
            self.info_label.setText("No RHU selected.")

    def calculate_for_selected_rhu(self):
        if not self.current_rhu:
            QMessageBox.information(self, "Info", "No RHU selected.")
            return

        try:
            days = int(self.days_input.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid number of days.")
            return

        cost = self.cost_calculator.calculate_total_cost(days, self.current_rhu)
        self.total_label.setText(
            f"Total accumulated cost: £{self.cost_calculator.total_cost:.2f} "
            f"(Last calculation: £{cost:.2f})"
        )



# GUI: Main Dashboard

class MainDashboard(QWidget):
    def __init__(self, controller: SystemController, cost_calculator: CostCalculator):
        super().__init__()
        self.setWindowTitle("Main Dashboard")
        self.controller = controller
        self.cost_calculator = cost_calculator

        # Widgets
        self.licensee_list = QListWidget()
        self.rhu_list = QListWidget()

        self.allocate_button = QPushButton("Allocate Licensee to RHU")
        self.allocate_button.clicked.connect(self.allocate_licensee)

        self.refresh_button = QPushButton("Refresh Lists")
        self.refresh_button.clicked.connect(self.refresh_lists)

        self.cost_summary_button = QPushButton("Open Cost Summary")
        self.cost_summary_button.clicked.connect(self.open_cost_summary)

        # Layouts
        main_layout = QVBoxLayout()
        lists_layout = QHBoxLayout()
        buttons_layout = QHBoxLayout()

        lists_layout.addWidget(QLabel("Licensees"))
        lists_layout.addWidget(QLabel("RHUs"))

        lists_row = QHBoxLayout()
        lists_row.addWidget(self.licensee_list)
        lists_row.addWidget(self.rhu_list)

        buttons_layout.addWidget(self.allocate_button)
        buttons_layout.addWidget(self.refresh_button)
        buttons_layout.addWidget(self.cost_summary_button)

        main_layout.addLayout(lists_layout)
        main_layout.addLayout(lists_row)
        main_layout.addLayout(buttons_layout)

        self.setLayout(main_layout)

        # Cost summary window
        self.cost_summary_screen = CostSummaryScreen(cost_calculator, controller)

        self.refresh_lists()


        self.rhu_list.currentItemChanged.connect(self.update_cost_summary_rhu)

    def refresh_lists(self):
        self.licensee_list.clear()
        self.rhu_list.clear()

        for lic in self.controller.list_of_licensees:
            item = QListWidgetItem(str(lic))
            item.setData(1, lic)
            self.licensee_list.addItem(item)

        for rhu in self.controller.list_of_rhus:
            item = QListWidgetItem(str(rhu))
            item.setData(1, rhu)
            self.rhu_list.addItem(item)

    def get_selected_licensee(self) -> Licensee | None:
        item = self.licensee_list.currentItem()
        if not item:
            return None
        return item.data(1)

    def get_selected_rhu(self) -> RHU | None:
        item = self.rhu_list.currentItem()
        if not item:
            return None
        return item.data(1)

    def allocate_licensee(self):
        licensee = self.get_selected_licensee()
        rhu = self.get_selected_rhu()

        if not licensee or not rhu:
            QMessageBox.warning(self, "Error", "Select both a licensee and an RHU.")
            return

        # Check conflicts
        if self.controller.detect_conflicts(licensee, rhu):
            reply = QMessageBox.question(
                self,
                "Conflict detected",
                "There are conflicts between licence conditions and RHU flags.\n"
                "Do you still want to allocate?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.No:
                return

        if rhu.add_licensee(licensee):
            QMessageBox.information(
                self,
                "Success",
                f"{licensee.name} allocated to {rhu.name}.",
            )
        else:
            QMessageBox.warning(self, "Error", "No space available in this RHU.")

        self.refresh_lists()

    def open_cost_summary(self):
        self.cost_summary_screen.show()

    def update_cost_summary_rhu(self):
        rhu = self.get_selected_rhu()
        self.cost_summary_screen.set_current_rhu(rhu)



# Sample data setup

def create_sample_data(controller: SystemController):
    today = date.today()
    l1 = Licensee(
        "John Smith",
        "P001",
        today + timedelta(days=120),
        licence_conditions=["no_city_center"],
        required_matching_attributes=["mental_health_support"],
    )
    l2 = Licensee(
        "Jane Doe",
        "P002",
        today + timedelta(days=60),
        licence_conditions=["no_alcohol"],
        required_matching_attributes=["substance_misuse_support"],
    )
    l3 = Licensee(
        "Alex Brown",
        "P003",
        today + timedelta(days=200),
        licence_conditions=[],
        required_matching_attributes=["wheelchair_access"],
    )

    r1 = RHU(
        "RHU North",
        capacity=2,
        cost_per_day=80.0,
        supported_attributes=["mental_health_support", "wheelchair_access"],
        location_flags=["near_city_center"],
    )
    r2 = RHU(
        "RHU South",
        capacity=3,
        cost_per_day=60.0,
        supported_attributes=["substance_misuse_support"],
        location_flags=["near_pubs"],
    )
    r3 = RHU(
        "RHU East",
        capacity=1,
        cost_per_day=50.0,
        supported_attributes=["wheelchair_access"],
        location_flags=[],
    )

    for lic in (l1, l2, l3):
        controller.register_licensee(lic)

    for rhu in (r1, r2, r3):
        controller.register_rhu(rhu)



# Application entry point

def main():
    app = QApplication(sys.argv)

    controller = SystemController()
    cost_calculator = CostCalculator()
    create_sample_data(controller)

    password_window = PasswordScreen()
    dashboard = MainDashboard(controller, cost_calculator)

    password_window.login_success.connect(dashboard.show)

    password_window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
