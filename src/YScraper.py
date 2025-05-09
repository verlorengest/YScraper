import io
import os
import textwrap
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog, simpledialog
import xml.etree.ElementTree as ET
from selenium.common import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException
import time
import undetected_chromedriver as uc
import requests
import json
import csv
import webbrowser
import re
import base64
import time
import threading
from urllib.parse import urlparse, quote_plus
import json
from enum import Enum
import xml.dom.minidom as minidom
import webbrowser

from selenium.webdriver.support.wait import WebDriverWait


class SortEnum(Enum):
    RELEVANT = 1
    NEWEST = 2
    HIGHEST_RATING = 3
    LOWEST_RATING = 4


class App:
    def __init__(self, master):
        self.master = master
        master.title("YScraper")
        master.geometry("1300x800")
        master.resizable(False, True)


        try:
            # Assuming 'app_icon.ico' is in the same directory as the script
            icon_path = os.path.join(os.path.dirname(__file__), 'app_icon.ico')
            if os.path.exists(icon_path):
                master.iconbitmap(icon_path)
            else:
                print("Warning: app_icon.ico not found. Skipping icon setting.")
        except tk.TclError:
            print("Warning: Could not set .ico icon (platform may not support .ico or file is invalid).")
        except Exception as e:
            print(f"Warning: An error occurred setting icon: {e}")


        self._setup_styles() 

        footer_frame = ttk.Frame(master, style="TFrame") 
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=5, pady=(2, 5)) # Fill horizontally

        self.developer_label = tk.Label(
            footer_frame, 
            text="Developed by Kaan Soyler",
            font=(self.font_label[0], 9),
            fg="blue",
            cursor="hand2"
        )
        # Pack to the right side *within* the footer_frame
        self.developer_label.pack(side=tk.RIGHT, padx=5) # No anchor needed if it's the only thing on the right
        self.developer_label.bind("<Button-1>", self._open_developer_link)
        # --- End Developer Credit Label ---

        self.youtube_notebook = ttk.Notebook(master)
        self.youtube_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0)) # Fill remaining space


        self.setup_youtube_tabs()

        # Data storage
        self.reviews_data = None
        self.youtube_comments = None
        self.place_data = {}



#----YOUTUBE-------

    def _open_developer_link(self, event=None):
            """Opens the developer's link in a web browser."""

            url_to_open = "https://github.com/verlorengest" 

            try:
                print(f"Opening link: {url_to_open}") # For debugging
                webbrowser.open(url_to_open)
            except Exception as e:
                error_msg = f"Could not open link {url_to_open}: {e}"
                print(error_msg)
                messagebox.showerror("Error", error_msg)



    def _setup_styles(self):
            self.style = ttk.Style()
            self.style.theme_use('clam') # Use 'clam' theme as a base

            # Define fonts
            self.font_label = ("Arial", 11)
            self.font_label_bold = ("Arial", 11, "bold")
            self.font_entry = ("Arial", 12)
            self.font_button = ("Arial", 12, "bold")
            self.font_text_area = ("Courier New", 10) # For ScrolledText
            self.font_status = ("Arial", 10)
            self.font_treeview_header = ("Arial", 10, "bold")
            self.font_treeview_text = ("Arial", 10) # For Treeview items

            # Configure ttk styles
            self.style.configure("TLabel", font=self.font_label)
            self.style.configure("Bold.TLabel", font=self.font_label_bold)
            self.style.configure("Status.TLabel", font=self.font_status, padding=5)
            self.style.configure("Error.TLabel", font=self.font_label, foreground="red")

            self.style.configure("TEntry", font=self.font_entry, padding=3)
            self.style.configure("TButton", font=self.font_button, padding=5)
            self.style.map("TButton",
                             foreground=[('disabled', 'grey')],
                             background=[('active', '#e0e0e0')])

            self.style.configure("TNotebook", tabposition='nw') # Ensure tabs are on top

            desired_tab_padding = [100, 5]

            self.style.configure("TNotebook.Tab",
                                 font=self.font_label_bold,
                                 padding=desired_tab_padding)

            # Explicitly map the padding to ensure 'selected' and 'active' (hover)
            # states also use this desired_tab_padding. This prevents shrinking.
            self.style.map("TNotebook.Tab",
                           padding=[('selected', desired_tab_padding),
                                    ('active', desired_tab_padding)])
            # --- END SOLUTION ---


            self.style.configure("TLabelframe", padding=10)
            self.style.configure("TLabelframe.Label", font=self.font_label_bold)

            self.style.configure("Treeview.Heading", font=self.font_treeview_header)
            self.style.configure("Treeview", font=self.font_treeview_text, rowheight=25)

            self.style.configure("TCheckbutton", font=self.font_label)
            self.style.configure("TRadiobutton", font=self.font_label)
            
            self.style.configure("Horizontal.TProgressbar", thickness=20, background='green')

    def setup_youtube_tabs(self):
        # Widen tabs
        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[100, 5])

        # Scraper
        self.y_scraper_tab = ttk.Frame(self.youtube_notebook)
        self.youtube_notebook.add(self.y_scraper_tab, text="Scraper")
        self.setup_youtube_scraper_tab()

        # Pretty View
        self.y_pretty_tab = ttk.Frame(self.youtube_notebook)
        self.youtube_notebook.add(self.y_pretty_tab, text="Pretty View")
        self.setup_youtube_pretty_tab()

        # User Ops
        self.y_user_ops_tab = ttk.Frame(self.youtube_notebook)
        self.youtube_notebook.add(self.y_user_ops_tab, text="User Ops")
        self.setup_youtube_user_ops_tab()
        self.update_youtube_ui_to_add_missing_functions()

    def setup_youtube_scraper_tab(self):
        frame = ttk.Frame(self.y_scraper_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Input frame
        input_frame = ttk.LabelFrame(frame, text="Input", style="TLabelframe")
        input_frame.pack(fill=tk.X, pady=5)

        # --- Scrape Mode Selection ---
        mode_selection_frame = ttk.Frame(input_frame)
        mode_selection_frame.pack(side=tk.LEFT, padx=5, pady=(0,5), anchor=tk.NW) # Anchor to top-west

        ttk.Label(mode_selection_frame, text="Scrape Mode:", style="Bold.TLabel").pack(side=tk.TOP, anchor=tk.W, pady=(0,3))

        self.y_scrape_mode_var = tk.StringVar(value="video") # Default to single video
        modes = [
            ("Single Video", "video"),
            ("Channel", "channel"),
            ("List from File", "list")
        ]
        for text, mode in modes:
            rb = ttk.Radiobutton(mode_selection_frame, text=text, variable=self.y_scrape_mode_var,
                                 value=mode, command=self.toggle_youtube_input_mode, style="TRadiobutton")
            rb.pack(side=tk.TOP, anchor=tk.W)
        # --- End Scrape Mode Selection ---


        # --- Mode-Specific Input Area ---
        # This frame will hold the dynamically changing input fields.
        # We need a container for inputs that change based on mode, separate from always-visible options.
        self.y_dynamic_input_area = ttk.Frame(input_frame)
        self.y_dynamic_input_area.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)


        # --- Video URL Input (initially visible for "video" mode) ---
        self.y_video_url_frame = ttk.Frame(self.y_dynamic_input_area)
        # self.y_video_url_frame.pack(side=tk.LEFT, fill=tk.X, expand=True) # Packed in toggle_youtube_input_mode

        ttk.Label(self.y_video_url_frame, text="YouTube Video URL:").pack(side=tk.LEFT, padx=5)
        self.y_url_entry = ttk.Entry(self.y_video_url_frame)
        self.y_url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        # --- End Video URL Input ---


        # --- Channel URL Input (initially hidden) ---
        self.y_channel_url_frame = ttk.Frame(self.y_dynamic_input_area)
        self.y_channel_label = ttk.Label(self.y_channel_url_frame, text="YouTube Channel URL:")
        self.y_channel_entry = ttk.Entry(self.y_channel_url_frame)
        # --- End Channel URL Input ---


        # --- Channel Video Limit Input (initially hidden) ---
        self.y_channel_limit_frame = ttk.Frame(self.y_dynamic_input_area)
        self.y_channel_limit_label = ttk.Label(self.y_channel_limit_frame, text="Number of Videos (or 'all'):")
        self.y_channel_limit_var = tk.StringVar(value="all")
        self.y_channel_limit_entry = ttk.Entry(self.y_channel_limit_frame, textvariable=self.y_channel_limit_var, width=10)
        # --- End Channel Video Limit Input ---


        # --- List File Input (initially hidden) ---
        self.y_list_file_frame = ttk.Frame(self.y_dynamic_input_area)
        self.y_list_file_label = ttk.Label(self.y_list_file_frame, text="URL List File (.txt):")
        self.y_list_file_entry = ttk.Entry(self.y_list_file_frame, width=30) # Adjusted width
        self.y_list_browse_button = ttk.Button(self.y_list_file_frame, text="Browse...", command=self.browse_youtube_list_file)
        # --- End List File Input ---


        # --- Common Inputs (Scroll times, Options) ---
        # These are always visible but their position relative to dynamic inputs is managed by toggle_youtube_input_mode
        # Scroll times for video scraping
        self.y_scroll_label = ttk.Label(self.y_dynamic_input_area, text="Scroll times:")
        self.y_scroll_var = tk.IntVar(value=5)
        self.y_scroll_entry = ttk.Entry(self.y_dynamic_input_area, textvariable=self.y_scroll_var, width=4)

        # Options frame for checkboxes - This will be packed to the right of dynamic inputs / scroll times
        options_frame = ttk.Frame(input_frame)
        options_frame.pack(side=tk.LEFT, padx=15, anchor=tk.NW) # Pack to the left of input_frame, but after dynamic_input_area

        self.y_include_replies = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Include Replies", variable=self.y_include_replies, style="TCheckbutton").pack(anchor=tk.W, pady=(0,2))

        self.y_include_photos = tk.BooleanVar(value=False)
        ttk.Checkbutton(options_frame, text="Include Profile Photos", variable=self.y_include_photos, style="TCheckbutton").pack(anchor=tk.W)

        # --- Debug Mode Checkbox ---
        self.y_debug_mode_var = tk.BooleanVar(value=False) # Default to False (headless)
        ttk.Checkbutton(options_frame, text="Debug Mode (Show Browser)", variable=self.y_debug_mode_var, style="TCheckbutton").pack(anchor=tk.W)
        # --- End Debug Mode Checkbox ---
        
        # --- End Common Inputs ---


        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=10)

        self.y_scrape_button = ttk.Button(btn_frame, text="Scrape Comments", command=self.start_youtube_scraping)
        self.y_scrape_button.pack(side=tk.LEFT, padx=5)

        self.y_pause_button = ttk.Button(btn_frame, text="Pause", command=self.pause_youtube_scraping, state=tk.DISABLED)
        self.y_pause_button.pack(side=tk.LEFT, padx=5)

        self.y_stop_button = ttk.Button(btn_frame, text="Stop", command=self.stop_youtube_scraping, state=tk.DISABLED)
        self.y_stop_button.pack(side=tk.LEFT, padx=5)

        self.y_save_button = ttk.Button(btn_frame, text="Save JSON", command=self.save_youtube_json, state=tk.DISABLED)
        self.y_save_button.pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Clear", command=self.clear_youtube).pack(side=tk.LEFT, padx=5)

        # Status & results
        self.y_progress = ttk.Progressbar(frame, maximum=100, style="Horizontal.TProgressbar")
        self.y_progress.pack(fill=tk.X, pady=5)
        self.y_status = tk.StringVar(value="Ready")
        ttk.Label(frame, textvariable=self.y_status, style="Status.TLabel").pack(anchor=tk.W)
        res_frame = ttk.LabelFrame(frame, text="Raw Results", style="TLabelframe")
        res_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.y_results_text = scrolledtext.ScrolledText(res_frame, font=self.font_text_area)
        self.y_results_text.pack(fill=tk.BOTH, expand=True)

        self.scraping_paused = False
        self.scraping_stopped = False
        self.scraping_thread = None
        self.youtube_comments = []

        # Call toggle function to set initial state based on default radio button
        self.toggle_youtube_input_mode()

    def setup_youtube_pretty_tab(self):
        frame = ttk.Frame(self.y_pretty_tab, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # Configure grid for the main frame layout
        frame.grid_columnconfigure(0, weight=1) # Allow content to expand horizontally
        # Row 0: search_frame
        # Row 1: controls_frame
        # Row 2: PanedWindow containing tree and details (this will expand vertically)
        frame.grid_rowconfigure(2, weight=1) # The PanedWindow itself will expand to fill available space


        # Search and filter frame
        search_frame = ttk.LabelFrame(frame, text="Search & Filter", style="TLabelframe")
        search_frame.grid(row=0, column=0, sticky="ew", pady=5)

        search_label = ttk.Label(search_frame, text="Search:")
        search_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.y_search_entry = ttk.Entry(search_frame, width=25)
        self.y_search_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        column_label = ttk.Label(search_frame, text="Column:")
        column_label.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)
        self.y_search_column = tk.StringVar(value="All")
        columns = ["All", "Author", "Time", "Likes", "Text"]
        column_dropdown = ttk.Combobox(search_frame, textvariable=self.y_search_column, values=columns, width=10)
        column_dropdown.config(font=self.font_entry)
        column_dropdown.grid(row=0, column=3, padx=5, pady=5, sticky=tk.W)
        search_button = ttk.Button(search_frame, text="Search", command=self.search_youtube_comments)
        search_button.grid(row=0, column=4, padx=5, pady=5, sticky=tk.W)
        reset_button = ttk.Button(search_frame, text="Reset", command=self.reset_youtube_search)
        reset_button.grid(row=0, column=5, padx=5, pady=5, sticky=tk.W)
        self.y_sort_direction = tk.StringVar(value="Ascending")
        sort_radio_frame = ttk.Frame(search_frame)
        sort_radio_frame.grid(row=0, column=6, padx=10, pady=5, sticky=tk.W)
        ttk.Radiobutton(sort_radio_frame, text="Asc", variable=self.y_sort_direction, value="Ascending", style="TRadiobutton").pack(side=tk.LEFT)
        ttk.Radiobutton(sort_radio_frame, text="Desc", variable=self.y_sort_direction, value="Descending", style="TRadiobutton").pack(side=tk.LEFT)
        search_frame.grid_columnconfigure(1, weight=1)

        # Controls frame (contains export options and view buttons)
        controls_frame = ttk.Frame(frame)
        controls_frame.grid(row=1, column=0, sticky="ew", pady=5)

        export_and_view_labelframe = ttk.LabelFrame(controls_frame, text="Actions", style="TLabelframe")
        export_and_view_labelframe.pack(fill=tk.X, expand=True, padx=0)
        all_actions_frame = ttk.Frame(export_and_view_labelframe)
        all_actions_frame.pack(fill=tk.X, pady=5)
        export_buttons_frame = ttk.Frame(all_actions_frame)
        export_buttons_frame.pack(side=tk.LEFT, padx=(0,10))
        self.y_export_fields = {
            "author": tk.BooleanVar(value=True), "time": tk.BooleanVar(value=True),
            "likes": tk.BooleanVar(value=True), "text": tk.BooleanVar(value=True),
            "replies": tk.BooleanVar(value=True)
        }
        fields_frame = ttk.Frame(export_buttons_frame)
        fields_frame.pack(fill=tk.X, pady=(0,5))
        for i, (field, var) in enumerate(self.y_export_fields.items()):
            ttk.Checkbutton(fields_frame, text=field.capitalize(), variable=var, style="TCheckbutton").grid(row=0, column=i, padx=5)
        self.y_export_xml_button = ttk.Button(export_buttons_frame, text="Export XML", command=self.export_youtube_to_xml, state=tk.DISABLED)
        self.y_export_xml_button.pack(side=tk.LEFT, padx=2)
        self.y_export_json_button = ttk.Button(export_buttons_frame, text="Export JSON", command=self.export_youtube_to_json, state=tk.DISABLED)
        self.y_export_json_button.pack(side=tk.LEFT, padx=2)
        self.y_export_csv_button = ttk.Button(export_buttons_frame, text="Export CSV", command=self.export_youtube_to_csv, state=tk.DISABLED)
        self.y_export_csv_button.pack(side=tk.LEFT, padx=2)
        view_buttons_frame = ttk.Frame(all_actions_frame)
        view_buttons_frame.pack(side=tk.LEFT, padx=5)
        ttk.Button(view_buttons_frame, text="Expand All", command=self.expand_all_youtube_replies).pack(side=tk.LEFT, padx=2)
        ttk.Button(view_buttons_frame, text="Collapse All", command=self.collapse_all_youtube_replies).pack(side=tk.LEFT, padx=2)


        # --- Create PanedWindow for Treeview and Details ---
        content_pane = ttk.PanedWindow(frame, orient=tk.VERTICAL)
        content_pane.grid(row=2, column=0, sticky="nsew", pady=5)

        # Comments treeview Frame (will be a pane)
        tree_frame = ttk.Frame(content_pane, relief=tk.SUNKEN, borderwidth=1) # Added relief for visual separation
        # tree_frame's children will use grid to fill tree_frame
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        # Add tree_frame to PanedWindow with a weight (e.g., 2 parts of initial space)
        content_pane.add(tree_frame, weight=3) # TreeView gets more initial space

        self.y_tree = ttk.Treeview(tree_frame, columns=("author", "time", "likes", "text"), show="tree headings", style="Treeview")
        self.y_tree.heading("author", text="Author", command=lambda: self.sort_youtube_treeview("author"))
        self.y_tree.heading("time", text="Time", command=lambda: self.sort_youtube_treeview("time"))
        self.y_tree.heading("likes", text="Likes", command=lambda: self.sort_youtube_treeview("likes"))
        self.y_tree.heading("text", text="Comment Text", command=lambda: self.sort_youtube_treeview("text"))
        self.y_tree.column("author", width=150, anchor="w")
        self.y_tree.column("time", width=100, anchor="w")
        self.y_tree.column("likes", width=50, anchor="center")
        self.y_tree.column("text", width=350, anchor="w")
        self.y_tree.column("#0", width=30)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.y_tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.y_tree.xview)
        self.y_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.y_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew") # Scrollbar for tree text itself


        # Review details Frame (will be another pane)
        details_frame = ttk.LabelFrame(content_pane, text="Comment Details", style="TLabelframe")
        # details_frame's children will use grid to fill details_frame
        details_frame.grid_rowconfigure(0, weight=1)
        details_frame.grid_columnconfigure(0, weight=1)
        # Add details_frame to PanedWindow with a weight (e.g., 1 part of initial space)
        content_pane.add(details_frame, weight=2) # Details get less initial space

        self.y_detail = scrolledtext.ScrolledText(details_frame, wrap=tk.WORD, height=15, font=self.font_text_area)
        self.y_detail.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        self.y_tree.bind("<ButtonRelease-1>", self.show_youtube_comment)

    def populate_youtube_pretty(self, comments):
        self.y_tree.delete(*self.y_tree.get_children())

        # Store reference to comments with proper indices
        self.youtube_comments_indexed = []

        for i, c in enumerate(comments):
            txt = c['text'][:100] + ('...' if len(c['text']) > 100 else '')
            # Add main comment
            comment_id = f"c{i}"
            self.y_tree.insert('', 'end', iid=comment_id, values=(c['author'], c['time'], c['likes'], txt))
            self.youtube_comments_indexed.append({"type": "main", "data": c})

            # Add replies if they exist
            if 'replies' in c and c['replies']:
                for j, reply in enumerate(c['replies']):
                    reply_txt = reply['text'][:100] + ('...' if len(reply['text']) > 100 else '')
                    reply_id = f"c{i}r{j}"

                    # Insert replies as children of the main comment
                    self.y_tree.insert(comment_id, 'end', iid=reply_id, values=(
                        f"↪ {reply['author']}",
                        reply['time'],
                        reply['likes'],
                        f"[Reply to {c['author']}] {reply_txt}"
                    ))
                    self.youtube_comments_indexed.append({"type": "reply", "data": reply, "parent": c})

                # Expand the parent comment to show replies
                self.y_tree.item(comment_id, open=True)

        # Enable export buttons
        self.y_export_json_button.config(state=tk.NORMAL)
        self.y_export_csv_button.config(state=tk.NORMAL)
        self.y_export_xml_button.config(state=tk.NORMAL)

    def setup_youtube_user_ops_tab(self):
        frame = ttk.Frame(self.y_user_ops_tab,padding="10")
        frame.pack(fill=tk.BOTH,expand=True)
        lf = ttk.LabelFrame(frame,text="Filter by Author", style="TLabelframe") # Apply TLabelframe
        lf.pack(fill=tk.X,pady=5)
        ttk.Label(lf,text="Author Name:").pack(side=tk.LEFT,padx=5) # Default TLabel
        self.y_filter_author = ttk.Entry(lf);self.y_filter_author.pack(side=tk.LEFT,fill=tk.X,expand=True) # Default TEntry
        ttk.Button(lf,text="Filter",command=self.filter_youtube_by_author).pack(side=tk.LEFT,padx=5) # Default TButton
        # Tree
        cols=("author","time","likes","text")
        self.y_ops_tree=ttk.Treeview(frame,columns=cols,show='headings', style="Treeview") # Apply Treeview
        for c in cols: # Treeview.Heading style applies
            self.y_ops_tree.heading(c,text=c.capitalize())
            self.y_ops_tree.column(c,width=150 if c=='text' else 80,anchor='w')
        vsb=ttk.Scrollbar(frame,orient='vertical',command=self.y_ops_tree.yview)
        self.y_ops_tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right',fill='y')
        self.y_ops_tree.pack(fill=tk.BOTH,expand=True)

    def populate_youtube_user_ops(self, comments):
        """Populate the user operations tab tree with all comments and replies"""
        self.y_ops_tree.delete(*self.y_ops_tree.get_children())

        # Add main comments
        for i, c in enumerate(comments):
            txt = c['text'][:100] + ('...' if len(c['text']) > 100 else '')
            self.y_ops_tree.insert('', 'end', values=(c['author'], c['time'], c['likes'], txt))

            # Add replies if they exist
            if 'replies' in c and c['replies']:
                for reply in c['replies']:
                    reply_txt = reply['text'][:100] + ('...' if len(reply['text']) > 100 else '')
                    self.y_ops_tree.insert('', 'end', values=(
                        f"↪ {reply['author']} (reply to {c['author']})",
                        reply['time'],
                        reply['likes'],
                        reply_txt
                    ))

    def update_setup_youtube_scraper_tab(self):
        """Update the YouTube scraper tab with additional functionality buttons"""
        # Find the button frame - assume it's the second packed widget in the scraper tab
        btn_frame = None
        for widget in self.y_scraper_tab.winfo_children():
            if isinstance(widget, ttk.Frame):
                for inner_widget in widget.winfo_children():
                    if isinstance(inner_widget, ttk.Frame) and not isinstance(inner_widget, ttk.LabelFrame):
                        btn_frame = inner_widget
                        break

        if not btn_frame:
            # If not found, we'll create a new button frame
            frame = self.y_scraper_tab.winfo_children()[0]  # Get the main frame
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(fill=tk.X, pady=10)

        # Add new action buttons
        ttk.Button(btn_frame, text="Open in Browser", command=self.open_youtube_in_browser).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Comment Stats", command=self.show_youtube_comment_count).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Download Photos", command=self.download_profile_photos).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Analyze", command=self.analyze_youtube_comments).pack(side=tk.LEFT, padx=5)

    def update_youtube_ui_to_add_missing_functions(self):
        """Add missing buttons and context menu binding."""
        # 1) Add action buttons to the scraper tab:
        self.update_setup_youtube_scraper_tab()

        # 2) Bind right-click on the pretty-view tree to our new context menu:
        self.y_tree.bind("<Button-3>", self.show_youtube_context_menu)
        self.y_tree.bind("<Button-2>", self.show_youtube_context_menu) 

        # 3) Ensure necessary imports flag (no change)
        try:
            from textblob import TextBlob
            self.has_textblob = True
        except ImportError:
            self.has_textblob = False

    def sort_youtube_treeview(self, column):
        # Get all items in the treeview
        items = [(self.y_tree.set(item, column), item) for item in self.y_tree.get_children('')]

        # Special sorting for likes (convert to int)
        if column == "likes":
            try:
                items = []
                for item in self.y_tree.get_children(''):
                    like_text = self.y_tree.set(item, column)
                    # Convert YouTube-style counts (5K, 12B, etc.) to integers
                    like_value = self._convert_youtube_count_to_int(like_text)
                    items.append((like_value, item))
            except ValueError:
                # If conversion fails, fall back to string sorting
                items = [(self.y_tree.set(item, column), item) for item in self.y_tree.get_children('')]

        # Sort based on direction
        items.sort(reverse=(self.y_sort_direction.get() == "Descending"))

        # Rearrange items in sorted order
        for index, (val, item) in enumerate(items):
            self.y_tree.move(item, '', index)

    def update_youtube_ui(self, comments):
            if not comments:
                self.y_status.set("No comments found. Try increasing scroll times.")
                self.y_progress['value'] = 100
                return

            # Count total comments including replies
            total_comments = len(comments)
            reply_count = sum(len(c.get('replies', [])) for c in comments)

            if reply_count > 0:
                self.y_status.set(f"Done: {total_comments} main comments + {reply_count} replies")
            else:
                self.y_status.set(f"Done: {total_comments} comments")

            self.y_progress['value'] = 100
            self.youtube_comments = comments
            self.y_save_button.config(state=tk.NORMAL)
            self.y_results_text.insert(tk.END, json.dumps(comments, indent=2))

            # populate pretty view
            self.populate_youtube_pretty(comments)
            # Also populate the user ops view
            self.populate_youtube_user_ops(comments)
            self.youtube_notebook.select(self.y_pretty_tab)


