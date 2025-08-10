# Book Recommendation System

A simple **Python** desktop application with a graphical user interface built using **Tkinter**. This app allows users to manage a personal list of read books and get English-language book recommendations based on their reading preferences.

## Features

- **Add books** with title, author, and category.
- **Edit and delete** existing books from your reading list.
- **Filter and sort** your book list by title, author, or category.
- **Recommend new books** based on your favorite authors and categories using the Google Books API (only English books).
- Data persistence with a lightweight **SQLite** database.
- Clean and user-friendly interface designed for easy navigation.

## How it works

The app stores your read books locally in a SQLite database. It analyzes the authors and categories you read most often, then fetches book recommendations from the Google Books API restricted to English-language books.

## Installation

1. Clone the repo:
   ```bash
   git clone https://github.com/godlicht/book-recommendation-app.git
   cd book-recommendation-app
