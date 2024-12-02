
import tkinter as tk    # Importing Tkinter for GUI elements
from tkinter import messagebox  # Importing messagebox module from Tkinter for displaying messages
from tkinter import ttk # Importing ttk module from Tkinter for themed widgets
import re   # Importing re for regular expressions
import pickle   # Importing pickle for object serialization
import os   # Importing os for interacting with the operating system
from PIL import Image, ImageTk  # Importing PIL's Image and ImageTk modules for image handling
import urllib.request   # Importing urllib.request for handling URLs


class TrainTicketManagementSystem:
    def __init__(self):
        self.load_data()
        # Compute the next train ID dynamically
        self.next_train_id = self.compute_next_train_id()
        self.current_user = None

    def compute_next_train_id(self):
        if not self.trains:
            return 1  # No trains exist, start from 1
        max_id = max(
            int(train_id.split('-')[1]) for train_id in self.trains.keys() if train_id.startswith("Train-")
        )
        return max_id + 1

    def is_valid_email(self, email):
        return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None

    def register_user(self, email, password):
        if not self.is_valid_email(email):
            messagebox.showerror("Error", "Invalid email format.")
            return
        if email in self.users:
            messagebox.showerror("Error", "Email is already registered.")
            return
        self.users[email] = {"password": password, "profile": {}}
        self.save_data()
        messagebox.showinfo("Success", f"User registered successfully with email: {email}")

    def login_user(self, email, password):
        if not self.is_valid_email(email):
            messagebox.showerror("Error", "Invalid email format.")
            return False
        if email not in self.users:
            messagebox.showerror("Error", "Email is not registered.")
            return False
        if self.users[email]["password"] == password:
            self.current_user = email
            messagebox.showinfo("Success", "User logged in successfully!")
            return True
        else:
            messagebox.showerror("Error", "Incorrect password.")
            return False

    def add_train(self, source, destination, availability, timings, price):
        if self.current_user != "admin@gmail.com":
            messagebox.showerror("Error", "Only admin can add trains.")
            return
        train_id = f"Train-{self.next_train_id}"
        self.trains[train_id] = {
            "route": (source, destination),
            "availability": int(availability),
            "timings": timings,
            "price": price,
        }
        self.next_train_id += 1  # Increment for the next train
        self.save_data()
        messagebox.showinfo("Success", f"Train {train_id} added successfully!")

    def search_trains(self, source, destination):
        available_trains = []
        for train_id, details in self.trains.items():
            if details["route"] == (source, destination):
                available_trains.append(f"{train_id}: {details}")
        if not available_trains:
            return "No trains available for this route."
        return "\n".join(available_trains)

    def book_ticket(self, train_id, seats):
        try:
            seats = int(seats)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of seats.")
            return

        if train_id not in self.trains:
            messagebox.showerror("Error", "Invalid train ID.")
            return

        availability = int(self.trains[train_id]["availability"])

        if availability < seats:
            messagebox.showerror("Error", "Not enough seats available.")
            return

        self.trains[train_id]["availability"] = availability - seats
        self.bookings.append({"user_email": self.current_user, "train_id": train_id, "seats": seats})
        self.save_data()
        messagebox.showinfo("Success", f"Booking successful for {seats} seats on {train_id}.")

    def cancel_ticket(self, train_id, seats):
        try:
            seats = int(seats)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number of seats.")
            return

        for booking in self.bookings:
            if booking["user_email"] == self.current_user and booking["train_id"] == train_id:
                if booking["seats"] >= seats:
                    self.trains[train_id]["availability"] += seats
                    booking["seats"] -= seats
                    if booking["seats"] == 0:
                        self.bookings.remove(booking)
                    self.save_data()
                    messagebox.showinfo("Success", f"Successfully cancelled {seats} seats on {train_id}.")
                    return
        messagebox.showerror("Error", "Booking not found or invalid number of seats to cancel.")

    def generate_report(self):
        report_lines = []
        for booking in self.bookings:
            if booking["user_email"] == self.current_user:
                train_id = booking["train_id"]
                train_details = self.trains.get(train_id)
                if train_details:
                    source, destination = train_details["route"]
                    timings = train_details["timings"]
                    seats = booking["seats"]
                    report_lines.append(f"Train ID: {train_id}, Source: {source}, Destination: {destination}, "f"Timings: {timings}, Seats Booked: {seats}")
        if not report_lines:
            return "No bookings found."
        return "\n".join(report_lines)

    def save_data(self):
        with open("train_ticket_data.pkl", "wb") as file:
            pickle.dump({"users": self.users, "trains": self.trains, "bookings": self.bookings}, file)

    def load_data(self):
        if not os.path.exists("train_ticket_data.pkl"):
            self.users = {"admin@gmail.com": {"password": "12345", "profile": {}}}
            self.trains = {}
            self.bookings = []
            return
        try:
            with open("train_ticket_data.pkl", "rb") as file:
                data = pickle.load(file)
                self.users = data.get("users", {"admin@gmail.com": {"password": "12345", "profile": {}}})
                self.trains = data.get("trains", {})
                self.bookings = data.get("bookings", [])
        except EOFError:
            self.users = {"admin@gmail.com": {"password": "12345", "profile": {}}}
            self.trains = {}
            self.bookings = []



