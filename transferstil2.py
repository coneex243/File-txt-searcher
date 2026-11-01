import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pandas as pd
import sqlite3
import csv
import re

class FileSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Поиск в файлах")
        
        # Переменные
        self.input_path = tk.StringVar()
        self.output_path = tk.StringVar()
        self.search_pattern = tk.StringVar(value=r'(любой запрос\любой запрос|любой запрос\любой запрос\любой запрос)')  # Обновленный шаблон
        
        # Виджеты
        tk.Label(root, text="G:\compressed_data\stealers").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(root, textvariable=self.input_path, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="Обзор", command=self.browse_input).grid(row=0, column=2, padx=5, pady=5)
        
        tk.Label(root, text="Шаблон для поиска (регулярное выражение):").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(root, textvariable=self.search_pattern, width=50).grid(row=1, column=1, padx=5, pady=5)
        tk.Label(root, text="Пример: любой запрос или любой запрос").grid(row=2, column=1, sticky="w", padx=10, pady=0)
        
        tk.Label(root, text="Путь для сохранения результатов (txt):").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        tk.Entry(root, textvariable=self.output_path, width=50).grid(row=3, column=1, padx=5, pady=5)
        tk.Button(root, text="Обзор", command=self.browse_output).grid(row=3, column=2, padx=5, pady=5)
        
        tk.Button(root, text="Начать поиск", command=self.start_search).grid(row=4, column=1, pady=10)
        
        # Прогресс бар
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.grid(row=5, column=0, columnspan=3, pady=10)
        
        # Текстовое поле для логов
        self.log_text = tk.Text(root, height=10, width=70, state="disabled")
        self.log_text.grid(row=6, column=0, columnspan=3, padx=10, pady=5)
        
    def browse_input(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.input_path.set(folder_path)
    
    def browse_output(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            self.output_path.set(file_path)
    
    def log_message(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")
        self.root.update()
    
    def start_search(self):
        input_path = self.input_path.get()
        output_path = self.output_path.get()
        pattern = self.search_pattern.get()
        
        if not all([input_path, output_path, pattern]):
            messagebox.showerror("Ошибка", "Заполните все поля!")
            return
        
        try:
            re.compile(pattern)
        except re.error:
            messagebox.showerror("Ошибка", "Некорректное регулярное выражение!")
            return
        
        self.log_message("Начало поиска...")
        self.progress["value"] = 0
        self.root.update()
        
        try:
            results = []
            files = [f for f in os.listdir(input_path) if os.path.isfile(os.path.join(input_path, f))]
            total_files = len(files)
            
            for i, filename in enumerate(files):
                file_path = os.path.join(input_path, filename)
                self.log_message(f"Обработка файла: {filename}")
                self.progress["value"] = (i / total_files) * 100
                self.root.update()
                
                try:
                    file_results = self.search_in_file(file_path, pattern, filename)
                    if file_results:
                        results.extend(file_results)
                except Exception as e:
                    self.log_message(f"Ошибка при обработке файла {filename}: {str(e)}")
            
            self.save_results(output_path, results)
            self.progress["value"] = 100
            self.log_message(f"Поиск завершен! Найдено {len(results)} строк с совпадениями.")
            messagebox.showinfo("Успех", f"Поиск завершен! Найдено {len(results)} строк с совпадениями.")
        except Exception as e:
            self.log_message(f"Критическая ошибка: {str(e)}")
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
    
    def search_in_file(self, file_path, pattern, filename):
        ext = os.path.splitext(file_path)[1].lower()
        results = []
        
        try:
            if ext == '.txt':
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if re.search(pattern, line):
                            # Добавляем имя файла к найденной строке
                            results.append(f"{line.strip()} | Файл: {filename}")
            
            elif ext == '.csv':
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        row_str = ' | '.join(row)
                        if re.search(pattern, row_str):
                            # Добавляем имя файла к найденной строке
                            results.append(f"{row_str} | Файл: {filename}")
            
            elif ext in ('.xls', '.xlsx'):
                df = pd.read_excel(file_path)
                for _, row in df.iterrows():
                    row_str = ' | '.join([str(x) for x in row.values])
                    if re.search(pattern, row_str):
                        # Добавляем имя файла к найденной строке
                        results.append(f"{row_str} | Файл: {filename}")
            
            elif ext == '.sqlite' or ext == '.db':
                conn = sqlite3.connect(file_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT * FROM {table_name}")
                    columns = [description[0] for description in cursor.description]
                    for row in cursor.fetchall():
                        row_str = ' | '.join([str(x) for x in row])
                        if re.search(pattern, row_str):
                            # Добавляем имя файла и таблицу к найденной строке
                            results.append(f"{row_str} | Файл: {filename} | Таблица: {table_name}")
                conn.close()
            
            else:
                self.log_message(f"Неизвестный формат файла: {file_path}")
        
        except Exception as e:
            self.log_message(f"Ошибка при чтении файла {file_path}: {str(e)}")
        
        return results
    
    def save_results(self, output_path, results):
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if not results:
                    f.write("Совпадений не найдено.")
                else:
                    for line in results:
                        f.write(line + "\n")
        except Exception as e:
            raise Exception(f"Ошибка при сохранении результатов: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSearchApp(root)
    root.mainloop()