#---------------------------------------#

    def start_youtube_scraping(self):
        """Starts the YouTube scraping process based on selected mode."""
        self.y_results_text.delete(1.0, tk.END)
        self.y_progress['value'] = 0
        self.y_save_button.config(state=tk.DISABLED)
        self.youtube_comments = []

        include_replies = self.y_include_replies.get()
        include_photos = self.y_include_photos.get()
        scroll_times = max(1, self.y_scroll_var.get()) # Common for all modes that scrape individual videos

        self.scraping_paused = False
        self.scraping_stopped = False
        self.y_scrape_button.config(state=tk.DISABLED)
        self.y_pause_button.config(state=tk.NORMAL)
        self.y_stop_button.config(state=tk.NORMAL)

        selected_mode = self.y_scrape_mode_var.get()

        if selected_mode == "channel":
            channel_url = self.y_channel_entry.get().strip()
            if not channel_url:
                messagebox.showerror("Error", "Please enter a YouTube Channel URL")
                self._reset_scraping_buttons()
                return

            video_limit_str = self.y_channel_limit_var.get().strip()
            video_limit = None
            if video_limit_str.lower() == 'all':
                video_limit = 'all'
            else:
                try:
                    video_limit = int(video_limit_str)
                    if video_limit <= 0:
                        messagebox.showerror("Error", "Number of videos must be 'all' or a positive number.")
                        self._reset_scraping_buttons()
                        return
                except ValueError:
                    messagebox.showerror("Error", "Invalid number of videos. Must be 'all' or a number.")
                    self._reset_scraping_buttons()
                    return

            self.y_status.set(f"Getting video links from channel: {channel_url}")
            self.scraping_thread = threading.Thread(
                target=self.youtube_channel_scrape_thread,
                args=(channel_url, video_limit, include_replies, include_photos)
            )
            self.scraping_thread.daemon = True
            self.scraping_thread.start()

        elif selected_mode == "list":
            list_file_path = self.y_list_file_entry.get().strip()
            if not list_file_path:
                messagebox.showerror("Error", "Please select a URL list file (.txt).")
                self._reset_scraping_buttons()
                return
            if not os.path.exists(list_file_path):
                messagebox.showerror("Error", f"File not found: {list_file_path}")
                self._reset_scraping_buttons()
                return

            try:
                with open(list_file_path, 'r', encoding='utf-8') as f:
                    urls_from_file = [line.strip() for line in f if line.strip()]
                if not urls_from_file:
                    messagebox.showinfo("Info", "The selected file is empty or contains no valid URLs.")
                    self._reset_scraping_buttons()
                    return
            except Exception as e:
                messagebox.showerror("Error", f"Could not read file {list_file_path}: {e}")
                self._reset_scraping_buttons()
                return

            valid_urls = []
            for u in urls_from_file:
                is_valid, normalized_url_or_msg = self.validate_youtube_url(u)
                if is_valid:
                    valid_urls.append(normalized_url_or_msg)
                else:
                    print(f"Skipping invalid URL from list: {u} ({normalized_url_or_msg})") # Log to console

            if not valid_urls:
                messagebox.showinfo("Info", "No valid YouTube video URLs found in the list file.")
                self._reset_scraping_buttons()
                return

            self.y_status.set(f"Starting to scrape {len(valid_urls)} videos from list file...")
            self.scraping_thread = threading.Thread(
                target=self.youtube_list_scrape_thread,
                args=(valid_urls, scroll_times, include_replies, include_photos)
            )
            self.scraping_thread.daemon = True
            self.scraping_thread.start()

        else: # Default is "video" (single video)
            video_url = self.y_url_entry.get().strip()
            is_valid, normalized_url_or_msg = self.validate_youtube_url(video_url)
            if not is_valid:
                messagebox.showerror("Error", normalized_url_or_msg)
                self._reset_scraping_buttons()
                return
            video_url = normalized_url_or_msg # Use normalized URL

            status_msg = "Launching browser to scrape single video..."
            if include_replies: status_msg += " (including replies...)"
            if include_photos: status_msg += " (including profile photos...)"
            self.y_status.set(status_msg)

            self.scraping_thread = threading.Thread(
                target=self.youtube_scrape_thread,
                args=(video_url, scroll_times, include_replies, include_photos)
            )
            self.scraping_thread.daemon = True
            self.scraping_thread.start()

    def youtube_scrape_thread(self, url, scroll_times, include_replies=False, include_photos=False):
        driver = None
        try:
            # Setup WebDriver
            opts = uc.ChromeOptions()
            if not self.y_debug_mode_var.get(): # Check if Debug Mode is OFF
                opts.add_argument("--headless")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            driver = uc.Chrome(options=opts)
            driver.get(url)

            # Set up waits
            short_wait = WebDriverWait(driver, 3)
            medium_wait = WebDriverWait(driver, 5)

            # Update progress - initial loading (10%)
            self.master.after(0, lambda: self.y_progress.configure(value=10))
            self.master.after(0, lambda: self.y_status.set("Page loaded, scrolling to comments..."))

            # Wait for page to be fully loaded
            try:
                short_wait.until(EC.presence_of_element_located((By.TAG_NAME, "video")))
            except TimeoutException:
                short_wait.until(EC.presence_of_element_located((By.ID, "content")))

            # Handle cookie banners
            self._handle_cookie_banners(driver, short_wait)

            # Check if stopped before continuing
            if self.scraping_stopped:
                raise Exception("Scraping was stopped by user")

            # Calculate progress allocations
            scrolling_weight, replies_weight, processing_weight = self._calculate_progress_weights(include_replies)

            # Scroll to load comments
            self._scroll_for_comments(driver, scroll_times, scrolling_weight)

            # Check if stopped before continuing
            if self.scraping_stopped:
                raise Exception("Scraping was stopped by user")

            # Expand reply sections if needed
            if include_replies:
                replies_progress_start = 10 + scrolling_weight
                self._expand_replies(driver, short_wait, replies_progress_start, replies_weight)

            # Check if stopped before continuing
            if self.scraping_stopped:
                raise Exception("Scraping was stopped by user")

            # Process comments
            comments_processing_start = 10 + scrolling_weight + (replies_weight if include_replies else 0)
            comments = self._process_comments(driver, include_replies, include_photos, comments_processing_start,
                                              processing_weight)

            # Set progress to 100% at the end of processing
            self.master.after(0, lambda: self.y_progress.configure(value=100))
            if driver:
                driver.quit()

            # Only update UI if not stopped
            if not self.scraping_stopped:
                self.master.after(0, lambda: self.update_youtube_ui(comments))

            # Reset UI buttons regardless of completion status
            self.master.after(0, self._reset_scraping_buttons)

        except Exception as e:
            print(f"Major error: {str(e)}")
            self.master.after(0, lambda: self.y_status.set(f"Error: {str(e)}"))
            if driver:
                driver.quit()
            self.master.after(0, self._reset_scraping_buttons)

    def _handle_cookie_banners(self, driver, short_wait):
        """Handle cookie consent banners if present."""
        try:
            cookie_buttons = driver.find_elements(By.XPATH,
                                                  "//button[contains(., 'Accept') or contains(., 'I agree') or contains(., 'Accept all')]")
            if cookie_buttons:
                cookie_buttons[0].click()
                try:
                    short_wait.until(
                        EC.invisibility_of_element_located((By.XPATH, "//div[contains(@class, 'cookie-banner')]")))
                except TimeoutException:
                    pass  # Continue anyway
        except:
            pass

    def _calculate_progress_weights(self, include_replies):
        """Calculate progress weights for each phase."""
        if include_replies:
            # 10% - Initial loading, 30% - Scrolling, 25% - Expanding replies, 35% - Processing comments
            return 30, 25, 35
        else:
            # 10% - Initial loading, 40% - Scrolling, 50% - Processing comments
            return 40, 0, 50

    def _scroll_for_comments(self, driver, scroll_times, scrolling_weight):
        """Scroll to load more comments, with a smoother initial scroll to find the comments section."""
        self.master.after(0, lambda: self.y_status.set("Initiating scroll to comments section..."))

        # --- Phase 1: Gently scroll to find and reveal the comments section ---
        comments_section_found = False
        for attempt in range(5): # Try a few times to find comments section
            if self.scraping_stopped: return

            # Scroll down by viewport height
            driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(0.4 + attempt * 0.2) # Increasingly longer pauses for page to load

            try:
                # Try to find the comments container
                comments_container = None
                try:
                    comments_container = driver.find_element(By.ID, "comments")
                except NoSuchElementException:
                    try:
                        comments_container = driver.find_element(By.CSS_SELECTOR, "ytd-comments")
                    except NoSuchElementException:
                        pass # Continue scrolling if not found yet

                if comments_container and comments_container.is_displayed():
                    # Scroll the found comments container into view if not already
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});", comments_container)
                    time.sleep(1.0) # Wait for it to settle
                    comments_section_found = True
                    self.master.after(0, lambda: self.y_status.set("Comments section located. Proceeding to load comments."))
                    break # Exit loop once comments section is visible
            except Exception as e_find_comments:
                print(f"Minor issue during initial scroll for comments section: {e_find_comments}")
                # Continue trying

            if self.scraping_stopped: return
            while self.scraping_paused and not self.scraping_stopped: time.sleep(0.5)
            if self.scraping_stopped: return


        if not comments_section_found:
            self.master.after(0, lambda: self.y_status.set("Could not definitively locate comments section, attempting general scroll..."))
            # Fallback: if comments section not explicitly found, do a couple more general scrolls
            for _ in range(2):
                driver.execute_script("window.scrollBy(0, window.innerHeight * 0.8);")
                time.sleep(1.0)
                if self.scraping_stopped: return

        # --- Phase 2: Continue scrolling to load more comments (as before) ---
        self.master.after(0, lambda: self.y_status.set(f"Scrolling to load comments ({scroll_times} times)..."))
        for idx in range(scroll_times):
            if self.scraping_stopped: return
            while self.scraping_paused and not self.scraping_stopped:
                time.sleep(0.5)
            if self.scraping_stopped: return

            # Scroll down a bit more to trigger loading of new comments
            # Using a smaller, consistent scroll amount here
            driver.execute_script("window.scrollBy(0, 800);") # Or window.innerHeight * 0.75

            # Wait for new comments to load or a spinner to appear/disappear
            try:
                # Check current number of main comment threads
                # This can be a bit flaky if the structure changes, but good as a heuristic
                current_main_comments = driver.find_elements(By.CSS_SELECTOR, "ytd-comment-thread-renderer")
                old_comment_count = len(current_main_comments)

                # Wait for a brief moment to allow new content to start loading
                time.sleep(0.4) # Slightly longer than before to allow network requests

                # Wait for either new comments to appear or a loading spinner to disappear (or timeout)
                wait_for_load_start_time = time.time()
                max_wait_for_load_time = 4 # seconds

                while time.time() - wait_for_load_start_time < max_wait_for_load_time:
                    if self.scraping_stopped: return
                    while self.scraping_paused and not self.scraping_stopped: time.sleep(0.5)
                    if self.scraping_stopped: return

                    new_main_comments = driver.find_elements(By.CSS_SELECTOR, "ytd-comment-thread-renderer")
                    new_comment_count = len(new_main_comments)

                    spinner_visible = False
                    try:
                        spinner = driver.find_element(By.CSS_SELECTOR, "paper-spinner[active], tp-yt-paper-spinner[active]")
                        if spinner.is_displayed():
                            spinner_visible = True
                    except NoSuchElementException:
                        spinner_visible = False # Spinner not present or not active

                    if new_comment_count > old_comment_count or not spinner_visible:
                        # Either more comments loaded, or no active spinner is visible (implying load finished or nothing to load)
                        break
                    time.sleep(0.3) # Check periodically

            except Exception as e:
                print(f"Minor error during comment load wait after scroll {idx+1}: {e}")
                time.sleep(0.5) # Fallback sleep if checks fail

            # Update progress based on allocated weight (if scrolling_weight is > 0)
            if scrolling_weight > 0:
                pct = 10 + ((idx + 1) * scrolling_weight / scroll_times)
                self.master.after(0, lambda v=pct: self.y_progress.configure(value=v))
            self.master.after(0, lambda i=idx: self.y_status.set(f"Scrolling... {i + 1}/{scroll_times}"))

        # Final wait for any remaining spinners to disappear after all scrolling
        try:
            WebDriverWait(driver, 4).until_not( # Increased timeout slightly
                EC.presence_of_element_located((By.CSS_SELECTOR, "paper-spinner[active], tp-yt-paper-spinner[active]"))
            )
        except TimeoutException:
            self.master.after(0, lambda: self.y_status.set("Final comment load wait timed out (spinner might persist)."))
            pass
        time.sleep(0.5) # Extra brief pause

    def _expand_replies(self, driver, short_wait, replies_progress_start, replies_weight):
        """Expand reply sections to load all replies."""
        self.master.after(0, lambda: self.y_status.set(f"Finding and expanding reply sections..."))
        self.master.after(0, lambda v=replies_progress_start: self.y_progress.configure(value=v))

        expanded_count = 0

        try:
            # First find all "Show replies" buttons, then find "Load more replies" buttons
            for expansion_round in range(3):  # Try 3 rounds of expansion

                if self.scraping_stopped:
                    return
                while self.scraping_paused and not self.scraping_stopped:
                    time.sleep(0.5)  # Sleep while paused

                self.master.after(0, lambda round=expansion_round:
                self.y_status.set(f"Expanding replies (round {round + 1}/3)..."))

                # STEP 1: First find the initial "Show replies" buttons (already working well)
                if expansion_round == 0:
                    # Use existing code to find initial reply buttons (this part works correctly)
                    reply_buttons = driver.find_elements(By.CSS_SELECTOR,
                                                         "button.yt-spec-button-shape-next--call-to-action, ytd-button-renderer#more-replies")

                # STEP 2: For subsequent rounds, focus on "Load more replies" buttons with the arrow icon
                else:
                    # Find "Load more replies" buttons specifically by their arrow icon SVG path
                    # This targets the exact structure you provided in your description
                    reply_buttons = driver.execute_script("""
                        function findLoadMoreRepliesButtons() {
                            const buttons = [];

                            // Target buttons containing the SVG path for loading more replies
                            // This looks for the specific arrow icon in the right direction
                            const svgPaths = document.querySelectorAll('svg path[d="M19 15l-6 6-1.42-1.42L15.17 16H4V4h2v10h9.17l-3.59-3.58L13 9l6 6z"]');

                            for (const path of svgPaths) {
                                // Navigate up to find the actual button element
                                const button = path.closest('button');
                                if (button) {
                                    buttons.push(button);
                                }
                            }

                            // Also look for continuation buttons in reply sections
                            const continuationButtons = document.querySelectorAll(
                                'ytd-comment-replies-renderer ytd-continuation-item-renderer button'
                            );

                            for (const button of continuationButtons) {
                                buttons.push(button);
                            }

                            return buttons;
                        }

                        return findLoadMoreRepliesButtons();
                    """)

                # Process buttons
                total_buttons = len(reply_buttons)
                round_expanded = 0

                self.master.after(0, lambda count=total_buttons:
                self.y_status.set(f"Found {count} reply buttons to expand in round {expansion_round + 1}"))

                for i, button in enumerate(reply_buttons):

                    if self.scraping_stopped:
                        return
                    while self.scraping_paused and not self.scraping_stopped:
                        time.sleep(0.5)  # Sleep while paused

                    try:
                        # Update progress periodically
                        if i % 5 == 0:
                            progress = replies_progress_start + ((i / max(1, total_buttons)) * (replies_weight * 0.7))
                            self.master.after(0, lambda val=i, tot=total_buttons:
                            self.y_status.set(f"Expanding replies {val}/{tot} in round {expansion_round + 1}..."))
                            self.master.after(0, lambda v=progress: self.y_progress.configure(value=v))

                        # Skip already expanded buttons (using existing code)
                        try:
                            already_expanded = driver.execute_script("""
                                function checkExpanded(btn) {
                                    // Check button itself
                                    if (btn.getAttribute('aria-expanded') === 'true') return true;

                                    // Check parent element
                                    let parent = btn.closest('[aria-expanded="true"]');
                                    if (parent) return true;

                                    // Check if button is inside an already expanded section
                                    let container = btn.closest('ytd-comment-thread-renderer');
                                    if (container) {
                                        // For "Load more replies" buttons, check if it's already been clicked
                                        // by looking for its disabled state or "loading" class
                                        if (btn.disabled || btn.classList.contains('loading') || 
                                            btn.getAttribute('aria-busy') === 'true') {
                                            return true;
                                        }
                                    }

                                    return false;
                                }
                                return checkExpanded(arguments[0]);
                            """, button)

                            if already_expanded:
                                continue
                        except:
                            pass

                        # First scroll to button
                        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                        time.sleep(0.2)  # Wait for scroll to complete

                        # Try multiple clicking methods to ensure success
                        clicked = False

                        # Method 1: Direct click
                        try:
                            button.click()
                            clicked = True
                        except:
                            pass

                        # Method 2: JS click if direct click fails
                        if not clicked:
                            try:
                                driver.execute_script("arguments[0].click();", button)
                                clicked = True
                            except:
                                pass

                        # Method 3: More comprehensive JS click if needed
                        if not clicked:
                            try:
                                driver.execute_script("""
                                    function clickButton(btn) {
                                        // Try regular click
                                        try { btn.click(); return true; } catch(e) {}

                                        // Try clicking any inner elements
                                        const clickables = btn.querySelectorAll('yt-formatted-string, span, div');
                                        for (let el of clickables) {
                                            try { el.click(); return true; } catch(e) {}
                                        }

                                        // Try simulated click event
                                        try {
                                            const rect = btn.getBoundingClientRect();
                                            const eventOptions = {
                                                bubbles: true,
                                                cancelable: true,
                                                view: window,
                                                clientX: rect.left + rect.width/2,
                                                clientY: rect.top + rect.height/2
                                            };

                                            btn.dispatchEvent(new MouseEvent('click', eventOptions));
                                            return true;
                                        } catch(e) {}

                                        return false;
                                    }
                                    return clickButton(arguments[0]);
                                """, button)
                                clicked = True
                            except:
                                pass

                        if not clicked:
                            continue

                        # Verify expansion was successful and wait for loading to complete
                        time.sleep(0.3)  # Wait for expansion to start

                        # Look for loading indicators
                        try:
                            loading = driver.execute_script("""
                                let container = arguments[0].closest('ytd-comment-thread-renderer');
                                if (container) {
                                    // Check for spinners
                                    let spinner = container.querySelector('paper-spinner, tp-yt-paper-spinner');
                                    if (spinner) return true;

                                    // Check for expanding reply section
                                    let repliesSection = container.querySelector('ytd-comment-replies-renderer[is-expanded="true"]');
                                    if (repliesSection) return true;

                                    // Check if the button is being replaced with a loading animation
                                    if (arguments[0].getAttribute('aria-busy') === 'true' || 
                                        arguments[0].classList.contains('loading')) {
                                        return true;
                                    }
                                }
                                return false;
                            """, button)

                            if loading:
                                expanded_count += 1
                                round_expanded += 1

                                # Wait for spinner to disappear (but not too long)
                                try:
                                    # Find the comment thread containing this button
                                    thread = driver.execute_script(
                                        "return arguments[0].closest('ytd-comment-thread-renderer');",
                                        button
                                    )

                                    if thread:
                                        # Wait for spinner to disappear within this thread
                                        spinner = thread.find_elements(By.CSS_SELECTOR,
                                                                       "paper-spinner, tp-yt-paper-spinner")
                                        if spinner:
                                            # Use a short wait to avoid getting stuck
                                            WebDriverWait(driver, 2).until_not(
                                                EC.visibility_of(spinner[0])
                                            )
                                except:
                                    # If waiting for spinner fails, just sleep briefly
                                    time.sleep(0.5)
                            else:
                                # Even if we didn't detect a loading indicator, give it a chance to load
                                time.sleep(0.3)
                        except:
                            # If checking loading failed, just wait
                            time.sleep(0.3)

                    except Exception as e:
                        print(f"Error with button {i} in round {expansion_round + 1}: {e}")
                        continue

                # Wait for all content to stabilize before starting next round
                try:
                    short_wait.until_not(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "paper-spinner, tp-yt-paper-spinner"))
                    )
                except TimeoutException:
                    pass

                time.sleep(1.0)  # Additional wait for UI stability between rounds

                # Update on this round's progress
                self.master.after(0, lambda count=round_expanded:
                self.y_status.set(f"Expanded {count} replies in round {expansion_round + 1}"))

                # If no expansions in this round, stop trying
                if round_expanded == 0:
                    break

            # After all rounds, update progress
            final_progress = replies_progress_start + replies_weight
            self.master.after(0, lambda v=final_progress: self.y_progress.configure(value=v))
            self.master.after(0, lambda count=expanded_count:
            self.y_status.set(f"Expanded {count} reply sections, waiting for content to load..."))

            # Final wait for content to load
            time.sleep(1.0)

        except Exception as e:
            print(f"Error in reply expansion: {e}")

    def _process_comments(self, driver, include_replies, include_photos, comments_processing_start, processing_weight):
        """Process comments and extract data."""
        # Find comment sections
        comment_sections = driver.find_elements(By.CSS_SELECTOR, 'ytd-comment-thread-renderer')
        if not comment_sections:
            comment_sections = driver.find_elements(By.CSS_SELECTOR, '#comments #content')

        total_sections = len(comment_sections)
        self.master.after(0, lambda: self.y_status.set(f"Processing {total_sections} comment sections..."))

        comments = []

        # Process each comment section
        for i, section in enumerate(comment_sections):
            # Update progress
            if i % 10 == 0:
                progress_value = comments_processing_start + ((i / max(1, total_sections)) * processing_weight)
                self.master.after(0, lambda val=i, tot=total_sections:
                self.y_status.set(f"Processing comments... {val}/{tot}"))
                self.master.after(0, lambda val=progress_value:
                self.y_progress.configure(value=val))

            try:
                # Extract comment data using helper JavaScript function
                comment_data = driver.execute_script("""
                    function extractCommentData(section) {
                        // Extract author
                        let author = "Unknown";
                        const authorElement = section.querySelector('#author-text, h3.ytd-comment-renderer a');
                        if (authorElement) {
                            author = authorElement.textContent.trim();
                        }

                        // Extract text
                        let text = "(No text)";
                        const textElement = section.querySelector('#content-text, yt-formatted-string#content-text');
                        if (textElement) {
                            text = textElement.textContent.trim();
                        }

                        // Extract time
                        let time = "";
                        const timeElement = section.querySelector('#published-time-text a, .published-time-text a');
                        if (timeElement) {
                            time = timeElement.textContent.trim();
                        }

                        // Extract likes
                        let likes = "0";
                        const likesElement = section.querySelector('#vote-count-middle, span.like-count');
                        if (likesElement) {
                            likes = likesElement.textContent.trim();
                        }

                        return {author, text, time, likes};
                    }

                    return extractCommentData(arguments[0]);
                """, section)

                # Add profile photo if requested
                if include_photos:
                    profile_photo = ""
                    try:
                        img_elem = section.find_element(By.CSS_SELECTOR, 'img#img')
                        profile_photo = img_elem.get_attribute('src')
                        if profile_photo:
                            comment_data['profile_photo'] = profile_photo
                    except:
                        pass

                # Only add comments with valid data
                if comment_data['author'] != "Unknown" or comment_data['text'] != "(No text)":
                    # Add empty replies list
                    comment_data['replies'] = []

                    # Process replies if requested
                    if include_replies:
                        try:
                            # First, check if there's a replies section and if it's expanded
                            replies_section = section.find_elements(By.CSS_SELECTOR, 'ytd-comment-replies-renderer')

                            if replies_section:
                                # Updated approach using the structure you provided
                                # Try multiple possible selectors for replies
                                replies = []

                                # Method 1: Using ytd-comment-view-model (new YouTube UI)
                                reply_elements = section.find_elements(By.CSS_SELECTOR,
                                                                       'ytd-comment-replies-renderer ytd-comment-view-model')

                                # If no results, try alternative selector
                                if not reply_elements:
                                    # Method 2: Using ytd-comment-renderer (older YouTube UI)
                                    reply_elements = section.find_elements(By.CSS_SELECTOR,
                                                                           'ytd-comment-replies-renderer ytd-comment-renderer')

                                # If still no results, try another alternative
                                if not reply_elements:
                                    # Method 3: Try a more general approach using any visible comments inside replies
                                    reply_elements = section.find_elements(By.CSS_SELECTOR,
                                                                           'ytd-comment-replies-renderer #contents > *')

                                # Log the number of reply elements found
                                print(f"Found {len(reply_elements)} reply elements for comment {i}")

                                # Process each reply element
                                for reply_elem in reply_elements:
                                    try:
                                        # Extract reply data using JS for better reliability
                                        reply_data = driver.execute_script("""
                                            function extractReplyData(reply) {
                                                // Extract author with multiple fallback options
                                                let author = "Unknown";
                                                const authorSelectors = [
                                                    '#author-text', 
                                                    'a[id="author-text"]', 
                                                    '#header-author yt-formatted-string.ytd-comment-renderer',
                                                    'a.yt-simple-endpoint[href*="channel"]',
                                                    'yt-formatted-string#author-name',
                                                    'span.ytd-channel-name'
                                                ];

                                                for (const selector of authorSelectors) {
                                                    const element = reply.querySelector(selector);
                                                    if (element && element.textContent.trim()) {
                                                        author = element.textContent.trim();
                                                        break;
                                                    }
                                                }

                                                // Extract text with multiple fallback options
                                                let text = "(No text)";
                                                const textSelectors = [
                                                    '#content-text', 
                                                    'yt-formatted-string#content-text',
                                                    '#comment-content',
                                                    'div#content'
                                                ];

                                                for (const selector of textSelectors) {
                                                    const element = reply.querySelector(selector);
                                                    if (element && element.textContent.trim()) {
                                                        text = element.textContent.trim();
                                                        break;
                                                    }
                                                }

                                                // Extract time
                                                let time = "";
                                                const timeSelectors = [
                                                    '#published-time-text a', 
                                                    '.published-time-text a',
                                                    'yt-formatted-string.ytd-comment-renderer[class*="time"]'
                                                ];

                                                for (const selector of timeSelectors) {
                                                    const element = reply.querySelector(selector);
                                                    if (element && element.textContent.trim()) {
                                                        time = element.textContent.trim();
                                                        break;
                                                    }
                                                }

                                                // Extract likes
                                                let likes = "0";
                                                const likesSelectors = [
                                                    '#vote-count-middle', 
                                                    'span.like-count',
                                                    '.vote-count-left'
                                                ];

                                                for (const selector of likesSelectors) {
                                                    const element = reply.querySelector(selector);
                                                    if (element && element.textContent.trim()) {
                                                        likes = element.textContent.trim();
                                                        break;
                                                    }
                                                }

                                                return {author, text, time, likes};
                                            }

                                            return extractReplyData(arguments[0]);
                                        """, reply_elem)

                                        # Add profile photo if requested
                                        if include_photos:
                                            try:
                                                img_elem = reply_elem.find_element(By.CSS_SELECTOR, 'img#img')
                                                reply_data['profile_photo'] = img_elem.get_attribute('src')
                                            except:
                                                pass

                                        # Only add replies with valid data
                                        if reply_data['author'] != "Unknown" or reply_data['text'] != "(No text)":
                                            replies.append(reply_data)
                                    except Exception as e:
                                        print(f"Error processing individual reply: {e}")
                                        continue

                                comment_data['replies'] = replies

                        except Exception as e:
                            print(f"Error processing replies for comment {i}: {e}")

                    comments.append(comment_data)

            except Exception as e:
                print(f"Error processing comment: {e}")
                continue

        return comments

    def youtube_list_scrape_thread(self, url_list, scroll_times, include_replies, include_photos):
        driver = None
        all_comments_from_list = []
        num_videos_to_scrape = len(url_list)

        try:
            opts = uc.ChromeOptions()
            if not self.y_debug_mode_var.get(): # Check if Debug Mode is OFF
                opts.add_argument("--headless")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            driver = uc.Chrome(options=opts)
            # short_wait will be initialized inside the loop for each video

            self.master.after(0, lambda: self.y_progress.configure(value=5))

            for i, video_url in enumerate(url_list):
                if self.scraping_stopped:
                    self.master.after(0, lambda: self.y_status.set("List scraping stopped by user."))
                    break

                while self.scraping_paused and not self.scraping_stopped:
                    status_text = f"List scraping paused before video {i+1}/{num_videos_to_scrape}: {video_url.split('v=')[-1]}"
                    self.master.after(0, lambda s=status_text: self.y_status.set(s))
                    time.sleep(0.5)

                if self.scraping_stopped:
                    self.master.after(0, lambda: self.y_status.set("List scraping stopped by user."))
                    break

                base_progress_for_this_video = 5 + (i / num_videos_to_scrape) * 90
                progress_increment_for_this_video = (1 / num_videos_to_scrape) * 90

                video_id_for_status = video_url.split('v=')[-1]
                status_msg = f"Scraping video {i+1}/{num_videos_to_scrape}: {video_id_for_status}"
                self.master.after(0, lambda s=status_msg: self.y_status.set(s))
                self.master.after(0, lambda p=base_progress_for_this_video: self.y_progress.configure(value=p))

                video_title_for_comments = "Unknown Video"
                try:
                    driver.get(video_url)
                    # *** Crucial: Initialize short_wait AFTER driver.get() for the new page ***
                    short_wait = WebDriverWait(driver, 3)

                    try:
                        title_element = WebDriverWait(driver, 7).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.ytd-watch-metadata #video-title, yt-formatted-string.ytd-watch-metadata[slot='title']"))
                        )
                        video_title_for_comments = title_element.text.strip()
                    except TimeoutException:
                        video_title_for_comments = driver.title
                    except Exception as e_title:
                        print(f"Could not get video title for {video_url}: {e_title}")
                        video_title_for_comments = driver.title or "Title N/A"

                    self._handle_cookie_banners(driver, short_wait) # Pass the correctly initialized short_wait
                    if self.scraping_stopped: continue

                    sub_status_1 = f"Scrolling V:{i+1} ({video_title_for_comments[:30]}...)"
                    self.master.after(0, lambda s=sub_status_1: self.y_status.set(s))
                    self._scroll_for_comments(driver, scroll_times, 0)
                    self.master.after(0, lambda p=base_progress_for_this_video + progress_increment_for_this_video * 0.4: self.y_progress.configure(value=p))
                    if self.scraping_stopped: continue

                    if include_replies:
                        sub_status_2 = f"Expanding replies V:{i+1} ({video_title_for_comments[:30]}...)"
                        self.master.after(0, lambda s=sub_status_2: self.y_status.set(s))
                        self._expand_replies(driver, short_wait, 0, 0) # Pass the correctly initialized short_wait
                        self.master.after(0, lambda p=base_progress_for_this_video + progress_increment_for_this_video * 0.7: self.y_progress.configure(value=p))
                        if self.scraping_stopped: continue

                    sub_status_3 = f"Processing comments V:{i+1} ({video_title_for_comments[:30]}...)"
                    self.master.after(0, lambda s=sub_status_3: self.y_status.set(s))
                    comments_for_this_video = self._process_comments(driver, include_replies, include_photos, 0, 0)

                    for comment_obj in comments_for_this_video:
                        comment_obj['video_url'] = video_url
                        comment_obj['video_title'] = video_title_for_comments
                    all_comments_from_list.extend(comments_for_this_video)

                    self.master.after(0, lambda p=base_progress_for_this_video + progress_increment_for_this_video: self.y_progress.configure(value=p))

                except Exception as e_video:
                    error_msg = f"Error on video {video_id_for_status}: {str(e_video)[:100]}"
                    print(f"Error scraping video {video_url}: {e_video}")
                    self.master.after(0, lambda s=error_msg: self.y_status.set(s))
                    time.sleep(1)

            if driver:
                driver.quit()
                driver = None

            final_progress = 95
            self.master.after(0, lambda p=final_progress: self.y_progress.configure(value=p))

            if not self.scraping_stopped:
                if all_comments_from_list:
                    status_final = f"List scrape complete. Total comments from {num_videos_to_scrape} videos: {len(all_comments_from_list)}"
                    self.master.after(0, lambda s=status_final: self.y_status.set(s))
                    self.master.after(0, lambda: self.update_youtube_ui(all_comments_from_list))
                else:
                    self.master.after(0, lambda: self.y_status.set("List scrape complete. No comments found in processed videos."))
                    self.master.after(0, lambda: messagebox.showinfo("List Scrape Complete", "No comments found in the processed videos from the list."))
            else:
                status_stopped_final = f"List scraping stopped. {len(all_comments_from_list)} comments collected."
                self.master.after(0, lambda s=status_stopped_final: self.y_status.set(s))
                if all_comments_from_list:
                    self.master.after(0, lambda: self.update_youtube_ui(all_comments_from_list))

            self.master.after(0, lambda: self.y_progress.configure(value=100))

        except Exception as e_list_main:
            error_list_final = f"List Scrape Main Error: {str(e_list_main)[:150]}"
            print(f"Major error in youtube_list_scrape_thread: {e_list_main}")
            import traceback
            traceback.print_exc()
            self.master.after(0, lambda s=error_list_final: self.y_status.set(s))
            if driver:
                driver.quit()
        finally:
            if driver:
                driver.quit()
            self.master.after(0, self._reset_scraping_buttons)

    def browse_youtube_list_file(self):
        """Opens a file dialog to select a .txt file containing YouTube URLs."""
        filepath = filedialog.askopenfilename(
            title="Select YouTube URL List File",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filepath:
            self.y_list_file_entry.delete(0, tk.END)
            self.y_list_file_entry.insert(0, filepath)
            self.y_status.set(f"Selected URL list file: {os.path.basename(filepath)}")

    def save_youtube_json(self):
        if not self.youtube_comments:
            return
        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON','*.json')])
        if path:
            with open(path,'w',encoding='utf-8') as f:
                json.dump(self.youtube_comments,f,indent=2)
            self.y_status.set(f"Saved to {path}")

    def clear_youtube(self):
        self.y_results_text.delete(1.0,tk.END)
        self.y_status.set("Ready")
        self.y_progress['value'] = 0
        self.youtube_comments = None



    def show_youtube_comment(self, event):
            """Show detailed comment in the detail text box when selected."""
            selected_item = self.y_tree.selection()

            if not selected_item:
                return

            selected_id = selected_item[0]  # e.g., "c5" or "c5r2"
            parent_tree_id = self.y_tree.parent(selected_id)  # e.g., "" for main comment, "c5" for reply

            try:
                self.y_detail.delete(1.0, tk.END)
                all_comments = self.youtube_comments  # Main data source for full comments

                retrieved_full_data = False

                # Only attempt to retrieve full data if all_comments is populated
                if all_comments:
                    if parent_tree_id:  # It's a reply
                        try:
                            # parent_tree_id is like "c5", selected_id is like "c5r2"
                            parent_idx = int(parent_tree_id[1:])  # Extract index from "c{index}"
                            
                            # selected_id is "c{i}r{j}", reply_idx_str becomes "{j}"
                            reply_idx_str = selected_id.split('r')[-1]
                            reply_idx = int(reply_idx_str)

                            if 0 <= parent_idx < len(all_comments):
                                parent_comment_obj = all_comments[parent_idx]
                                if 'replies' in parent_comment_obj and 0 <= reply_idx < len(parent_comment_obj['replies']):
                                    reply_data_obj = parent_comment_obj['replies'][reply_idx]
                                    
                                    detail_text = f"REPLY TO: {parent_comment_obj.get('author', 'Unknown')}\n\n"
                                    detail_text += f"Author: {reply_data_obj.get('author', 'Unknown')}\n"
                                    detail_text += f"Posted: {reply_data_obj.get('time', '')}\n"
                                    detail_text += f"Likes: {reply_data_obj.get('likes', '0')}\n\n"
                                    detail_text += f"{reply_data_obj.get('text', '(No text)')}"  # Full text
                                    
                                    if 'profile_photo' in reply_data_obj and reply_data_obj.get('profile_photo'):
                                        detail_text += f"\n\nProfile Photo: {reply_data_obj['profile_photo']}"
                                        
                                    self.y_detail.insert(tk.END, detail_text)
                                    retrieved_full_data = True
                                else:
                                    print(f"Debug: Reply data not found. Parent index: {parent_idx}, Reply index: {reply_idx}, Parent has replies: {'replies' in parent_comment_obj}")
                            else:
                                print(f"Debug: Parent index {parent_idx} out of bounds for all_comments (len {len(all_comments)})")
                        except (ValueError, IndexError) as e:
                            print(f"Error parsing reply ID ('{selected_id}', parent '{parent_tree_id}'): {e}")
                    
                    elif not parent_tree_id:  # It's a main comment
                        # Ensure it's not a reply that somehow lost its parent in the tree structure
                        if 'r' not in selected_id:
                            try:
                                # selected_id is like "c5"
                                comment_idx = int(selected_id[1:])  # Extract index from "c{index}"
                                if 0 <= comment_idx < len(all_comments):
                                    main_comment_obj = all_comments[comment_idx]
                                    
                                    detail_text = f"Author: {main_comment_obj.get('author', 'Unknown')}\n"
                                    detail_text += f"Posted: {main_comment_obj.get('time', '')}\n"
                                    detail_text += f"Likes: {main_comment_obj.get('likes', '0')}\n\n"
                                    detail_text += f"{main_comment_obj.get('text', '(No text)')}"  # Full text
                                    
                                    if 'profile_photo' in main_comment_obj and main_comment_obj.get('profile_photo'):
                                        detail_text += f"\n\nProfile Photo: {main_comment_obj['profile_photo']}"
                                        
                                    self.y_detail.insert(tk.END, detail_text)
                                    retrieved_full_data = True
                                else:
                                    print(f"Debug: Comment index {comment_idx} out of bounds for all_comments (len {len(all_comments)})")
                            except (ValueError, IndexError) as e:
                                print(f"Error parsing main comment ID ('{selected_id}'): {e}")
                        else:
                             print(f"Warning: Item '{selected_id}' appears to be a reply (contains 'r') but has no parent_tree_id.")


                if not retrieved_full_data:
                    # Fallback: If full data wasn't retrieved (e.g., all_comments was empty or ID parsing/lookup failed)
                    # Display data from the tree (which might be truncated)
                    print(f"Fallback: Displaying (potentially truncated) data from tree for item {selected_id}")
                    tree_values = self.y_tree.item(selected_id, "values")
                    
                    if not tree_values or len(tree_values) < 4:
                        self.y_detail.insert(tk.END, f"Error: No valid data in tree for item {selected_id}.")
                        return
                    
                    author, time_val, likes, text_preview = tree_values[0], tree_values[1], tree_values[2], tree_values[3]
                    
                    # text_preview is what's shown in the tree; for replies, it includes "[Reply to...] "
                    detail_text = f"Author: {author}\n"  # Author might be "↪ ReplyAuthor"
                    detail_text += f"Posted: {time_val}\n"
                    detail_text += f"Likes: {likes}\n\n"
                    detail_text += f"{text_preview}" # This is the text from the tree cell
                    
                    if not all_comments:
                         detail_text += "\n\n(Note: Original comment data source was not available or empty)"
                    else:
                         detail_text += "\n\n(Note: Full data retrieval failed, showing preview from tree)"
                    self.y_detail.insert(tk.END, detail_text)

            except Exception as e:
                print(f"General error displaying comment details for {selected_id}: {e}")
                import traceback
                traceback.print_exc()  # For more detailed error logging in the console
                self.y_detail.insert(tk.END, f"An error occurred while displaying comment details: {str(e)}")

    def show_profile_photo(self, event):
        """Display the profile photo in a new window when right-clicked on a comment"""
        try:
            # Get the selected item
            sel = self.y_tree.selection()
            if not sel:
                return

            item_id = sel[0]

            # Find the comment data and extract photo URL
            index = int(item_id.split('c')[1].split('r')[0])
            is_reply = 'r' in item_id

            photo_url = None
            if is_reply:
                reply_index = int(item_id.split('r')[1])
                comment = self.youtube_comments[index]['replies'][reply_index]
                if 'profile_photo' in comment:
                    photo_url = comment['profile_photo']
            else:
                comment = self.youtube_comments[index]
                if 'profile_photo' in comment:
                    photo_url = comment['profile_photo']

            if not photo_url:
                messagebox.showinfo("Info", "No profile photo available for this comment.")
                return

            # Create a new window to display the photo
            photo_window = tk.Toplevel(self.master)
            photo_window.title(f"Profile Photo - {comment['author']}")
            photo_window.geometry("300x350")

            # Add details
            ttk.Label(photo_window, text=f"Author: {comment['author']}").pack(pady=5)

            # Try to download and show the image
            try:
                # Use a separate thread to download the image
                def download_and_show():
                    try:
                        response = requests.get(photo_url, stream=True)
                        if response.status_code == 200:
                            # Create a PIL Image
                            from PIL import Image, ImageTk
                            img = Image.open(io.BytesIO(response.content))
                            # Resize if needed
                            img = img.resize((150, 150), Image.LANCZOS)
                            # Convert to PhotoImage
                            photo = ImageTk.PhotoImage(img)

                            # Update UI in main thread
                            photo_window.after(0, lambda: update_ui(photo, img))
                        else:
                            photo_window.after(0, lambda: messagebox.showerror("Error", "Failed to download image"))
                    except Exception as e:
                        photo_window.after(0, lambda: messagebox.showerror("Error", f"Error loading image: {str(e)}"))

                def update_ui(photo, img):
                    nonlocal img_label
                    img_label.config(image=photo)
                    img_label.image = photo  # Keep a reference

                    # Add URL and save button
                    ttk.Label(photo_window, text="Image URL:").pack(pady=5)
                    url_entry = ttk.Entry(photo_window, width=40)
                    url_entry.pack(pady=5)
                    url_entry.insert(0, photo_url)

                    # Save button
                    def save_image():
                        file_path = filedialog.asksaveasfilename(
                            defaultextension=".png",
                            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
                        )
                        if file_path:
                            try:
                                img.save(file_path)
                                messagebox.showinfo("Success", f"Image saved to {file_path}")
                            except Exception as e:
                                messagebox.showerror("Error", f"Failed to save image: {str(e)}")

                    ttk.Button(photo_window, text="Save Image", command=save_image).pack(pady=10)

                # Placeholder for image
                img_label = ttk.Label(photo_window, text="Loading image...")
                img_label.pack(pady=20)

                # Start download thread
                threading.Thread(target=download_and_show, daemon=True).start()

            except Exception as e:
                messagebox.showerror("Error", f"Failed to display image: {str(e)}")

        except Exception as e:
            messagebox.showerror("Error", f"Error showing profile photo: {str(e)}")



    def filter_youtube_by_author(self):
        name = self.y_filter_author.get().strip().lower()
        if not self.youtube_comments:
            messagebox.showinfo("Info", "No comments available. Please scrape comments first.")
            return

        # Search both main comments and replies
        filtered_main = []
        filtered_replies = []

        for c in self.youtube_comments:
            # Check main comment
            if name in c['author'].lower():
                filtered_main.append(c)

            # Check replies
            if 'replies' in c and c['replies']:
                for reply in c['replies']:
                    if name in reply['author'].lower():
                        filtered_replies.append({
                            'parent_author': c['author'],
                            'reply': reply
                        })

        self.y_ops_tree.delete(*self.y_ops_tree.get_children())

        # No results case
        if not filtered_main and not filtered_replies:
            messagebox.showinfo("Info", f"No comments or replies found for author containing '{name}'")
            # Show all comments again
            self.populate_youtube_user_ops(self.youtube_comments)
            return

        # Add main comments
        for i, c in enumerate(filtered_main):
            txt = c['text'][:100] + ('...' if len(c['text']) > 100 else '')
            self.y_ops_tree.insert('', 'end', values=(c['author'], c['time'], c['likes'], txt))

        # Add replies
        for i, item in enumerate(filtered_replies):
            reply = item['reply']
            txt = reply['text'][:100] + ('...' if len(reply['text']) > 100 else '')
            self.y_ops_tree.insert('', 'end', values=(
                f"↪ {reply['author']} (reply to {item['parent_author']})",
                reply['time'],
                reply['likes'],
                txt
            ))

        total_found = len(filtered_main) + len(filtered_replies)
        self.y_status.set(
            f"Found {len(filtered_main)} comments and {len(filtered_replies)} replies by authors containing '{name}'")

    def search_youtube_comments(self):
        query = self.y_search_entry.get().strip().lower()
        column = self.y_search_column.get()

        if not query:
            messagebox.showinfo("Info", "Please enter a search term")
            return

        if not self.youtube_comments:
            messagebox.showinfo("Info", "No comments available. Please scrape comments first.")
            return

        # Clear the tree
        self.y_tree.delete(*self.y_tree.get_children())

        # Track found items
        found_items = []

        for i, comment in enumerate(self.youtube_comments):
            main_match = False

            # Check if the main comment matches
            if column == "All" or column == "Author":
                if query in comment['author'].lower():
                    main_match = True

            if column == "All" or column == "Time":
                if query in comment['time'].lower():
                    main_match = True

            if column == "All" or column == "Likes":
                if query in comment['likes'].lower():
                    main_match = True

            if column == "All" or column == "Text":
                if query in comment['text'].lower():
                    main_match = True

            # Add main comment if it matches
            if main_match:
                txt = comment['text'][:100] + ('...' if len(comment['text']) > 100 else '')
                self.y_tree.insert('', 'end', iid=f"c{i}",
                                   values=(comment['author'], comment['time'], comment['likes'], txt))
                found_items.append({"type": "main", "data": comment})

            # Check replies
            if 'replies' in comment and comment['replies']:
                for j, reply in enumerate(comment['replies']):
                    reply_match = False

                    if column == "All" or column == "Author":
                        if query in reply['author'].lower():
                            reply_match = True

                    if column == "All" or column == "Time":
                        if query in reply['time'].lower():
                            reply_match = True

                    if column == "All" or column == "Likes":
                        if query in reply['likes'].lower():
                            reply_match = True

                    if column == "All" or column == "Text":
                        if query in reply['text'].lower():
                            reply_match = True

                    # Add reply if it matches
                    if reply_match:
                        reply_txt = reply['text'][:100] + ('...' if len(reply['text']) > 100 else '')
                        self.y_tree.insert('', 'end', iid=f"c{i}r{j}",
                                           values=(f"↪ {reply['author']}", reply['time'],
                                                   reply['likes'], f"[Reply to {comment['author']}] {reply_txt}"))
                        found_items.append({"type": "reply", "data": reply, "parent": comment})

        if not found_items:
            messagebox.showinfo("Search Result", f"No comments found containing '{query}'")
            # Reset to show all
            self.populate_youtube_pretty(self.youtube_comments)
        else:
            self.y_status.set(f"Found {len(found_items)} items matching '{query}'")

    def reset_youtube_search(self):
        if self.youtube_comments:
            self.populate_youtube_pretty(self.youtube_comments)
            self.y_search_entry.delete(0, tk.END)
            self.y_search_column.set("All")
            self.y_status.set("Search reset")



    def export_youtube_to_xml(self):
        """Export YouTube comments to XML file"""
        if not self.youtube_comments:
            messagebox.showinfo("Info", "No comments available to export.")
            return

        # Get selected fields for export
        fields = {field: var.get() for field, var in self.y_export_fields.items()}

        path = filedialog.asksaveasfilename(defaultextension='.xml', filetypes=[('XML', '*.xml')])
        if not path:
            return

        try:
            root = ET.Element("youtube_comments")

            for comment in self.youtube_comments:
                comment_elem = ET.SubElement(root, "comment")

                # Add main comment fields based on selection
                if fields["author"]:
                    ET.SubElement(comment_elem, "author").text = comment.get('author', '')
                if fields["time"]:
                    ET.SubElement(comment_elem, "time").text = comment.get('time', '')
                if fields["likes"]:
                    ET.SubElement(comment_elem, "likes").text = comment.get('likes', '0')
                if fields["text"]:
                    ET.SubElement(comment_elem, "text").text = comment.get('text', '')

                # Add replies if selected and if they exist
                if fields["replies"] and 'replies' in comment and comment['replies']:
                    replies_elem = ET.SubElement(comment_elem, "replies")
                    for reply in comment['replies']:
                        reply_elem = ET.SubElement(replies_elem, "reply")
                        if fields["author"]:
                            ET.SubElement(reply_elem, "author").text = reply.get('author', '')
                        if fields["time"]:
                            ET.SubElement(reply_elem, "time").text = reply.get('time', '')
                        if fields["likes"]:
                            ET.SubElement(reply_elem, "likes").text = reply.get('likes', '0')
                        if fields["text"]:
                            ET.SubElement(reply_elem, "text").text = reply.get('text', '')

            # Create XML tree and save
            tree = ET.ElementTree(root)
            tree.write(path, encoding='utf-8', xml_declaration=True)

            self.y_status.set(f"Exported to XML: {path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export XML: {str(e)}")

    def export_youtube_to_json(self):
        """Export YouTube comments to JSON file, but respecting field selection"""
        if not self.youtube_comments:
            messagebox.showinfo("Info", "No comments available to export.")
            return

        # Get selected fields for export
        fields = {field: var.get() for field, var in self.y_export_fields.items()}

        path = filedialog.asksaveasfilename(defaultextension='.json', filetypes=[('JSON', '*.json')])
        if not path:
            return

        try:
            filtered_comments = []

            for comment in self.youtube_comments:
                filtered_comment = {}

                # Add only selected fields
                if fields["author"]:
                    filtered_comment["author"] = comment.get('author', '')
                if fields["time"]:
                    filtered_comment["time"] = comment.get('time', '')
                if fields["likes"]:
                    filtered_comment["likes"] = comment.get('likes', '0')
                if fields["text"]:
                    filtered_comment["text"] = comment.get('text', '')

                # Add replies if selected and if they exist
                if fields["replies"] and 'replies' in comment and comment['replies']:
                    filtered_comment["replies"] = []
                    for reply in comment['replies']:
                        filtered_reply = {}
                        if fields["author"]:
                            filtered_reply["author"] = reply.get('author', '')
                        if fields["time"]:
                            filtered_reply["time"] = reply.get('time', '')
                        if fields["likes"]:
                            filtered_reply["likes"] = reply.get('likes', '0')
                        if fields["text"]:
                            filtered_reply["text"] = reply.get('text', '')
                        filtered_comment["replies"].append(filtered_reply)

                filtered_comments.append(filtered_comment)

            # Save to file
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(filtered_comments, f, indent=2, ensure_ascii=False)

            self.y_status.set(f"Exported to JSON: {path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export JSON: {str(e)}")

    def export_youtube_to_csv(self):
        """Export YouTube comments to CSV file"""
        if not self.youtube_comments:
            messagebox.showinfo("Info", "No comments available to export.")
            return

        # Get selected fields for export
        fields = {field: var.get() for field, var in self.y_export_fields.items()}

        path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV', '*.csv')])
        if not path:
            return

        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as csvfile:
                # Determine which headers to use
                headers = []
                if fields["author"]:
                    headers.append("Author")
                if fields["time"]:
                    headers.append("Time")
                if fields["likes"]:
                    headers.append("Likes")
                if fields["text"]:
                    headers.append("Text")
                if fields["replies"]:
                    headers.append("Is Reply")
                    headers.append("Parent Author")

                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()

                # Write main comments
                for comment in self.youtube_comments:
                    row = {}
                    if fields["author"]:
                        row["Author"] = comment.get('author', '')
                    if fields["time"]:
                        row["Time"] = comment.get('time', '')
                    if fields["likes"]:
                        row["Likes"] = comment.get('likes', '0')
                    if fields["text"]:
                        row["Text"] = comment.get('text', '')
                    if fields["replies"]:
                        row["Is Reply"] = "No"
                        row["Parent Author"] = ""
                    writer.writerow(row)

                    # Write replies if selected and if they exist
                    if fields["replies"] and 'replies' in comment and comment['replies']:
                        for reply in comment['replies']:
                            reply_row = {}
                            if fields["author"]:
                                reply_row["Author"] = reply.get('author', '')
                            if fields["time"]:
                                reply_row["Time"] = reply.get('time', '')
                            if fields["likes"]:
                                reply_row["Likes"] = reply.get('likes', '0')
                            if fields["text"]:
                                reply_row["Text"] = reply.get('text', '')
                            if fields["replies"]:
                                reply_row["Is Reply"] = "Yes"
                                reply_row["Parent Author"] = comment.get('author', '')
                            writer.writerow(reply_row)

            self.y_status.set(f"Exported to CSV: {path}")

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export CSV: {str(e)}")

    def validate_youtube_url(self, url):
        """Validate and normalize YouTube URL"""
        if not url.strip():
            return False, "Please enter a URL"

        # Handle YouTube URL formats
        if "youtube.com" in url or "youtu.be" in url:
            # Convert short URLs
            if "youtu.be" in url:
                video_id = url.split("/")[-1].split("?")[0]
                url = f"https://www.youtube.com/watch?v={video_id}"
            # Handle other formats
            elif "youtube.com" in url and "/watch?v=" not in url:
                if "v=" in url:
                    video_id = url.split("v=")[1].split("&")[0]
                    url = f"https://www.youtube.com/watch?v={video_id}"
                else:
                    return False, "Invalid YouTube URL format"
            return True, url
        else:
            return False, "Not a YouTube URL"

    def open_youtube_in_browser(self):
        """Open the current YouTube video in browser"""
        url = self.y_url_entry.get().strip()
        valid, url_or_msg = self.validate_youtube_url(url)
        if valid:
            webbrowser.open(url_or_msg)
        else:
            messagebox.showerror("Error", url_or_msg)

    def show_youtube_comment_count(self):
        """Display statistics about the comments with robust likes parsing."""
        if not self.youtube_comments:
            messagebox.showinfo("Info", "No comments available. Please scrape comments first.")
            return

        total_comments = len(self.youtube_comments)
        total_replies = sum(len(c.get('replies', [])) for c in self.youtube_comments)

        def parse_likes(likes_str):
            s = likes_str.strip().replace(' ', '')
            if not s:
                return 0
            # detect suffix
            unit = s[-1].upper()
            num = s[:-1] if unit in ('K', 'M', 'B') else s
            try:
                val = float(num)
            except ValueError:
                return 0
            if unit == 'K':
                return int(val * 1_000)
            elif unit == 'M':
                return int(val * 1_000_000)
            elif unit == 'B':
                return int(val * 1_000_000_000)
            else:
                return int(val)

        # gather likes
        main_likes = [parse_likes(c.get('likes', '0')) for c in self.youtube_comments]
        avg_likes = sum(main_likes) / len(main_likes) if main_likes else 0

        # find most active user
        authors = {}
        for c in self.youtube_comments:
            a = c.get('author', 'Unknown')
            authors[a] = authors.get(a, 0) + 1
            for r in c.get('replies', []):
                ra = r.get('author', 'Unknown')
                authors[ra] = authors.get(ra, 0) + 1
        most_active, count = max(authors.items(), key=lambda x: x[1]) if authors else ('Unknown', 0)

        stats = (
            f"Total Comments: {total_comments}\n"
            f"Total Replies: {total_replies}\n"
            f"Average Likes: {avg_likes:.1f}\n"
            f"Most Active User: {most_active} ({count} comments/replies)"
        )
        messagebox.showinfo("Comment Statistics", stats)

    def _convert_youtube_count_to_int(self, count_text):
        """Convert YouTube format like counts (5K, 10M, 1B) to integers for sorting"""
        if not count_text or count_text.strip() == '':
            return 0

        count_text = count_text.strip().upper()

        # Handle special cases
        if count_text == 'NO LIKES' or count_text == '0':
            return 0

        # Remove any commas
        count_text = count_text.replace(',', '')

        # Check for letter indicators
        multipliers = {
            'K': 1000,
            'M': 1000,
            'B': 1000
        }

        # See if the count ends with a letter multiplier
        if count_text[-1] in multipliers:
            # Extract the numeric part
            try:
                numeric_part = float(count_text[:-1])
                # Apply the multiplier
                return int(numeric_part * multipliers[count_text[-1]])
            except ValueError:
                # If conversion fails, return 0
                return 0
        else:
            # No letter indicator, try to convert directly
            try:
                return int(float(count_text))
            except ValueError:
                return 0

    def download_profile_photos(self):
        """Download all profile photos from comments"""
        if not self.youtube_comments:
            messagebox.showinfo("Info", "No comments available. Please scrape comments first.")
            return

        # Check if any photos are available
        has_photos = False
        for c in self.youtube_comments:
            if 'profile_photo' in c:
                has_photos = True
                break
            for r in c.get('replies', []):
                if 'profile_photo' in r:
                    has_photos = True
                    break

        if not has_photos:
            messagebox.showinfo("Info", "No profile photos available. Try scraping with 'Include Profile Photos' option.")
            return

        # Ask for directory
        directory = filedialog.askdirectory(title="Select directory to save profile photos")
        if not directory:
            return

        # Start download process
        self.y_status.set("Downloading profile photos...")
        self.y_progress['value'] = 0

        def download_thread():
            total_photos = 0
            downloaded = 0

            # Count total photos
            for c in self.youtube_comments:
                if 'profile_photo' in c:
                    total_photos += 1
                for r in c.get('replies', []):
                    if 'profile_photo' in r:
                        total_photos += 1

            for c in self.youtube_comments:
                # Download comment author photo
                if 'profile_photo' in c:
                    try:
                        url = c['profile_photo']
                        # Create safe filename
                        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', c['author'])
                        filename = os.path.join(directory, f"{safe_name}.png")

                        # Download image
                        response = requests.get(url, stream=True)
                        if response.status_code == 200:
                            with open(filename, 'wb') as f:
                                for chunk in response.iter_content(1024):
                                    f.write(chunk)
                            downloaded += 1

                            # Update progress
                            progress = int(downloaded * 100 / total_photos)
                            self.master.after(0, lambda p=progress: self.y_progress.configure(value=p))
                            self.master.after(0, lambda d=downloaded, t=total_photos:
                            self.y_status.set(f"Downloading photos: {d}/{t}"))
                    except Exception as e:
                        print(f"Error downloading photo for {c['author']}: {str(e)}")

                # Download reply author photos
                for r in c.get('replies', []):
                    if 'profile_photo' in r:
                        try:
                            url = r['profile_photo']
                            # Create safe filename - add reply indication
                            safe_name = re.sub(r'[^a-zA-Z0-9]', '_', r['author']) + "_reply"
                            filename = os.path.join(directory, f"{safe_name}.png")

                            # Download image
                            response = requests.get(url, stream=True)
                            if response.status_code == 200:
                                with open(filename, 'wb') as f:
                                    for chunk in response.iter_content(1024):
                                        f.write(chunk)
                                downloaded += 1

                                # Update progress
                                progress = int(downloaded * 100 / total_photos)
                                self.master.after(0, lambda p=progress: self.y_progress.configure(value=p))
                                self.master.after(0, lambda d=downloaded, t=total_photos:
                                self.y_status.set(f"Downloading photos: {d}/{t}"))
                        except Exception as e:
                            print(f"Error downloading photo for {r['author']}: {str(e)}")

            # Done
            self.master.after(0, lambda: self.y_status.set(f"Done! Downloaded {downloaded}/{total_photos} profile photos"))
            self.master.after(0, lambda: self.y_progress.configure(value=100))

        # Start download in background
        threading.Thread(target=download_thread, daemon=True).start()

    def analyze_youtube_comments(self):
        """Analyze comments and show insights"""
        if not self.youtube_comments:
            messagebox.showinfo("Info", "No comments available. Please scrape comments first.")
            return

        # Start analysis
        self.y_status.set("Analyzing comments...")

        # Create a new window for analysis
        analysis_window = tk.Toplevel(self.master)
        analysis_window.title("YouTube Comments Analysis")
        analysis_window.geometry("700x600")

        # Create notebook for different analyses
        notebook = ttk.Notebook(analysis_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Tab 1: Basic Stats
        stats_tab = ttk.Frame(notebook)
        notebook.add(stats_tab, text="Basic Statistics")

        # Calculate statistics
        total_comments = len(self.youtube_comments)
        total_replies = sum(len(c.get('replies', [])) for c in self.youtube_comments)

        # Convert likes to integers, handling 'K' suffix
        def parse_likes(likes_str):
            if not likes_str or likes_str == '':
                return 0
            try:
                if 'K' in likes_str:
                    return int(float(likes_str.replace('K', '')) * 1000)
                return int(likes_str)
            except:
                return 0

        # Get all likes
        main_likes = [parse_likes(c.get('likes', '0')) for c in self.youtube_comments]
        avg_likes = sum(main_likes) / len(main_likes) if main_likes else 0
        max_likes = max(main_likes) if main_likes else 0
        min_likes = min(main_likes) if main_likes else 0

        # Find most liked comment
        most_liked_comment = None
        for c in self.youtube_comments:
            likes = parse_likes(c.get('likes', '0'))
            if likes == max_likes:
                most_liked_comment = c
                break

        # Create stats display
        stats_frame = ttk.LabelFrame(stats_tab, text="Comment Statistics")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        stats_text = (
            f"Total Comments: {total_comments}\n"
            f"Total Replies: {total_replies}\n\n"
            f"Average Likes: {avg_likes:.1f}\n"
            f"Maximum Likes: {max_likes}\n"
            f"Minimum Likes: {min_likes}\n\n"
        )

        if most_liked_comment:
            stats_text += (
                f"Most Liked Comment:\n"
                f"Author: {most_liked_comment.get('author', 'Unknown')}\n"
                f"Likes: {most_liked_comment.get('likes', '0')}\n"
                f"Text: {most_liked_comment.get('text', '')[:100]}...\n\n"
            )

        # Authors stats
        authors = {}
        for c in self.youtube_comments:
            author = c.get('author', 'Unknown')
            authors[author] = authors.get(author, 0) + 1
            # Add reply authors
            for r in c.get('replies', []):
                reply_author = r.get('author', 'Unknown')
                authors[reply_author] = authors.get(reply_author, 0) + 1

        most_active = max(authors.items(), key=lambda x: x[1]) if authors else ('Unknown', 0)

        stats_text += (
            f"Total Unique Authors: {len(authors)}\n"
            f"Most Active Author: {most_active[0]} ({most_active[1]} comments/replies)\n"
        )

        ttk.Label(stats_frame, text=stats_text, justify=tk.LEFT).pack(padx=10, pady=10, anchor=tk.W)

        # Tab 2: Time Analysis
        time_tab = ttk.Frame(notebook)
        notebook.add(time_tab, text="Time Analysis")

        # Process timestamps
        time_data = {}
        for c in self.youtube_comments:
            timestamp = c.get('time', '')
            if timestamp:
                # Common YouTube time formats
                if "year" in timestamp or "month" in timestamp or "week" in timestamp or "day" in timestamp or "hour" in timestamp or "minute" in timestamp:
                    category = timestamp
                    time_data[category] = time_data.get(category, 0) + 1

        # Display time distribution
        time_frame = ttk.LabelFrame(time_tab, text="Comment Time Distribution")
        time_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        if time_data:
            # Sort by frequency
            time_items = sorted(time_data.items(), key=lambda x: x[1], reverse=True)
            time_text = "Comment Age Distribution:\n\n"
            for category, count in time_items:
                time_text += f"{category}: {count} comments\n"

            ttk.Label(time_frame, text=time_text, justify=tk.LEFT).pack(padx=10, pady=10, anchor=tk.W)
        else:
            ttk.Label(time_frame, text="No time data available for analysis").pack(padx=10, pady=10)

        # Tab 3: Length Analysis
        length_tab = ttk.Frame(notebook)
        notebook.add(length_tab, text="Content Analysis")

        # Analyze comment length
        length_frame = ttk.LabelFrame(length_tab, text="Comment Length Analysis")
        length_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Calculate lengths
        lengths = [len(c.get('text', '')) for c in self.youtube_comments]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        max_length = max(lengths) if lengths else 0
        min_length = min(lengths) if lengths else 0

        # Find shortest and longest comments
        shortest_comment = None
        longest_comment = None
        for c in self.youtube_comments:
            text_len = len(c.get('text', ''))
            if text_len == min_length and min_length > 0:
                shortest_comment = c
            if text_len == max_length:
                longest_comment = c

        length_text = (
            f"Average Comment Length: {avg_length:.1f} characters\n"
            f"Longest Comment: {max_length} characters\n"
            f"Shortest Comment: {min_length} characters\n\n"
        )

        if longest_comment:
            length_text += (
                f"Longest Comment Example:\n"
                f"Author: {longest_comment.get('author', 'Unknown')}\n"
                f"Text: {longest_comment.get('text', '')[:200]}...\n\n"
            )

        if shortest_comment and min_length > 0:
            length_text += (
                f"Shortest Comment Example:\n"
                f"Author: {shortest_comment.get('author', 'Unknown')}\n"
                f"Text: {shortest_comment.get('text', '')}\n"
            )

        ttk.Label(length_frame, text=length_text, justify=tk.LEFT).pack(padx=10, pady=10, anchor=tk.W)

        # Set status when done
        self.y_status.set("Analysis complete")



    def show_youtube_context_menu(self, event):
        """Show a right-click menu on a comment/reply row with profile-photo options."""
        item_id = self.y_tree.identify_row(event.y)
        if not item_id:
            self._log_youtube_warning("Context menu: No item identified at click position.")
            return

        # Select the identified item in the tree
        self.y_tree.selection_set(item_id)
        self.y_tree.focus(item_id) # Also set focus

        self._log_youtube_info(f"Context menu for item: {item_id}")

        comment_data_obj = None
        author_name = "Unknown" # Default author name

        try:
            # Determine if it's a main comment or a reply based on item_id structure
            # Assuming item_id is like "c{index}" for main comments and "c{index}r{reply_index}" for replies.
            if 'r' in item_id:  # It's a reply
                parts = item_id.replace('c', '').split('r')
                parent_idx = int(parts[0])
                reply_idx = int(parts[1])
                if self.youtube_comments and 0 <= parent_idx < len(self.youtube_comments):
                    parent_comment = self.youtube_comments[parent_idx]
                    if 'replies' in parent_comment and 0 <= reply_idx < len(parent_comment['replies']):
                        comment_data_obj = parent_comment['replies'][reply_idx]
                        author_name = comment_data_obj.get('author', f"Reply Author {reply_idx}")
                    else:
                        self._log_youtube_warning(f"Context menu: Reply index {reply_idx} out of bounds for parent c{parent_idx}.")
                else:
                    self._log_youtube_warning(f"Context menu: Parent comment index {parent_idx} out of bounds.")
            else:  # It's a main comment
                comment_idx_str = item_id.replace('c', '')
                comment_idx = int(comment_idx_str)
                if self.youtube_comments and 0 <= comment_idx < len(self.youtube_comments):
                    comment_data_obj = self.youtube_comments[comment_idx]
                    author_name = comment_data_obj.get('author', f"Comment Author {comment_idx}")
                else:
                    self._log_youtube_warning(f"Context menu: Main comment index {comment_idx} out of bounds.")

        except (ValueError, IndexError, TypeError) as e:
            self._log_youtube_error(f"Context menu: Error parsing item ID '{item_id}' or accessing comment data: {e}")
            messagebox.showerror("Menu Error", f"Could not retrieve data for item {item_id}.")
            return
        except Exception as e: # Catch any other unexpected error during data retrieval
            self._log_youtube_error(f"Context menu: Unexpected error retrieving data for item '{item_id}': {e}")
            messagebox.showerror("Menu Error", f"Unexpected error for item {item_id}.")
            return


        menu = tk.Menu(self.master, tearoff=0)

        if comment_data_obj:
            photo_url = comment_data_obj.get('profile_photo')
            if photo_url:
                self._log_youtube_info(f"Context menu: Found photo URL for {author_name}: {photo_url[:50]}...")
                menu.add_command(label=f"View Photo for {author_name}",
                                 command=lambda u=photo_url, a=author_name: self.open_profile_photo_window(u, a))
                menu.add_command(label=f"Save Photo for {author_name}...",
                                 command=lambda u=photo_url, a=author_name: self.save_profile_photo_to_folder(u, a))
            else:
                self._log_youtube_warning(f"Context menu: No 'profile_photo' URL found for {author_name}.")
                menu.add_command(label=f"No profile photo for {author_name}", state="disabled")
        else:
            self._log_youtube_warning(f"Context menu: Comment data object not found for item '{item_id}'.")
            menu.add_command(label="Comment data not found", state="disabled")

        menu.add_separator()
        menu.add_command(label="Copy Comment Text", command=lambda cd=comment_data_obj: self._copy_comment_text_to_clipboard(cd))
        menu.add_command(label="Copy Author Name", command=lambda cd=comment_data_obj: self._copy_author_to_clipboard(cd))


        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release() # Ensure menu doesn't lock up UI if there's an issue

    def open_profile_photo_window(self, url, author):
        """Display the selected profile photo in a pop-up window."""
        win = tk.Toplevel(self.master)
        win.title(f"Profile Photo – {author}")
        win.geometry("300x350")
        ttk.Label(win, text=f"Author: {author}").pack(pady=5)
        img_label = ttk.Label(win, text="Loading…")
        img_label.pack(pady=20)

        def _download():
            try:
                r = requests.get(url, stream=True)
                r.raise_for_status()
                from PIL import Image, ImageTk
                img = Image.open(io.BytesIO(r.content)).resize((150,150), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                img_label.config(image=photo, text="")
                img_label.image = photo
            except Exception as e:
                messagebox.showerror("Error", f"Could not load image:\n{e}")

        threading.Thread(target=_download, daemon=True).start()

    def save_profile_photo_to_folder(self, url, author):
        """Prompt for folder and save that comment-author’s profile photo."""
        directory = filedialog.askdirectory(title="Select folder to save photo")
        if not directory:
            return
        try:
            r = requests.get(url, stream=True)
            r.raise_for_status()
            from PIL import Image
            img = Image.open(io.BytesIO(r.content))
            safe = re.sub(r'[^0-9A-Za-z]+', '_', author) or "photo"
            path = os.path.join(directory, f"{safe}.png")
            img.save(path)
            messagebox.showinfo("Saved", f"Profile photo saved to:\n{path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save photo:\n{e}")

    def expand_all_youtube_replies(self):
        for item in self.y_tree.get_children():
            self.y_tree.item(item, open=True)

    def collapse_all_youtube_replies(self):
        for item in self.y_tree.get_children():
            self.y_tree.item(item, open=False)


    def _copy_comment_text_to_clipboard(self, comment_data_obj):
        if comment_data_obj and 'text' in comment_data_obj:
            try:
                self.master.clipboard_clear()
                self.master.clipboard_append(comment_data_obj['text'])
                self._log_youtube_success("Comment text copied to clipboard.")
            except tk.TclError:
                self._log_youtube_error("Could not access clipboard to copy comment text.")
                messagebox.showerror("Clipboard Error", "Could not copy text to clipboard.")
        else:
            self._log_youtube_warning("No comment text to copy.")

    def _copy_author_to_clipboard(self, comment_data_obj):
        if comment_data_obj and 'author' in comment_data_obj:
            try:
                self.master.clipboard_clear()
                self.master.clipboard_append(comment_data_obj['author'])
                self._log_youtube_success("Author name copied to clipboard.")
            except tk.TclError:
                self._log_youtube_error("Could not access clipboard to copy author name.")
                messagebox.showerror("Clipboard Error", "Could not copy author to clipboard.")
        else:
            self._log_youtube_warning("No author name to copy.")


    def pause_youtube_scraping(self):
        """Pause or resume the scraping process"""
        if not self.scraping_thread or not self.scraping_thread.is_alive():
            return

        if self.scraping_paused:
            # Resume scraping
            self.scraping_paused = False
            self.y_pause_button.config(text="Pause")
            self.y_status.set("Resuming scraping...")
        else:
            # Pause scraping
            self.scraping_paused = True
            self.y_pause_button.config(text="Resume")
            self.y_status.set("Scraping paused. Click Resume to continue.")
    def stop_youtube_scraping(self):
        """Stop the scraping process completely"""
        if not self.scraping_thread or not self.scraping_thread.is_alive():
            return

        self.scraping_stopped = True
        self.y_status.set("Stopping scraping, please wait...")

        # Disable pause button when stopping
        self.y_pause_button.config(state=tk.DISABLED)

    def _reset_scraping_buttons(self):
        """Reset UI buttons after scraping completes or is stopped"""
        self.y_scrape_button.config(state=tk.NORMAL)
        self.y_pause_button.config(state=tk.DISABLED, text="Pause")
        self.y_stop_button.config(state=tk.DISABLED)
        self.scraping_paused = False
        self.scraping_stopped = False

    def toggle_channel_mode(self):
        enabled = self.y_channel_mode_var.get()
        # Toggle entries
        self.y_channel_entry.config(state=tk.NORMAL if enabled else tk.DISABLED)
        self.y_url_entry.config(state=tk.DISABLED if enabled else tk.NORMAL)
        # Toggle video mode controls
        for w in (self.y_video_all_rb, self.y_video_num_rb):
            w.config(state=tk.NORMAL if enabled else tk.DISABLED)
        # Update count entry
        self.update_video_count_entry()

    def update_video_count_entry(self):
        if self.y_channel_mode_var.get() and self.y_video_mode.get() == "Number":
            self.y_video_count_entry.config(state=tk.NORMAL)
        else:
            self.y_video_count_entry.config(state=tk.DISABLED)


    def get_channel_video_links(self, driver, channel_url_videos_tab, video_limit):
        """
        Navigates to a YouTube channel's videos page, scrolls to load videos,
        and extracts video links in the order they appear (latest first, row by row).

        Args:
            driver: Selenium WebDriver instance.
            channel_url_videos_tab: URL of the channel's videos tab.
            video_limit: Number of videos to get (integer), or 'all' (string).

        Returns:
            A list of video URLs in the correct order, respecting the video_limit.
        """
        self.master.after(0, lambda: self.y_status.set(f"Opening channel videos page: {channel_url_videos_tab}"))
        try:
            driver.get(channel_url_videos_tab)
            # Wait for the main container of videos to appear
            WebDriverWait(driver, 15).until( # Increased wait time slightly
                 EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-rich-grid-renderer")), # Common for /videos tab
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-grid-renderer")), # Older layout or other views
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-browse[page-subtype='channels'] #contents")) # General content area
                 )
            )
        except TimeoutException:
            self.master.after(0, lambda: self.y_status.set(f"Timeout loading videos page contents: {channel_url_videos_tab}"))
            # Proceed with cookie handling and link extraction attempt anyway, page might be partially loaded
            pass

        # Assuming _handle_cookie_banners is a method in your class
        self._handle_cookie_banners(driver, WebDriverWait(driver, 5))

        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        scroll_attempts_no_change = 0
        MAX_NO_CHANGE_SCROLLS = 7 # Stop if height doesn't change for this many scrolls
        SCROLL_PAUSE_TIME = 2.0 # Pause between scrolls to let content load

        self.master.after(0, lambda: self.y_status.set("Scrolling page to load all required videos..."))

        # --- Scrolling Phase ---
        while True:
            if self.scraping_stopped:
                self.master.after(0, lambda: self.y_status.set("Stopped by user while getting video links."))
                return []

            while self.scraping_paused and not self.scraping_stopped:
                self.master.after(0, lambda: self.y_status.set("Paused by user while scrolling for video links..."))
                time.sleep(0.5)

            if self.scraping_stopped: # Re-check after pause
                self.master.after(0, lambda: self.y_status.set("Stopped by user while getting video links."))
                return []

            # Optimization: If a video_limit is set, check if we might have enough elements.
            # This checks for video *item containers*, not just links yet.
            if video_limit != 'all' and isinstance(video_limit, int):
                 try:
                     # These selectors target the individual video item containers in the grid
                     current_video_item_elements = driver.find_elements(By.CSS_SELECTOR, "ytd-rich-item-renderer, ytd-grid-video-renderer")
                     current_elements_count = len(current_video_item_elements)
                     self.master.after(0, lambda n=current_elements_count, lim=video_limit: self.y_status.set(f"Scrolling... ({n} video items found, aiming for {lim if isinstance(lim,int) else 'all'})"))
                     if current_elements_count >= video_limit:
                         # Found enough potential items. Scroll a tiny bit more to ensure rendering and then stop scrolling.
                         driver.execute_script("window.scrollBy(0, 500);") # Small scroll
                         time.sleep(1.0) # Let it settle
                         self.master.after(0, lambda n=current_elements_count: self.y_status.set(f"Potentially enough video items ({n}) loaded for limit. Stopping scroll."))
                         break
                 except Exception as e:
                     print(f"Minor error checking element count during scroll: {e}") # Non-critical

            # Scroll down to the bottom of the page
            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)

            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                scroll_attempts_no_change += 1
            else:
                scroll_attempts_no_change = 0 # Reset if height changed

            last_height = new_height

            if scroll_attempts_no_change >= MAX_NO_CHANGE_SCROLLS:
                self.master.after(0, lambda: self.y_status.set("Reached end of scrollable content or no new content loaded after multiple attempts."))
                break

        # --- Collection Phase ---
        self.master.after(0, lambda: self.y_status.set("Scrolling complete. Collecting video links in DOM order..."))
        ordered_video_links = []
        collected_urls_set = set() # To ensure uniqueness while preserving order

        try:
            # Find all video link elements. These selectors target the <a> tag directly.
            # The order returned by find_elements should reflect the DOM order (top-to-bottom, left-to-right).
            video_link_elements = driver.find_elements(By.CSS_SELECTOR, "ytd-rich-item-renderer a#video-title-link")
            if not video_link_elements: # Fallback for potentially different grid structures
                video_link_elements.extend(driver.find_elements(By.CSS_SELECTOR, "ytd-grid-video-renderer a#video-title-link"))
            # Broader fallback (less ideal as it might pick up other #video-title elements if not careful)
            if not video_link_elements:
                video_link_elements.extend(driver.find_elements(By.CSS_SELECTOR, "a#video-title"))


            self.master.after(0, lambda n=len(video_link_elements): self.y_status.set(f"Found {n} potential video link elements. Extracting URLs..."))

            for elem_idx, elem in enumerate(video_link_elements):
                if self.scraping_stopped: break
                while self.scraping_paused and not self.scraping_stopped:
                    self.master.after(0, lambda: self.y_status.set("Paused during link collection..."))
                    time.sleep(0.5)
                if self.scraping_stopped: break

                # Apply video_limit check here before processing the element
                if video_limit != 'all' and isinstance(video_limit, int) and len(ordered_video_links) >= video_limit:
                     self.master.after(0, lambda lim=video_limit: self.y_status.set(f"Reached video limit of {lim} during collection."))
                     break

                try:
                    href = elem.get_attribute('href')
                    if href and "watch?v=" in href: # Basic validation for a YouTube video link
                        # Normalize URL to standard watch URL format to help with uniqueness
                        video_id_param = href.split("watch?v=")[1].split("&")[0]
                        normalized_href = f"https://www.youtube.com/watch?v={video_id_param}"

                        if normalized_href not in collected_urls_set:
                            ordered_video_links.append(normalized_href)
                            collected_urls_set.add(normalized_href)
                            if elem_idx % 20 == 0: # Update status periodically
                                self.master.after(0, lambda c=len(ordered_video_links): self.y_status.set(f"Collected {c} unique video links..."))

                except Exception as e_extract:
                    print(f"Error extracting href from element: {e_extract}")
                    continue # Skip problematic element

        except Exception as e_collect:
            print(f"Error collecting video link elements after scroll: {e_collect}")
            self.master.after(0, lambda: self.y_status.set("Error occurred while collecting video links."))
            # Return whatever might have been collected so far

        # Final trim to video_limit if 'all' was not specified and more were collected than needed
        # (This is a safeguard, the loop above should also break)
        final_links = ordered_video_links
        if video_limit != 'all' and isinstance(video_limit, int):
             final_links = ordered_video_links[:video_limit]

        if self.scraping_stopped:
            self.master.after(0, lambda c=len(final_links): self.y_status.set(f"Link collection stopped by user. {c} links gathered."))
        else:
            self.master.after(0, lambda c=len(final_links): self.y_status.set(f"Finished getting video links. Total collected: {c}"))

        return final_links

    def youtube_channel_scrape_thread(self, channel_url, video_limit, include_replies, include_photos):
        driver = None
        all_comments_from_channel = []
        try:
            original_scroll_times = self.y_scroll_var.get()
        except AttributeError:
            print("Warning: self.y_scroll_var not found for original_scroll_times, defaulting to 5.")
            original_scroll_times = 5

        try:
            opts = uc.ChromeOptions()
            if not self.y_debug_mode_var.get(): # Check if Debug Mode is OFF
                opts.add_argument("--headless")
            opts.add_argument("--disable-blink-features=AutomationControlled")
            driver = uc.Chrome(options=opts)

            clean_channel_url = channel_url.strip().rstrip('/')
            if '/videos' not in clean_channel_url.lower():
                if '/@' in clean_channel_url or '/c/' in clean_channel_url or '/user/' in clean_channel_url:
                    channel_url_videos_tab = clean_channel_url + '/videos'
                else:
                    channel_url_videos_tab = clean_channel_url + '/videos'
            else:
                channel_url_videos_tab = clean_channel_url

            self.master.after(0, lambda: self.y_progress.configure(value=5))

            video_urls = self.get_channel_video_links(driver, channel_url_videos_tab, video_limit)

            if not video_urls:
                if not self.scraping_stopped:
                    self.master.after(0, lambda: self.y_status.set("No video links found or process stopped."))
                    self.master.after(0, lambda: messagebox.showinfo("Channel Scrape Info", "No video links found or process stopped."))
                if driver:
                    driver.quit()
                self.master.after(0, self._reset_scraping_buttons)
                return

            num_videos_to_scrape = len(video_urls)
            self.master.after(0, lambda: self.y_progress.configure(value=10))

            for i, video_url in enumerate(video_urls):
                if self.scraping_stopped:
                    self.master.after(0, lambda: self.y_status.set("Channel scraping stopped by user."))
                    break

                while self.scraping_paused and not self.scraping_stopped:
                    status_text = f"Channel scraping paused before video {i+1}/{num_videos_to_scrape}: {video_url.split('v=')[-1]}"
                    self.master.after(0, lambda s=status_text: self.y_status.set(s))
                    time.sleep(0.5)

                if self.scraping_stopped:
                    self.master.after(0, lambda: self.y_status.set("Channel scraping stopped by user."))
                    break

                base_progress_for_this_video = 10 + (i / num_videos_to_scrape) * 85
                progress_increment_for_this_video = (1 / num_videos_to_scrape) * 85

                status_msg = f"Scraping video {i+1}/{num_videos_to_scrape}: {video_url.split('v=')[-1]}"
                self.master.after(0, lambda s=status_msg: self.y_status.set(s))
                self.master.after(0, lambda p=base_progress_for_this_video: self.y_progress.configure(value=p))

                video_title_for_comments = "Unknown Video"
                try:
                    driver.get(video_url)
                    # *** Crucial: Initialize short_wait AFTER driver.get() for the new page ***
                    short_wait = WebDriverWait(driver, 3)

                    try:
                        title_element = WebDriverWait(driver, 7).until(
                            EC.visibility_of_element_located((By.CSS_SELECTOR, "h1.ytd-watch-metadata #video-title, yt-formatted-string.ytd-watch-metadata[slot='title']"))
                        )
                        video_title_for_comments = title_element.text.strip()
                    except TimeoutException:
                        video_title_for_comments = driver.title
                    except Exception as e_title:
                        print(f"Could not get video title for {video_url}: {e_title}")
                        video_title_for_comments = driver.title or "Title N/A"

                    self._handle_cookie_banners(driver, short_wait) # Pass the correctly initialized short_wait

                    if self.scraping_stopped: continue

                    sub_status_1 = f"Scrolling comments for V:{i+1} ({video_title_for_comments[:30]}...)"
                    self.master.after(0, lambda s=sub_status_1: self.y_status.set(s))
                    self._scroll_for_comments(driver, original_scroll_times, 0)
                    self.master.after(0, lambda p=base_progress_for_this_video + progress_increment_for_this_video * 0.4: self.y_progress.configure(value=p))

                    if self.scraping_stopped: continue

                    if include_replies:
                        sub_status_2 = f"Expanding replies for V:{i+1} ({video_title_for_comments[:30]}...)"
                        self.master.after(0, lambda s=sub_status_2: self.y_status.set(s))
                        self._expand_replies(driver, short_wait, 0, 0) # Pass the correctly initialized short_wait
                        self.master.after(0, lambda p=base_progress_for_this_video + progress_increment_for_this_video * 0.7: self.y_progress.configure(value=p))

                    if self.scraping_stopped: continue

                    sub_status_3 = f"Processing comments for V:{i+1} ({video_title_for_comments[:30]}...)"
                    self.master.after(0, lambda s=sub_status_3: self.y_status.set(s))
                    comments_for_this_video = self._process_comments(driver, include_replies, include_photos, 0, 0)

                    for comment_obj in comments_for_this_video:
                        comment_obj['video_url'] = video_url
                        comment_obj['video_title'] = video_title_for_comments
                    all_comments_from_channel.extend(comments_for_this_video)

                    self.master.after(0, lambda p=base_progress_for_this_video + progress_increment_for_this_video: self.y_progress.configure(value=p))

                except Exception as e_video:
                    error_msg = f"Error on video {video_url.split('v=')[-1]}: {str(e_video)[:100]}"
                    print(f"Error scraping video {video_url}: {e_video}")
                    self.master.after(0, lambda s=error_msg: self.y_status.set(s))
                    time.sleep(1)

            if driver:
                driver.quit()
                driver = None

            final_progress = 95
            self.master.after(0, lambda p=final_progress: self.y_progress.configure(value=p))

            if not self.scraping_stopped:
                if all_comments_from_channel:
                    status_final = f"Channel scrape complete. Total comments from {len(video_urls)} videos: {len(all_comments_from_channel)}"
                    self.master.after(0, lambda s=status_final: self.y_status.set(s))
                    self.master.after(0, lambda: self.update_youtube_ui(all_comments_from_channel))
                else:
                    self.master.after(0, lambda: self.y_status.set("Channel scrape complete. No comments found in processed videos."))
                    self.master.after(0, lambda: messagebox.showinfo("Channel Scrape Complete", "No comments were found in the processed videos for this channel."))
            else:
                status_stopped_final = f"Channel scraping stopped. {len(all_comments_from_channel)} comments collected."
                self.master.after(0, lambda s=status_stopped_final: self.y_status.set(s))
                if all_comments_from_channel:
                     self.master.after(0, lambda: self.update_youtube_ui(all_comments_from_channel))

            self.master.after(0, lambda: self.y_progress.configure(value=100))

        except Exception as e_channel_main:
            error_channel_final = f"Channel Scrape Main Error: {str(e_channel_main)[:150]}"
            print(f"Major error in youtube_channel_scrape_thread: {e_channel_main}")
            import traceback
            traceback.print_exc()
            self.master.after(0, lambda s=error_channel_final: self.y_status.set(s))
            if driver:
                driver.quit()
        finally:
            if driver:
                driver.quit()
            self.master.after(0, self._reset_scraping_buttons)

    def toggle_youtube_input_mode(self):
        """Toggles UI elements based on the selected scrape mode."""
        selected_mode = self.y_scrape_mode_var.get()

        # Forget all potentially packed mode-specific frames and their children first
        self.y_video_url_frame.pack_forget()
        # Children of y_video_url_frame (label, entry) are managed by its packing

        self.y_channel_url_frame.pack_forget()
        self.y_channel_label.pack_forget()
        self.y_channel_entry.pack_forget()

        self.y_channel_limit_frame.pack_forget()
        self.y_channel_limit_label.pack_forget()
        self.y_channel_limit_entry.pack_forget()

        self.y_list_file_frame.pack_forget()
        self.y_list_file_label.pack_forget()
        self.y_list_file_entry.pack_forget()
        self.y_list_browse_button.pack_forget()

        # Always visible common elements might need repacking if their relative position changes
        # However, if they are in a separate container from y_dynamic_input_area,
        # or if y_dynamic_input_area just expands/contracts, their pack order within y_dynamic_input_area is key.
        self.y_scroll_label.pack_forget()
        self.y_scroll_entry.pack_forget()


        if selected_mode == "video":
            # --- Single video scraping mode ---
            # Order: Video URL -> Scroll Times
            self.y_video_url_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            # (Children of y_video_url_frame like its label and entry are packed within it during its own setup)

            self.y_scroll_label.pack(side=tk.LEFT, padx=(10, 5)) # Add some space after URL frame
            self.y_scroll_entry.pack(side=tk.LEFT)

            self.y_scrape_button.config(text="Scrape Comments")

        elif selected_mode == "channel":
            # --- Channel scraping mode ---
            # Order: Channel URL -> Number of Videos -> Scroll Times

            # Pack Channel URL input
            self.y_channel_url_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            self.y_channel_label.pack(side=tk.LEFT, padx=5)
            self.y_channel_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

            # Pack Number of Videos input
            self.y_channel_limit_frame.pack(side=tk.LEFT, padx=5)
            self.y_channel_limit_label.pack(side=tk.LEFT, padx=5)
            self.y_channel_limit_entry.pack(side=tk.LEFT, padx=5)

            # Pack Scroll Times input
            self.y_scroll_label.pack(side=tk.LEFT, padx=(10, 5))
            self.y_scroll_entry.pack(side=tk.LEFT)

            self.y_scrape_button.config(text="Scrape Channel Videos")

        elif selected_mode == "list":
            # --- List from File scraping mode ---
            # Order: List File Input -> Scroll Times
            self.y_list_file_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0,5))
            self.y_list_file_label.pack(side=tk.LEFT, padx=5)
            self.y_list_file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
            self.y_list_browse_button.pack(side=tk.LEFT, padx=5)

            self.y_scroll_label.pack(side=tk.LEFT, padx=(10, 5)) # Add some space after list file frame
            self.y_scroll_entry.pack(side=tk.LEFT)

            self.y_scrape_button.config(text="Scrape List")

        # Ensure the dynamic input area's parent (input_frame) adjusts if needed.
        # self.y_dynamic_input_area.master.update_idletasks() # May not be necessary

    def get_channel_video_links(self, driver, channel_url_videos_tab, video_limit):
        """
        Navigates to a YouTube channel's videos page, scrolls to load videos,
        and extracts video links in the order they appear (latest first, row by row).

        Args:
            driver: Selenium WebDriver instance.
            channel_url_videos_tab: URL of the channel's videos tab.
            video_limit: Number of videos to get (integer), or 'all' (string).

        Returns:
            A list of video URLs in the correct order, respecting the video_limit.
        """
        self.master.after(0, lambda: self.y_status.set(f"Opening channel videos page: {channel_url_videos_tab}"))
        try:
            driver.get(channel_url_videos_tab)
            WebDriverWait(driver, 15).until(
                 EC.any_of(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-rich-grid-renderer")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-grid-renderer")),
                    EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-browse[page-subtype='channels'] #contents"))
                 )
            )
        except TimeoutException:
            self.master.after(0, lambda: self.y_status.set(f"Timeout loading videos page contents: {channel_url_videos_tab}"))
            pass

        self._handle_cookie_banners(driver, WebDriverWait(driver, 5))

        last_height = driver.execute_script("return document.documentElement.scrollHeight")
        scroll_attempts_no_change = 0
        MAX_NO_CHANGE_SCROLLS = 7
        SCROLL_PAUSE_TIME = 2.0

        self.master.after(0, lambda: self.y_status.set("Scrolling page to load all required videos..."))

        # --- Scrolling Phase ---
        while True:
            if self.scraping_stopped:
                self.master.after(0, lambda: self.y_status.set("Stopped by user while getting video links."))
                return []

            while self.scraping_paused and not self.scraping_stopped:
                self.master.after(0, lambda: self.y_status.set("Paused by user while scrolling for video links..."))
                time.sleep(0.5)

            if self.scraping_stopped:
                self.master.after(0, lambda: self.y_status.set("Stopped by user while getting video links."))
                return []

            if video_limit != 'all' and isinstance(video_limit, int):
                 try:
                     current_video_item_elements = driver.find_elements(By.CSS_SELECTOR, "ytd-rich-item-renderer, ytd-grid-video-renderer")
                     current_elements_count = len(current_video_item_elements)
                     self.master.after(0, lambda n=current_elements_count, lim=video_limit: self.y_status.set(f"Scrolling... ({n} video items found, aiming for {lim if isinstance(lim,int) else 'all'})"))
                     if current_elements_count >= video_limit:
                         driver.execute_script("window.scrollBy(0, 500);")
                         time.sleep(1.0)
                         self.master.after(0, lambda n=current_elements_count: self.y_status.set(f"Potentially enough video items ({n}) loaded for limit. Stopping scroll."))
                         break
                 except Exception as e:
                     print(f"Minor error checking element count during scroll: {e}")

            driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)

            new_height = driver.execute_script("return document.documentElement.scrollHeight")
            if new_height == last_height:
                scroll_attempts_no_change += 1
            else:
                scroll_attempts_no_change = 0

            last_height = new_height

            if scroll_attempts_no_change >= MAX_NO_CHANGE_SCROLLS:
                self.master.after(0, lambda: self.y_status.set("Reached end of scrollable content or no new content loaded."))
                break

        # --- Collection Phase (Revised) ---
        self.master.after(0, lambda: self.y_status.set("Scrolling complete. Collecting video links in DOM order..."))
        ordered_video_links = []
        collected_urls_set = set()

        try:
            # Primary combined selector:
            # Targets 'a#video-title-link' inside 'ytd-rich-item-renderer' OR 'ytd-grid-video-renderer'.
            # This should return elements in their combined DOM order, preserving visual flow.
            # Also include 'a#video-title' as a fallback within these items if 'a#video-title-link' isn't always present.
            combined_link_selector = (
                "ytd-rich-item-renderer a#video-title-link, "
                "ytd-grid-video-renderer a#video-title-link, "
                "ytd-rich-item-renderer a#video-title, "  # Fallback for #video-title within rich items
                "ytd-grid-video-renderer a#video-title"   # Fallback for #video-title within grid items
            )
            video_link_elements = driver.find_elements(By.CSS_SELECTOR, combined_link_selector)

            # Broader fallback if the specific item-based selectors yield nothing.
            # This targets any a#video-title, which is less precise but can be a last resort.
            if not video_link_elements:
                self.master.after(0, lambda: self.y_status.set("Primary/secondary item link selectors failed, trying broad 'a#video-title'."))
                video_link_elements = driver.find_elements(By.CSS_SELECTOR, "a#video-title")
                if video_link_elements:
                    self.master.after(0, lambda: self.y_status.set("Using broad fallback link selector (a#video-title)."))


            self.master.after(0, lambda n=len(video_link_elements): self.y_status.set(f"Found {n} potential video link elements. Extracting URLs..."))

            for elem_idx, elem in enumerate(video_link_elements):
                if self.scraping_stopped: break
                while self.scraping_paused and not self.scraping_stopped:
                    self.master.after(0, lambda: self.y_status.set("Paused during link collection..."))
                    time.sleep(0.5)
                if self.scraping_stopped: break

                if video_limit != 'all' and isinstance(video_limit, int) and len(ordered_video_links) >= video_limit:
                     self.master.after(0, lambda lim=video_limit: self.y_status.set(f"Reached video limit of {lim} during collection."))
                     break

                try:
                    href = elem.get_attribute('href')
                    if href and "watch?v=" in href and "/@SHEIN" not in href.upper(): # Basic validation & filter out "SHEIN" or similar ad/non-video links if they use #video-title
                        video_id_param = href.split("watch?v=")[1].split("&")[0]
                        normalized_href = f"https://www.youtube.com/watch?v={video_id_param}"

                        if normalized_href not in collected_urls_set:
                            ordered_video_links.append(normalized_href)
                            collected_urls_set.add(normalized_href)
                            if elem_idx > 0 and elem_idx % 20 == 0:
                                self.master.after(0, lambda c=len(ordered_video_links): self.y_status.set(f"Collected {c} unique video links..."))
                except Exception as e_extract:
                    print(f"Error extracting href from element or normalizing: {e_extract} on element: {elem.get_attribute('outerHTML')[:100]}")
                    continue

        except Exception as e_collect:
            print(f"Error collecting video link elements after scroll: {e_collect}")
            self.master.after(0, lambda: self.y_status.set("Error occurred while collecting video links."))

        final_links = ordered_video_links
        if video_limit != 'all' and isinstance(video_limit, int):
             final_links = ordered_video_links[:video_limit]

        if self.scraping_stopped:
            self.master.after(0, lambda c=len(final_links): self.y_status.set(f"Link collection stopped by user. {c} links gathered."))
        else:
            self.master.after(0, lambda c=len(final_links): self.y_status.set(f"Finished getting video links. Total collected: {c}"))

        return final_links




    def _log_youtube_info(self, msg):     print(f"[INFO ] {msg}")
    def _log_youtube_warning(self, msg):  print(f"[WARN ] {msg}")
    def _log_youtube_error(self, msg):    print(f"[ERROR] {msg}")
    def _log_youtube_success(self, msg):  print(f"[ OK  ] {msg}")



#---------------------------------------#



def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()