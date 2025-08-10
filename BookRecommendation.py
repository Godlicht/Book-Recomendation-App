import requests
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk

API_URL = "https://www.googleapis.com/books/v1/volumes"
DB_FILE = "books.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS read_books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            author TEXT,
            category TEXT
        )
    """)
    conn.commit()
    conn.close()

def add_book(title, author, category):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO read_books (title, author, category) VALUES (?, ?, ?)",
              (title, author, category))
    conn.commit()
    conn.close()

def update_book(book_id, title, author, category):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE read_books SET title=?, author=?, category=? WHERE id=?",
              (title, author, category, book_id))
    conn.commit()
    conn.close()

def delete_book(book_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM read_books WHERE id=?", (book_id,))
    conn.commit()
    conn.close()

def get_all_books():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, title, author, category FROM read_books")
    books = c.fetchall()
    conn.close()
    return books

def search_books(query, max_results=10, lang="en"):
    params = {"q": query, "maxResults": max_results, "langRestrict": lang}
    r = requests.get(API_URL, params=params)
    data = r.json()

    results = []
    for item in data.get("items", []):
        volume_info = item.get("volumeInfo", {})
        title = volume_info.get("title", "No title")
        authors = ", ".join(volume_info.get("authors", ["No author"]))
        categories = ", ".join(volume_info.get("categories", ["No category"]))
        results.append((title, authors, categories))
    return results

def recommend_books():
    books = get_all_books()
    if not books:
        messagebox.showwarning("No Data", "Please add some read books first.")
        return []

    # We pick the most frequent author and category from read books
    authors = {}
    categories = {}

    for _, _, author, category in books:
        for a in author.split(","):
            a = a.strip()
            authors[a] = authors.get(a, 0) + 1
        for c in category.split(","):
            c = c.strip()
            categories[c] = categories.get(c, 0) + 1

    fav_author = max(authors, key=authors.get)
    fav_category = max(categories, key=categories.get)

    recs_author = search_books(f"inauthor:{fav_author}", lang="en")
    recs_category = search_books(f"subject:{fav_category}", lang="en")

    # Combine and remove duplicates
    combined = { (t,a,c): (t,a,c) for t,a,c in recs_author + recs_category }
    return list(combined.values())

class BookApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Book Recommendation System")
        self.state('zoomed')
        self.configure(bg="#f0f0f0")

        self.sort_column = None
        self.sort_reverse = False

        self.create_widgets()
        self.refresh_read_books()

    def create_widgets(self):
        # --- Form ---
        form_frame = tk.Frame(self, bg="#f0f0f0", pady=15)
        form_frame.pack(fill="x", padx=20)

        tk.Label(form_frame, text="Title:", font=("Arial", 12), bg="#f0f0f0").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.title_entry = tk.Entry(form_frame, font=("Arial", 12), width=40)
        self.title_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Author:", font=("Arial", 12), bg="#f0f0f0").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.author_entry = tk.Entry(form_frame, font=("Arial", 12), width=40)
        self.author_entry.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Category:", font=("Arial", 12), bg="#f0f0f0").grid(row=2, column=0, sticky="e", padx=5, pady=5)
        self.category_entry = tk.Entry(form_frame, font=("Arial", 12), width=40)
        self.category_entry.grid(row=2, column=1, padx=5, pady=5)

        add_btn = tk.Button(form_frame, text="Add Book", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white",
                            activebackground="#45a049", padx=15, pady=15, command=self.add_book_from_form)
        add_btn.grid(row=0, column=2, rowspan=3, padx=(20, 0), sticky="ns")

        # --- Filter ---
        filter_frame = tk.Frame(self, bg="#f0f0f0")
        filter_frame.pack(fill="x", padx=20)

        tk.Label(filter_frame, text="Filter:", font=("Arial", 12), bg="#f0f0f0").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda name, index, mode: self.apply_filter())
        filter_entry = tk.Entry(filter_frame, font=("Arial", 12), textvariable=self.filter_var)
        filter_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        refresh_btn = tk.Button(filter_frame, text="Refresh List", font=("Arial", 12), bg="#2196F3", fg="white",
                                activebackground="#1976D2", padx=10, pady=5, command=self.refresh_read_books)
        refresh_btn.pack(side="left", padx=10)

        # --- List ---
        list_frame = tk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        columns = ("Title", "Author", "Category")
        self.books_list = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        for col in columns:
            self.books_list.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))
            self.books_list.column(col, width=300 if col=="Title" else 200, anchor="w")
        self.books_list.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.books_list.yview)
        self.books_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # --- Buttons ---
        btn_frame = tk.Frame(self, bg="#f0f0f0", pady=10)
        btn_frame.pack(fill="x", padx=20, pady=(0, 15))

        rec_btn = tk.Button(btn_frame, text="Show Recommendations", font=("Arial", 12, "bold"),
                            bg="#2196F3", fg="white", activebackground="#1976D2", padx=20, pady=7,
                            command=self.show_recommendations)
        rec_btn.pack(side="left", padx=10)

        edit_btn = tk.Button(btn_frame, text="Edit Selected Book", font=("Arial", 12, "bold"),
                             bg="#FFC107", fg="black", activebackground="#FFA000", padx=15, pady=7,
                             command=self.edit_selected_book)
        edit_btn.pack(side="left", padx=10)

        delete_btn = tk.Button(btn_frame, text="Delete Selected Book", font=("Arial", 12, "bold"),
                               bg="#f44336", fg="white", activebackground="#d32f2f", padx=15, pady=7,
                               command=self.delete_selected_book)
        delete_btn.pack(side="left", padx=10)

    def add_book_from_form(self):
        title = self.title_entry.get().strip()
        author = self.author_entry.get().strip()
        category = self.category_entry.get().strip()

        if not title:
            messagebox.showerror("Input Error", "Please enter the book title.")
            return
        if not author:
            author = "Unknown"
        if not category:
            category = "Unknown"

        add_book(title, author, category)
        self.refresh_read_books()

        self.title_entry.delete(0, tk.END)
        self.author_entry.delete(0, tk.END)
        self.category_entry.delete(0, tk.END)

        messagebox.showinfo("Success", f"Book '{title}' added successfully!")

    def refresh_read_books(self):
        self.books_list.delete(*self.books_list.get_children())
        self.all_books = get_all_books()  # cache all books for filtering & sorting
        for book_id, t, a, c in self.all_books:
            self.books_list.insert("", "end", iid=book_id, values=(t, a, c))

    def apply_filter(self):
        filter_text = self.filter_var.get().lower()
        self.books_list.delete(*self.books_list.get_children())
        for book_id, t, a, c in self.all_books:
            if (filter_text in t.lower()) or (filter_text in a.lower()) or (filter_text in c.lower()):
                self.books_list.insert("", "end", iid=book_id, values=(t, a, c))

    def sort_by_column(self, col):
        col_map = {"Title": 1, "Author": 2, "Category": 3}
        idx = col_map[col]
        # Sort cache
        self.sort_reverse = not self.sort_reverse if self.sort_column == col else False
        self.sort_column = col

        sorted_books = sorted(self.all_books, key=lambda x: x[idx].lower(), reverse=self.sort_reverse)
        self.books_list.delete(*self.books_list.get_children())
        filter_text = self.filter_var.get().lower()
        for book_id, t, a, c in sorted_books:
            if (filter_text in t.lower()) or (filter_text in a.lower()) or (filter_text in c.lower()):
                self.books_list.insert("", "end", iid=book_id, values=(t, a, c))

    def show_recommendations(self):
        recs = recommend_books()
        if not recs:
            return

        rec_window = tk.Toplevel(self)
        rec_window.title("Book Recommendations")
        rec_window.geometry("700x400")

        rec_list = ttk.Treeview(rec_window, columns=("Title", "Author", "Category"), show="headings")
        for col in ("Title", "Author", "Category"):
            rec_list.heading(col, text=col)
            rec_list.column(col, width=230, anchor="w")
        rec_list.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(rec_window, orient="vertical", command=rec_list.yview)
        rec_list.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        for t, a, c in recs:
            rec_list.insert("", "end", values=(t, a, c))

    def edit_selected_book(self):
        selected = self.books_list.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a book to edit.")
            return
        book_id = selected[0]
        book = None
        for b in self.all_books:
            if str(b[0]) == book_id:
                book = b
                break
        if not book:
            messagebox.showerror("Error", "Selected book not found.")
            return

        edit_win = tk.Toplevel(self)
        edit_win.title("Edit Book")

        tk.Label(edit_win, text="Title:", font=("Arial", 12)).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        title_entry = tk.Entry(edit_win, font=("Arial", 12), width=40)
        title_entry.grid(row=0, column=1, padx=5, pady=5)
        title_entry.insert(0, book[1])

        tk.Label(edit_win, text="Author:", font=("Arial", 12)).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        author_entry = tk.Entry(edit_win, font=("Arial", 12), width=40)
        author_entry.grid(row=1, column=1, padx=5, pady=5)
        author_entry.insert(0, book[2])

        tk.Label(edit_win, text="Category:", font=("Arial", 12)).grid(row=2, column=0, padx=5, pady=5, sticky="e")
        category_entry = tk.Entry(edit_win, font=("Arial", 12), width=40)
        category_entry.grid(row=2, column=1, padx=5, pady=5)
        category_entry.insert(0, book[3])

        def save_changes():
            new_title = title_entry.get().strip()
            new_author = author_entry.get().strip()
            new_category = category_entry.get().strip()
            if not new_title:
                messagebox.showerror("Input Error", "Title cannot be empty.")
                return
            if not new_author:
                new_author = "Unknown"
            if not new_category:
                new_category = "Unknown"

            update_book(book_id, new_title, new_author, new_category)
            self.refresh_read_books()
            messagebox.showinfo("Success", "Book updated successfully!")
            edit_win.destroy()

        save_btn = tk.Button(edit_win, text="Save", font=("Arial", 12, "bold"), bg="#4CAF50", fg="white",
                             activebackground="#45a049", padx=15, pady=10, command=save_changes)
        save_btn.grid(row=3, column=0, columnspan=2, pady=10)

    def delete_selected_book(self):
        selected = self.books_list.selection()
        if not selected:
            messagebox.showerror("Selection Error", "Please select a book to delete.")
            return
        book_id = selected[0]
        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete the selected book?")
        if confirm:
            delete_book(book_id)
            self.refresh_read_books()
            messagebox.showinfo("Deleted", "Book deleted successfully.")

if __name__ == "__main__":
    init_db()
    app = BookApp()
    app.mainloop()