class TrainTicketManagementGUI:
    def __init__(self, root, system):
        self.root = root
        self.system = system
        self.root.title("Train Ticket Management System")
        self.root.geometry("800x600")
        self.load_background_image()
        self.setup_styles()  # Initialize custom styles
        self.main_menu(logged_in=False)
        self.root.bind("<Configure>", self.resize_background)

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Rounded.TFrame", background="#f0f0f0", padding=10)
        style.configure("Custom.TFrame", background="#ffffff", relief="solid", borderwidth=2)

        # Configure style for larger buttons with padding
        style.configure("Large.TButton", font=("Helvetica", 14), padding=(5, 5))

    def load_background_image(self):
        url = "https://img.freepik.com/free-photo/view-3d-modern-train-with-nature-scenery_23-2150905519.jpg"
        image_path = "background.jpg"
        urllib.request.urlretrieve(url, image_path)
        self.bg_image = Image.open(image_path)

    def resize_background(self, event=None):
        if hasattr(self, 'canvas') and self.canvas.winfo_exists():
            width = self.root.winfo_width()
            height = self.root.winfo_height()
            resized_bg = self.bg_image.resize((width, height), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(resized_bg)
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

    def setup_page_with_background(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.canvas = tk.Canvas(self.root, width=self.root.winfo_width(), height=self.root.winfo_height())
        self.canvas.pack(fill="both", expand=True)
        self.resize_background()

    def main_menu(self, logged_in):
        self.setup_page_with_background()

        # Create the frame with increased width, height, and rounded corners
        frame = ttk.Frame(self.root, style="Rounded.TFrame")
        frame.place(relx=0.5, rely=0.5, anchor="center", width=500, height=400)  # Adjust the width and height here

        # Apply border radius effect using rounded corners
        ttk.Label(frame, text="Train Ticket Reservation System", font=("Times New Roman", 28)).pack(pady=20)

        if not logged_in:
            # Display buttons for registration and login when not logged in
            register_button = ttk.Button(frame, text="Register", command=self.register, style="Large.TButton")
            register_button.pack(pady=20)
            login_button = ttk.Button(frame, text="Login", command=self.login, style="Large.TButton")
            login_button.pack(pady=20)
        else:
            # Display menu options when logged in
            ttk.Button(frame, text="Search Trains", command=self.search_trains, style="Large.TButton").pack(pady=5)
            ttk.Button(frame, text="Book Ticket", command=self.book_ticket, style="Large.TButton").pack(pady=5)
            ttk.Button(frame, text="Cancel Ticket", command=self.cancel_ticket, style="Large.TButton").pack(pady=5)
            ttk.Button(frame, text="Booking Report", command=self.view_report, style="Large.TButton").pack(pady=5)
            ttk.Button(frame, text="Show All Trains", command=self.show_all_trains, style="Large.TButton").pack(pady=5)

            if self.system.current_user == "admin@gmail.com":
                # Add train option for admin
                ttk.Button(frame, text="Add Train (Admin)", command=self.add_train, style="Large.TButton").pack(pady=5)
            else:
                # Logout option for non-admin users
                ttk.Button(frame, text="Logout", command=self.logout_user, style="Large.TButton").pack(pady=5)

    def logout_user(self):
        """Logs out the current user and returns to the main menu."""
        self.system.current_user = None  # Clear the current user
        messagebox.showinfo("Logout", "You have been logged out.")
        self.main_menu(logged_in=False)

    def register(self):
        self.setup_page_with_background()

        # Create a frame with larger dimensions and prevent resizing
        frame = ttk.Frame(self.root, width=400, height=350)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)  # Prevent frame from shrinking to fit content

        # Title label with larger font
        ttk.Label(frame, text="Register", font=("Times New Roman", 25)).pack(pady=5)

        # Email label and entry
        ttk.Label(frame, text="Email:").pack(pady=(5, 2))
        email_entry = ttk.Entry(frame, width=30)
        email_entry.pack(pady=5)

        # Password label and entry
        ttk.Label(frame, text="Password:").pack(pady=(5, 2))
        password_entry = ttk.Entry(frame, show="*", width=30)
        password_entry.pack(pady=5)

        # Show Password Checkbox
        show_password_var = tk.BooleanVar()
        show_password_checkbox = ttk.Checkbutton(frame, text="Show Password", variable=show_password_var,command=lambda: self.toggle_password_visibility(password_entry, show_password_var))
        show_password_checkbox.pack(pady=5)

        # Register and Back buttons with larger padding
        ttk.Button(frame, text="Register",command=lambda: self.system.register_user(email_entry.get(), password_entry.get())).pack(pady=10)
        ttk.Button(frame, text="Back to Main Menu", command=lambda: self.main_menu(logged_in=False)).pack(pady=10)

    def login(self):
        self.setup_page_with_background()

        # Create a frame with larger dimensions
        frame = ttk.Frame(self.root, width=400, height=350)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)  # Prevent the frame from resizing to fit content

        ttk.Label(frame, text="Login", font=("Times New Roman", 25)).pack(pady=5)

        # Email label and entry
        ttk.Label(frame, text="Email:").pack(pady=(5, 3))
        email_entry = ttk.Entry(frame, width=30)
        email_entry.pack(pady=5)

        # Password label and entry
        ttk.Label(frame, text="Password:").pack(pady=(5, 3))
        password_entry = ttk.Entry(frame, show="*", width=30)
        password_entry.pack(pady=5)

        # Show Password Checkbox
        show_password_var = tk.BooleanVar()
        show_password_checkbox = ttk.Checkbutton(frame, text="Show Password", variable=show_password_var,command=lambda: self.toggle_password_visibility(password_entry, show_password_var))
        show_password_checkbox.pack(pady=5)

        # Login and Back buttons with larger padding
        ttk.Button(frame, text="Login", command=lambda: self.login_user(email_entry.get(), password_entry.get())).pack(pady=10)
        ttk.Button(frame, text="Back to Main Menu", command=lambda: self.main_menu(logged_in=False)).pack(pady=10)

    def toggle_password_visibility(self, entry, show_var):
        entry.config(show="" if show_var.get() else "*")

    def login_user(self, email, password):
        if self.system.login_user(email, password):
            self.main_menu(logged_in=True)

    def add_train(self):
        self.setup_page_with_background()

        # Create a larger frame and prevent resizing
        frame = ttk.Frame(self.root, width=500, height=500)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)  # Prevent frame from shrinking to fit content

        # Title with larger font
        ttk.Label(frame, text="Add Train", font=("Times New Roman", 30)).pack(pady=10)

        # Source label and entry with padding
        ttk.Label(frame, text="Source:").pack(pady=(5, 2))
        source_entry = ttk.Entry(frame, width=35)
        source_entry.pack(pady=5)

        # Destination label and entry
        ttk.Label(frame, text="Destination:").pack(pady=(5, 2))
        destination_entry = ttk.Entry(frame, width=35)
        destination_entry.pack(pady=5)

        # Availability label and entry
        ttk.Label(frame, text="Availability:").pack(pady=(5, 2))
        availability_entry = ttk.Entry(frame, width=35)
        availability_entry.pack(pady=5)

        # Timings label and entry
        ttk.Label(frame, text="Timings:").pack(pady=(5, 2))
        timings_entry = ttk.Entry(frame, width=35)
        timings_entry.pack(pady=5)

        # Price label and entry
        ttk.Label(frame, text="Price:").pack(pady=(5, 2))
        price_entry = ttk.Entry(frame, width=35)
        price_entry.pack(pady=5)

        # Buttons with extra padding
        ttk.Button(frame, text="Add Train", command=lambda: self.system.add_train(source_entry.get(), destination_entry.get(), availability_entry.get(), timings_entry.get(),price_entry.get())).pack(pady=10)

        ttk.Button(frame, text="Back to Main Menu", command=lambda: self.main_menu(logged_in=True)).pack(pady=10)

    def search_trains(self):
        self.setup_page_with_background()

        # Create a larger frame and prevent it from resizing to content
        frame = ttk.Frame(self.root, width=400, height=350)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)  # Keep frame size fixed

        # Title label with larger font and padding
        ttk.Label(frame, text="Search Trains", font=("Times New Roman", 30)).pack(pady=7)

        # Source label and entry with additional padding
        ttk.Label(frame, text="Source:").pack(pady=(3, 1))
        source_entry = ttk.Entry(frame, width=35)
        source_entry.pack(pady=3)

        # Destination label and entry
        ttk.Label(frame, text="Destination:").pack(pady=(3, 1))
        destination_entry = ttk.Entry(frame, width=35)
        destination_entry.pack(pady=3)

        # Output label for displaying search results
        output_label = ttk.Label(frame, text="", wraplength=350)  # Wrap text to fit within frame
        output_label.pack(pady=3)

        # Buttons with extra padding
        ttk.Button(frame, text="Search", command=lambda: output_label.config(text=self.system.search_trains(source_entry.get(), destination_entry.get()))).pack(pady=5)

        ttk.Button(frame, text="Back to Main Menu", command=lambda: self.main_menu(logged_in=True)).pack(pady=5)

    def book_ticket(self):
        self.setup_page_with_background()

        # Create a larger frame and fix its size
        frame = ttk.Frame(self.root, width=400, height=300)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)  # Prevent resizing to content

        # Title label with increased font size and padding
        ttk.Label(frame, text="Book Ticket", font=("Times New Roman", 30)).pack(pady=10)

        # Train ID label and entry with additional padding
        ttk.Label(frame, text="Train ID:").pack(pady=(5, 2))
        train_id_entry = ttk.Entry(frame, width=30)
        train_id_entry.pack(pady=5)

        # Seats label and entry
        ttk.Label(frame, text="Seats:").pack(pady=(5, 2))
        seats_entry = ttk.Entry(frame, width=30)
        seats_entry.pack(pady=5)

        # Book button with padding
        ttk.Button(frame, text="Book",command=lambda: self.system.book_ticket(train_id_entry.get(), seats_entry.get())).pack(pady=7)

        # Back button with padding
        ttk.Button(frame, text="Back to Main Menu", command=lambda: self.main_menu(logged_in=True)).pack(pady=7)

    def cancel_ticket(self):
        self.setup_page_with_background()

        # Create a larger frame and fix its size
        frame = ttk.Frame(self.root, width=400, height=300)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)  # Prevent resizing to content

        # Title label with increased font size and padding
        ttk.Label(frame, text="Cancel Ticket", font=("Times New Roman", 30)).pack(pady=10)

        # Train ID label and entry with additional padding
        ttk.Label(frame, text="Train ID:").pack(pady=(5, 2))
        train_id_entry = ttk.Entry(frame, width=30)
        train_id_entry.pack(pady=5)

        # Seats label and entry
        ttk.Label(frame, text="Seats:").pack(pady=(5, 2))
        seats_entry = ttk.Entry(frame, width=30)
        seats_entry.pack(pady=5)

        # Cancel button with padding
        ttk.Button(frame, text="Cancel",command=lambda: self.system.cancel_ticket(train_id_entry.get(), seats_entry.get())).pack(pady=10)

        # Back button with padding
        ttk.Button(frame, text="Back to Main Menu", command=lambda: self.main_menu(logged_in=True)).pack(pady=10)

    def show_all_trains(self):
        self.setup_page_with_background()

        # Create a frame with a scrollable canvas
        outer_frame = ttk.Frame(self.root, width=500, height=400)
        outer_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Canvas to hold the scrollable content
        canvas = tk.Canvas(outer_frame, width=400, height=400)
        scrollbar = ttk.Scrollbar(outer_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack the canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Title centered above the scrollable content
        title_label = ttk.Label(scrollable_frame, text="All Trains", font=("Times New Roman", 30))
        title_label.pack(pady=10, anchor="center")

        # Display each train's details in the scrollable frame (centered)
        for train_id, train in self.system.trains.items():
            train_details = (
                f"Train ID: {train_id}\n"
                f"Source: {train['route'][0]} | Destination: {train['route'][1]}\n"
                f"Availability: {train['availability']} | Timings: {train['timings']} | Price: {train['price']}\n"
            )
            train_label = ttk.Label(scrollable_frame, text=train_details, justify="center", wraplength=650)
            train_label.pack(pady=5, anchor="center")

        # Frame for the back button (placed below the scrollable area)
        back_button_frame = ttk.Frame(self.root)
        back_button_frame.place(relx=0.5, rely=0.86, anchor="center")

        # Back button (separated from the scrollable content)
        back_button = ttk.Button(back_button_frame, text="Back to Main Menu",
                                 command=lambda: self.main_menu(logged_in=True))
        back_button.pack(pady=0)

    def view_report(self):
        self.setup_page_with_background()

        # Create a larger frame with fixed dimensions
        frame = ttk.Frame(self.root, width=600, height=300)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)  # Prevent frame from resizing to fit its content

        # Add title label with increased font size and padding
        ttk.Label(frame, text="Booking Report", font=("Times New Roman", 30)).pack(pady=20)

        # Display the generated report content with wrapping and padding
        report = self.system.generate_report()
        ttk.Label(frame, text=report, wraplength=550, justify="left").pack(pady=15)

        # Add a Back button with padding
        ttk.Button(frame, text="Back to Main Menu", command=lambda: self.main_menu(logged_in=True)).pack(pady=25)


if __name__ == "__main__":
    root = tk.Tk()
    system = TrainTicketManagementSystem()
    app = TrainTicketManagementGUI(root, system)
    root.mainloop()


