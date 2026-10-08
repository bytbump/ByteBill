"""STEP 6 — Coupon master: create codes customers can use in Billing."""
from datetime import date


def build(parent, app):
    import customtkinter as ctk
    from tkinter import ttk, messagebox
    from theme import COLORS, FONTS
    import database as db

    for w in parent.winfo_children():
        w.destroy()

    selected = {"id": None}

    tframe = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    tframe.pack(fill="both", expand=True, padx=4, pady=4)
    ctk.CTkLabel(tframe, text="Coupon Codes", font=FONTS["heading"],
                 text_color=COLORS["text_dark"]).pack(anchor="w", padx=16, pady=(10, 2))
    cols = ("code", "pct", "cap", "valid", "status")
    tree = ttk.Treeview(tframe, columns=cols, show="headings", height=10)
    for c, h, wd in [("code", "Code", 150), ("pct", "Disc %", 80), ("cap", "Max ₹", 100),
                     ("valid", "Valid From → To", 220), ("status", "Status", 100)]:
        tree.heading(c, text=h)
        tree.column(c, width=wd, anchor="center")
    tree.pack(fill="both", expand=True, padx=16, pady=4)
    id_map = {}

    def refresh():
        for r in tree.get_children():
            tree.delete(r)
        id_map.clear()
        for c in db.list_coupons():
            iid = tree.insert("", "end", values=(
                c["code"], f"{c['discount_percent']:g}", f"₹{c['max_discount']:g}",
                f"{c['valid_from'] or '…'} → {c['valid_to'] or '…'}",
                "Active" if c["active"] else "Off"))
            id_map[iid] = c

    form = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    form.pack(fill="x", padx=4, pady=4)
    ctk.CTkLabel(form, text="Add / Edit Coupon", font=FONTS["heading"],
                 text_color=COLORS["text_dark"]).pack(anchor="w", padx=16, pady=(10, 2))
    frow = ctk.CTkFrame(form, fg_color="transparent")
    frow.pack(fill="x", padx=16, pady=2)
    e_code = ctk.CTkEntry(frow, width=150, height=32, placeholder_text="CODE *")
    e_code.pack(side="left", padx=(0, 8))
    e_pct = ctk.CTkEntry(frow, width=80, height=32, placeholder_text="% *")
    e_pct.pack(side="left", padx=8)
    e_cap = ctk.CTkEntry(frow, width=100, height=32, placeholder_text="Max ₹")
    e_cap.insert(0, "500")
    e_cap.pack(side="left", padx=8)
    e_from = ctk.CTkEntry(frow, width=120, height=32, placeholder_text="From YYYY-MM-DD")
    e_from.insert(0, str(date.today()))
    e_from.pack(side="left", padx=8)
    e_to = ctk.CTkEntry(frow, width=120, height=32, placeholder_text="To YYYY-MM-DD")
    e_to.insert(0, "2030-12-31")
    e_to.pack(side="left", padx=8)
    active_var = ctk.BooleanVar(value=True)
    ctk.CTkCheckBox(frow, text="Active", variable=active_var).pack(side="left", padx=8)
    msg = ctk.CTkLabel(form, text="", font=FONTS["body"])
    msg.pack(anchor="w", padx=16)

    brow = ctk.CTkFrame(form, fg_color="transparent")
    brow.pack(fill="x", padx=16, pady=(0, 12))
    ctk.CTkButton(brow, text="＋ Save Coupon", height=36, width=150, fg_color=COLORS["success"],
                  hover_color="#1E8449", command=lambda: on_save()).pack(side="left")
    ctk.CTkButton(brow, text="Clear", height=36, width=90, fg_color="#95A5B8",
                  hover_color="#7F8C9B", command=lambda: clear()).pack(side="left", padx=8)
    ctk.CTkButton(brow, text="On/Off Selected", height=36, width=140, fg_color=COLORS["accent"],
                  hover_color=COLORS["accent_hover"], command=lambda: on_toggle()).pack(side="left", padx=8)

    def clear():
        selected["id"] = None
        for e, v in ((e_code, ""), (e_pct, ""), (e_cap, "500"),
                     (e_from, str(date.today())), (e_to, "2030-12-31")):
            e.delete(0, "end")
            e.insert(0, v)
        active_var.set(True)
        msg.configure(text="")

    def on_save():
        try:
            db.save_coupon(selected["id"], e_code.get(), e_pct.get() or 0, e_cap.get() or 0,
                           e_from.get().strip(), e_to.get().strip(), active_var.get())
            msg.configure(text="✓ Coupon saved — usable in Billing immediately.",
                          text_color=COLORS["success"])
            clear()
            refresh()
        except ValueError as ex:
            msg.configure(text=f"⚠ {ex}", text_color=COLORS["danger"])

    def on_toggle():
        sel = tree.selection()
        if not sel or sel[0] not in id_map:
            msg.configure(text="⚠ Select a coupon first.", text_color=COLORS["danger"])
            return
        c = id_map[sel[0]]
        db.save_coupon(c["id"], c["code"], c["discount_percent"], c["max_discount"],
                       c["valid_from"], c["valid_to"], not c["active"])
        refresh()

    def on_select(_ev=None):
        sel = tree.selection()
        if sel and sel[0] in id_map:
            c = id_map[sel[0]]
            selected["id"] = c["id"]
            for e, v in ((e_code, c["code"]), (e_pct, str(c["discount_percent"])),
                         (e_cap, str(c["max_discount"])),
                         (e_from, c["valid_from"]), (e_to, c["valid_to"])):
                e.delete(0, "end")
                e.insert(0, v or "")
            active_var.set(bool(c["active"]))

    tree.bind("<<TreeviewSelect>>", on_select)
    refresh()
