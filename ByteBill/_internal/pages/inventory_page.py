"""STEP 3 — Inventory page: tabular add/edit + stock totals + low-stock alerts."""
from datetime import datetime

UNITS = ["pcs", "kg", "g", "ltr", "ml", "box", "mtr", "pkt"]
GST_SLABS = ["0", "5", "12", "18", "28"]


def _f(x, default=0.0):
    try:
        return float(str(x).strip() or default)
    except (ValueError, AttributeError):
        return default


def build(parent, app):
    import customtkinter as ctk
    from tkinter import ttk, messagebox
    from theme import COLORS, FONTS
    import database as db

    for w in parent.winfo_children():
        w.destroy()

    selected_id = {"id": None}

    # ---- Summary bar ----
    summ = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    summ.pack(fill="x", padx=4, pady=(4, 6))
    stat_labels = {}
    for i, key in enumerate(["total_products", "total_qty", "stock_value", "low_count"]):
        f = ctk.CTkFrame(summ, fg_color="transparent")
        f.grid(row=0, column=i, padx=18, pady=10, sticky="w")
        summ.grid_columnconfigure(i, weight=1)
        t = {"total_products": "Total Products", "total_qty": "Remaining Stock (qty)",
             "stock_value": "Stock Value", "low_count": "Low Stock Alerts"}[key]
        ctk.CTkLabel(f, text=t, font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w")
        v = ctk.CTkLabel(f, text="–", font=FONTS["heading"], text_color=COLORS["text_dark"])
        v.pack(anchor="w")
        stat_labels[key] = v

    def refresh_summary():
        s = db.inventory_summary()
        stat_labels["total_products"].configure(text=str(s["total_products"]))
        stat_labels["total_qty"].configure(text=f"{s['total_qty']:g}")
        stat_labels["stock_value"].configure(text=f"₹ {s['stock_value']:,.2f}")
        stat_labels["low_count"].configure(
            text=str(s["low_count"]),
            text_color=COLORS["danger"] if s["low_count"] else COLORS["success"])
        low_banner.configure(
            text=f"⚠ {s['low_count']} item(s) at/below low-stock limit — restock soon!" if s["low_count"]
            else "✓ Stock levels healthy.",
            text_color=COLORS["danger"] if s["low_count"] else COLORS["success"])

    low_banner = ctk.CTkLabel(parent, text="", font=FONTS["body"])
    low_banner.pack(anchor="w", padx=10)

    # ---- Search row ----
    srow = ctk.CTkFrame(parent, fg_color="transparent")
    srow.pack(fill="x", padx=4, pady=4)
    ctk.CTkLabel(srow, text="Search:", font=FONTS["body"], text_color=COLORS["text_dark"]).pack(side="left", padx=(4, 6))
    e_search = ctk.CTkEntry(srow, width=260, height=32, placeholder_text="name / code / SKU / brand…")
    e_search.pack(side="left")
    low_only = ctk.CTkCheckBox(srow, text="Low stock only")
    low_only.pack(side="left", padx=12)
    ctk.CTkButton(srow, text="Search", width=90, height=32, fg_color=COLORS["accent"],
                  hover_color=COLORS["accent_hover"], command=lambda: refresh_table()).pack(side="left", padx=4)
    ctk.CTkButton(srow, text="Clear", width=80, height=32, fg_color="#95A5B8",
                  hover_color="#7F8C9B",
                  command=lambda: (e_search.delete(0, "end"), refresh_table())).pack(side="left")

    # ---- Table (Treeview) ----
    tframe = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    tframe.pack(fill="both", expand=True, padx=4, pady=4)
    cols = ("code", "name", "brand", "sku", "unit", "price", "stock", "rack", "gst", "expiry")
    tree = ttk.Treeview(tframe, columns=cols, show="headings", height=9)
    heads = {"code": "Item Code", "name": "Product Name", "brand": "Brand", "sku": "SKU", "unit": "Unit",
             "price": "Sell Price", "stock": "Stock", "rack": "Rack", "gst": "GST%",
             "expiry": "Expiry"}
    widths = {"code": 95, "name": 190, "brand": 100, "sku": 90, "unit": 55, "price": 85,
              "stock": 65, "rack": 65, "gst": 55, "expiry": 95}
    for c in cols:
        tree.heading(c, text=heads[c])
        tree.column(c, width=widths[c], anchor="center" if c != "name" else "w")
    tree.tag_configure("low", background="#FDECEA", foreground="#C0392B")
    vsb = ttk.Scrollbar(tframe, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True, padx=(12, 0), pady=12)
    vsb.pack(side="right", fill="y", padx=(0, 12), pady=12)

    id_map = {}

    def refresh_table():
        for r in tree.get_children():
            tree.delete(r)
        id_map.clear()
        for p in db.list_products(e_search.get().strip(), bool(low_only.get())):
            low = p["stock_qty"] <= p["low_stock_limit"]
            iid = tree.insert("", "end", values=(
                p["item_code"], p["item_name"], p.get("brand", ""), p["sku"], p["unit"],
                f"{p['selling_price']:.2f}", f"{p['stock_qty']:g}", p["rack_no"],
                f"{p['gst_percent']:g}", p["expiry_date"] or "–"),
                tags=("low",) if low else ())
            id_map[iid] = p
        refresh_summary()

    # ---- Form ----
    form = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    form.pack(fill="x", padx=4, pady=(4, 2))
    ctk.CTkLabel(form, text="Add / Edit Item  ( * required )", font=FONTS["heading"],
                 text_color=COLORS["text_dark"]).pack(anchor="w", padx=16, pady=(10, 2))
    grid = ctk.CTkFrame(form, fg_color="transparent")
    grid.pack(fill="x", padx=16, pady=4)

    entries = {}

    def fld(r, c, label, key, default="", w=150, kind="entry", values=None):
        cell = ctk.CTkFrame(grid, fg_color="transparent")
        cell.grid(row=r, column=c, padx=8, pady=3, sticky="w")
        ctk.CTkLabel(cell, text=label, font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w")
        if kind == "option":
            e = ctk.CTkOptionMenu(cell, values=values, width=w)
            e.set(default)
        else:
            e = ctk.CTkEntry(cell, width=w, height=30)
            e.insert(0, str(default))
        e.pack(anchor="w")
        entries[key] = e
        return e

    fld(0, 0, "Product Name *", "item_name", w=190)
    fld(0, 1, "Item Code * (unique)", "item_code", w=150)
    fld(0, 2, "Brand (Generic / Company)", "brand", w=150)
    fld(0, 3, "SKU", "sku", w=130)
    fld(0, 4, "Unit", "unit", "pcs", 100, "option", UNITS)
    fld(0, 5, "GST %", "gst_percent", "18", 80, "option", GST_SLABS)
    fld(1, 0, "Selling Price *", "selling_price", "0", 150)
    fld(1, 1, "Purchase Price", "purchase_price", "0", 150)
    fld(1, 2, "Stock Qty *", "stock_qty", "0", 120)
    fld(1, 3, "Low-stock Limit", "low_stock_limit", "5", 120)
    fld(1, 4, "Rack No", "rack_no", w=110)
    fld(2, 0, "Mfg Date (YYYY-MM-DD)", "mfg_date", w=150)
    fld(2, 1, "Expiry Date (YYYY-MM-DD)", "expiry_date", w=150)
    fld(2, 2, "Serial / Batch / IMEI", "serial_no", w=190)
    ctk.CTkLabel(form, text="Brand: type Generic or company name (e.g. Samsung, Cipla).  Serial / Batch / IMEI: phone IMEI, medicine batch no. — printed on the bill.",
                 font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=16)
    msg = ctk.CTkLabel(form, text="", font=FONTS["body"])
    msg.pack(anchor="w", padx=16)

    brow = ctk.CTkFrame(form, fg_color="transparent")
    brow.pack(fill="x", padx=16, pady=(0, 12))
    btn_add = ctk.CTkButton(brow, text="＋ Add Item", height=36, width=140, fg_color=COLORS["success"],
                            hover_color="#1E8449", command=lambda: on_add())
    btn_add.pack(side="left", padx=(0, 8))
    ctk.CTkButton(brow, text="✔ Update Selected", height=36, width=150, fg_color=COLORS["accent"],
                  hover_color=COLORS["accent_hover"], command=lambda: on_update()).pack(side="left", padx=8)
    ctk.CTkButton(brow, text="🗑 Delete Selected", height=36, width=150, fg_color=COLORS["danger"],
                  hover_color="#C0392B", command=lambda: on_delete()).pack(side="left", padx=8)
    ctk.CTkButton(brow, text="Clear Form", height=36, width=110, fg_color="#95A5B8",
                  hover_color="#7F8C9B", command=lambda: clear_form()).pack(side="left", padx=8)
    serial_btn = ctk.CTkButton(brow, text="▤ Serials / Batches…", height=36, width=170,
                               fg_color=COLORS["navy"], hover_color=COLORS["navy_light"],
                               command=lambda: open_serial_manager())
    serial_btn.pack(side="left", padx=8)
    serial_info = ctk.CTkLabel(brow, text="", font=FONTS["small"], text_color=COLORS["text_muted"])
    serial_info.pack(side="left", padx=8)

    def open_serial_manager():
        import customtkinter as ctk2
        sel = tree.selection()
        if not sel or sel[0] not in id_map:
            # fall back to the item_code typed in the form
            code = entries["item_code"].get().strip()
            prods = db.list_products(code) if code else []
            p = next((x for x in prods if x["item_code"] == code), None)
            if p is None:
                msg.configure(text="⚠ Select an item in the table first (serials belong to a saved product).",
                              text_color=COLORS["danger"])
                return
        else:
            p = id_map[sel[0]]
        win = ctk2.CTkToplevel(app)
        win.title(f"Serials — {p['item_code']} {p['item_name']}")
        win.geometry("520x560")
        win.grab_set()
        ctk2.CTkLabel(win, text=f"{p['item_code']}  •  {p['item_name']}",
                      font=FONTS["heading"]).pack(pady=(14, 2))
        cnt_lbl = ctk2.CTkLabel(win, text="", font=FONTS["body"])
        cnt_lbl.pack()
        lst_frame = ctk2.CTkScrollableFrame(win, height=220)
        lst_frame.pack(fill="both", expand=True, padx=16, pady=8)
        status_lbl = ctk2.CTkLabel(win, text="One per line: IMEI / serial / batch code. Same number can't repeat.",
                                   font=FONTS["small"], text_color=COLORS["text_muted"])
        status_lbl.pack()
        bulk = ctk2.CTkTextbox(win, height=90)
        bulk.pack(fill="x", padx=16, pady=6)
        bulk.insert("1.0", "")

        def redraw():
            rows = db.list_serials(p["id"])
            for w in lst_frame.winfo_children():
                w.destroy()
            for r in rows:
                row = ctk2.CTkFrame(lst_frame, fg_color="transparent")
                row.pack(fill="x", pady=1)
                dot = "🟢" if r["status"] == "available" else "🔴"
                ctk2.CTkLabel(row, text=f"{dot}  {r['serial_no']}  ({r['status']})",
                              font=FONTS["body"], anchor="w").pack(side="left", padx=6)
                if r["status"] == "available":
                    ctk2.CTkButton(row, text="✕", width=36, height=24, fg_color=COLORS["danger"],
                                   command=lambda s=r["serial_no"]: (
                                       db.delete_serial(p["id"], s), redraw(), refresh_table())
                                   ).pack(side="right", padx=6)
            c = db.serial_count(p["id"])
            cnt_lbl.configure(text=f"Available: {c['available']}   •   Sold: {c['sold']}")
            refresh_table()

        def on_add_bulk():
            text = bulk.get("1.0", "end")
            parts = [x.strip() for x in text.replace(",", "\n").splitlines() if x.strip()]
            if not parts:
                status_lbl.configure(text="⚠ Type at least one number.", text_color=COLORS["danger"])
                return
            added, dupes = db.add_serials(p["id"], parts)
            bulk.delete("1.0", "end")
            extra = f"  Skipped dupes: {', '.join(dupes[:5])}" if dupes else ""
            status_lbl.configure(text=f"✓ Added {added}.{extra}", text_color=COLORS["success"])
            redraw()

        ctk2.CTkButton(win, text="＋ Add These Numbers", fg_color=COLORS["success"],
                       command=on_add_bulk).pack(pady=(0, 14))
        redraw()

    def form_data():
        return {
            "item_name": entries["item_name"].get().strip(),
            "item_code": entries["item_code"].get().strip(),
            "brand": entries["brand"].get().strip(),
            "sku": entries["sku"].get().strip(),
            "unit": entries["unit"].get(),
            "gst_percent": _f(entries["gst_percent"].get()),
            "selling_price": _f(entries["selling_price"].get()),
            "purchase_price": _f(entries["purchase_price"].get()),
            "stock_qty": _f(entries["stock_qty"].get()),
            "low_stock_limit": _f(entries["low_stock_limit"].get(), 5),
            "rack_no": entries["rack_no"].get().strip(),
            "mfg_date": entries["mfg_date"].get().strip(),
            "expiry_date": entries["expiry_date"].get().strip(),
            "serial_no": entries["serial_no"].get().strip(),
        }

    def clear_form():
        selected_id["id"] = None
        for k, e in entries.items():
            if isinstance(e, ctk.CTkOptionMenu):
                e.set("pcs" if k == "unit" else ("18" if k == "gst_percent" else e.get()))
            else:
                e.delete(0, "end")
                e.insert(0, {"selling_price": "0", "purchase_price": "0", "stock_qty": "0",
                             "low_stock_limit": "5"}.get(k, ""))
        msg.configure(text="")

    def fill_form(p):
        selected_id["id"] = p["id"]
        for k, e in entries.items():
            v = p.get(k, "")
            if isinstance(e, ctk.CTkOptionMenu):
                try:
                    e.set(str(v) if v else ("pcs" if k == "unit" else "18"))
                except Exception:
                    pass
            else:
                e.delete(0, "end")
                e.insert(0, str(v) if v is not None else "")

    def on_tree_select(_ev=None):
        sel = tree.selection()
        if sel and sel[0] in id_map:
            fill_form(id_map[sel[0]])
            p = id_map[sel[0]]
            try:
                c = db.serial_count(p["id"])
                serial_info.configure(
                    text=f"Tracked: {c['available']} avail / {c['sold']} sold"
                    if (c["available"] + c["sold"]) else "No serials tracked")
            except Exception:
                pass
            msg.configure(text=f"Editing: {id_map[sel[0]]['item_code']}", text_color=COLORS["accent"])

    tree.bind("<<TreeviewSelect>>", on_tree_select)

    def on_add():
        d = form_data()
        try:
            if not d["item_name"] or not d["item_code"]:
                raise ValueError("Product Name and Item Code are required")
            db.add_product(d)
            msg.configure(text=f"✓ Added {d['item_code']}", text_color=COLORS["success"])
            clear_form()
            refresh_table()
        except ValueError as ex:
            msg.configure(text=f"⚠ {ex}", text_color=COLORS["danger"])

    def on_update():
        if not selected_id["id"]:
            msg.configure(text="⚠ Select an item in the table first.", text_color=COLORS["danger"])
            return
        d = form_data()
        try:
            db.update_product(selected_id["id"], d)
            msg.configure(text="✓ Updated.", text_color=COLORS["success"])
            refresh_table()
        except ValueError as ex:
            msg.configure(text=f"⚠ {ex}", text_color=COLORS["danger"])

    def on_delete():
        sel = tree.selection()
        if not sel or sel[0] not in id_map:
            msg.configure(text="⚠ Select an item in the table first.", text_color=COLORS["danger"])
            return
        p = id_map[sel[0]]
        if messagebox.askyesno("Delete", f"Delete {p['item_code']} — {p['item_name']}?"):
            db.delete_product(p["id"])
            clear_form()
            refresh_table()

    e_search.bind("<Return>", lambda _e: refresh_table())
    refresh_table()
