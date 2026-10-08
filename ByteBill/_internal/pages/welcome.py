"""Welcome (home) page — Step 1 deliverable."""
from datetime import datetime


def build(parent, app):
    """parent: CTkFrame content area. app: BillingApp (for navigation + settings)."""
    import customtkinter as ctk
    from theme import COLORS, FONTS
    import database as db

    for w in parent.winfo_children():
        w.destroy()

    s = db.get_settings()
    biz = s.get("business_name") or "Your Business Name"

    # Header card
    head = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    head.pack(fill="x", padx=4, pady=4)
    ctk.CTkLabel(head, text=f"Welcome to {biz} 👋",
                 font=FONTS["title"], text_color=COLORS["text_dark"]).pack(anchor="w", padx=20, pady=(16, 2))
    ctk.CTkLabel(head, text=f"{datetime.now():%A, %d %B %Y}  •  Professional Billing, Inventory & GST Reports",
                 font=FONTS["subtitle"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=20, pady=(0, 16))

    # 4 stat cards row
    stats = ctk.CTkFrame(parent, fg_color="transparent")
    stats.pack(fill="x", padx=4, pady=4)
    for i, (title, value, hint) in enumerate([
        ("Today's Sales", "₹ 0", "updates with every bill"),
        ("Total Products", "0", "live from Inventory"),
        ("Low Stock Alerts", "0", "automatic restock reminders"),
        ("Next Invoice No", f"{s.get('invoice_prefix','INV')}-{s.get('invoice_next_no',1)}", "customise in Settings"),
    ]):
        card = ctk.CTkFrame(stats, fg_color=COLORS["card"], corner_radius=12, width=200)
        card.grid(row=0, column=i, padx=6, sticky="nsew")
        stats.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(card, text=title, font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=14, pady=(12, 0))
        ctk.CTkLabel(card, text=value, font=FONTS["heading"], text_color=COLORS["text_dark"]).pack(anchor="w", padx=14)
        ctk.CTkLabel(card, text=hint, font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=14, pady=(0, 12))

    # Quick actions
    qa = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    qa.pack(fill="x", padx=4, pady=4)
    ctk.CTkLabel(qa, text="Quick Actions", font=FONTS["heading"], text_color=COLORS["text_dark"]).pack(anchor="w", padx=20, pady=(14, 6))
    btnrow = ctk.CTkFrame(qa, fg_color="transparent")
    btnrow.pack(fill="x", padx=20, pady=(0, 16))
    for label, page in [("＋  New Bill", "billing"), ("▦  Manage Inventory", "inventory"),
                        ("⚙  Business Settings", "settings"), ("▤  View Reports", "reports")]:
        ctk.CTkButton(btnrow, text=label, command=lambda p=page: app.show_page(p),
                      fg_color=COLORS["accent"], hover_color=COLORS["accent_hover"],
                      corner_radius=8, height=38).pack(side="left", padx=(0, 10))

    note = ctk.CTkFrame(parent, fg_color="transparent")
    note.pack(fill="x", padx=8, pady=2)
    ctk.CTkLabel(note,
                 text="Tip: complete your business profile in Settings, add products in Inventory, then start billing.",
                 font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w")
