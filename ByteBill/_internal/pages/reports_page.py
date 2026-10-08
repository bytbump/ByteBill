"""STEP 5+6 — Reports: Bills history | Sales & GST | Stock & Access export."""
from datetime import date


def _f(x, default=0.0):
    try:
        return float(str(x).strip() or default)
    except (ValueError, AttributeError):
        return default


def build(parent, app):
    import customtkinter as ctk
    from theme import COLORS, FONTS

    for w in parent.winfo_children():
        w.destroy()

    tabs = ctk.CTkFrame(parent, fg_color="transparent")
    tabs.pack(fill="x", padx=4, pady=(4, 0))
    body = ctk.CTkFrame(parent, fg_color="transparent")
    body.pack(fill="both", expand=True)
    btns = {}

    def show(which):
        for k, b in btns.items():
            b.configure(fg_color=COLORS["accent"] if k == which else "#95A5B8")
        for w in body.winfo_children():
            w.destroy()
        {"bills": _section_bills, "sales": _section_sales,
         "stock": _section_stock}[which](body, app)

    for key, label in [("bills", "🧾 Bills History"), ("sales", "📊 Sales & GST"),
                       ("stock", "📦 Stock & Access")]:
        b = ctk.CTkButton(tabs, text=label, height=34, width=170,
                          fg_color=COLORS["accent"] if key == "bills" else "#95A5B8",
                          command=lambda k=key: show(k))
        b.pack(side="left", padx=(0, 8))
        btns[key] = b
    _section_bills(body, app)


# ---------------- Bills history (Step 5, unchanged) ----------------

def _section_bills(parent, app):
    import customtkinter as ctk
    from tkinter import ttk, messagebox
    from theme import COLORS, FONTS
    import database as db
    import pdf_bill

    # ---- search row ----
    srow = ctk.CTkFrame(parent, fg_color="transparent")
    srow.pack(fill="x", padx=4, pady=4)
    ctk.CTkLabel(srow, text="Search bills:", font=FONTS["body"]).pack(side="left", padx=(4, 6))
    e_search = ctk.CTkEntry(srow, width=280, height=32,
                            placeholder_text="invoice no / customer / mobile…")
    e_search.pack(side="left")
    ctk.CTkButton(srow, text="Search", width=90, height=32, fg_color=COLORS["accent"],
                  hover_color=COLORS["accent_hover"],
                  command=lambda: refresh()).pack(side="left", padx=6)
    ctk.CTkButton(srow, text="Clear", width=80, height=32, fg_color="#95A5B8",
                  hover_color="#7F8C9B",
                  command=lambda: (e_search.delete(0, "end"), refresh())).pack(side="left")
    msg = ctk.CTkLabel(parent, text="", font=FONTS["body"])
    msg.pack(anchor="w", padx=10)

    # ---- table ----
    tframe = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    tframe.pack(fill="both", expand=True, padx=4, pady=4)
    cols = ("inv", "date", "customer", "mobile", "items", "total")
    tree = ttk.Treeview(tframe, columns=cols, show="headings", height=12)
    for c, h, wd in [("inv", "Invoice No", 150), ("date", "Date", 100),
                     ("customer", "Customer", 220), ("mobile", "Mobile", 120),
                     ("items", "Lines", 60), ("total", "Grand Total", 120)]:
        tree.heading(c, text=h)
        tree.column(c, width=wd, anchor="center" if c != "customer" else "w")
    tree.pack(fill="both", expand=True, padx=12, pady=12)
    id_map = {}

    def refresh():
        for r in tree.get_children():
            tree.delete(r)
        id_map.clear()
        for b in db.list_bills(e_search.get().strip()):
            n_items = len(db.get_bill_full(b["id"])[1])
            iid = tree.insert("", "end", values=(
                b["invoice_no"], b["bill_date"], b["customer_name"],
                b["customer_mobile"], n_items, f"₹ {b['grand_total']:.2f}"))
            id_map[iid] = b
        s = db.get_connection()
        tot = s.execute("SELECT COUNT(*) c, COALESCE(SUM(grand_total),0) g FROM bills").fetchone()
        s.close()
        msg.configure(text=f"{tot['c']} bill(s)  •  lifetime sales ₹ {tot['g']:.2f}",
                      text_color=COLORS["text_muted"])

    def selected():
        sel = tree.selection()
        if not sel or sel[0] not in id_map:
            messagebox.showwarning("Bills", "Select a bill in the table first.")
            return None
        return id_map[sel[0]]

    # ---- action buttons ----
    brow = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    brow.pack(fill="x", padx=4, pady=4)
    ctk.CTkButton(brow, text="📄 Open PDF", height=36, width=140, fg_color=COLORS["accent"],
                  hover_color=COLORS["accent_hover"], command=lambda: on_open()).pack(side="left", padx=8, pady=8)
    ctk.CTkButton(brow, text="↻ Regenerate PDF", height=36, width=160, fg_color=COLORS["navy"],
                  hover_color=COLORS["navy_light"], command=lambda: on_regen()).pack(side="left", padx=8, pady=8)
    ctk.CTkButton(brow, text="✎ Edit Bill", height=36, width=130, fg_color=COLORS["success"],
                  hover_color="#1E8449", command=lambda: on_edit()).pack(side="left", padx=8, pady=8)
    ctk.CTkButton(brow, text="🗑 Delete Bill", height=36, width=140, fg_color=COLORS["danger"],
                  hover_color="#C0392B", command=lambda: on_delete()).pack(side="left", padx=8, pady=8)
    om_paper = ctk.CTkOptionMenu(brow, values=["A4", "Thermal 80mm", "Thermal 58mm"], width=140)
    try:
        _pv = (db.get_settings().get("paper_size") or "A4").upper()
        om_paper.set("Thermal 80mm" if _pv == "T80" else ("Thermal 58mm" if _pv == "T58" else "A4"))
    except Exception:
        pass
    om_paper.pack(side="left", padx=8, pady=8)
    ctk.CTkButton(brow, text="🖨 Print Bill", height=36, width=130, fg_color=COLORS["accent"],
                  hover_color=COLORS["accent_hover"], command=lambda: on_print()).pack(side="left", padx=8, pady=8)
    ctk.CTkLabel(parent, text="Print opens the bill sized for your printer — choose the thermal printer, Actual size, and print.",
                 font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=10)

    def on_print():
        b = selected()
        if not b:
            return
        code = {"THERMAL 80MM": "T80", "THERMAL 58MM": "T58"}.get(om_paper.get().upper(), "A4")
        try:
            p = pdf_bill.generate_bill_pdf(b["id"], code)
            pdf_bill.open_file(p)
        except Exception as ex:
            messagebox.showerror("Print", f"Failed: {ex}")

    def on_open():
        b = selected()
        if not b:
            return
        hdr, _ = db.get_bill_full(b["id"])
        p = hdr.get("pdf_path") or ""
        if not p or not __import__("os").path.exists(p):
            try:
                p = pdf_bill.generate_bill_pdf(b["id"])
            except Exception as ex:
                messagebox.showerror("PDF", f"Could not build PDF: {ex}")
                return
        try:
            pdf_bill.open_file(p)
        except Exception as ex:
            messagebox.showerror("PDF", f"Saved at {p}\nBut auto-open failed: {ex}")

    def on_regen():
        b = selected()
        if not b:
            return
        try:
            p = pdf_bill.generate_bill_pdf(b["id"])
            messagebox.showinfo("PDF", f"Regenerated:\n{p}")
        except Exception as ex:
            messagebox.showerror("PDF", f"Failed: {ex}")

    def on_delete():
        b = selected()
        if not b:
            return
        if not messagebox.askyesno("Delete Bill",
                                   f"Delete {b['invoice_no']} (₹ {b['grand_total']:.2f})?\n"
                                   "Stock + serials will be returned."):
            return
        try:
            db.delete_bill(b["id"])
            refresh()
            messagebox.showinfo("Deleted", f"{b['invoice_no']} deleted, stock restored.")
        except Exception as ex:
            messagebox.showerror("Delete", str(ex))

    def on_edit():
        b = selected()
        if not b:
            return
        hdr, items = db.get_bill_full(b["id"])
        win = ctk.CTkToplevel(app)
        win.title(f"Edit {hdr['invoice_no']}")
        win.geometry("860x640")
        win.grab_set()
        ctk.CTkLabel(win, text=f"Edit {hdr['invoice_no']}  (same invoice no. Stock re-checked on save.)",
                     font=FONTS["heading"]).pack(pady=(12, 4))

        f1 = ctk.CTkFrame(win, fg_color="transparent")
        f1.pack(fill="x", padx=16)
        e_name = ctk.CTkEntry(f1, width=220, height=30)
        e_name.insert(0, hdr["customer_name"])
        e_name.pack(side="left", padx=4)
        e_addr = ctk.CTkEntry(f1, width=260, height=30)
        e_addr.insert(0, hdr["customer_address"] or "")
        e_addr.pack(side="left", padx=4)
        e_mob = ctk.CTkEntry(f1, width=130, height=30)
        e_mob.insert(0, hdr["customer_mobile"] or "")
        e_mob.pack(side="left", padx=4)

        f2 = ctk.CTkFrame(win, fg_color="transparent")
        f2.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(f2, text="Overall%").pack(side="left")
        e_over = ctk.CTkEntry(f2, width=60, height=30)
        e_over.insert(0, str(hdr["overall_discount_percent"]))
        e_over.pack(side="left", padx=4)
        ctk.CTkLabel(f2, text="Festive%").pack(side="left", padx=(8, 0))
        e_fest = ctk.CTkEntry(f2, width=60, height=30)
        e_fest.insert(0, str(hdr["festive_percent"]))
        e_fest.pack(side="left", padx=4)
        ctk.CTkLabel(f2, text="Coupon").pack(side="left", padx=(8, 0))
        e_coupon = ctk.CTkEntry(f2, width=120, height=30)
        e_coupon.insert(0, hdr["coupon_code"] or "")
        e_coupon.pack(side="left", padx=4)

        cols2 = ("code", "name", "qty", "price", "disc", "serial")
        etree = ttk.Treeview(win, columns=cols2, show="headings", height=8)
        for c, h, wd in [("code", "Code", 100), ("name", "Product", 220), ("qty", "Qty", 60),
                         ("price", "Price", 90), ("disc", "Disc%", 60), ("serial", "Serial/Batch", 170)]:
            etree.heading(c, text=h)
            etree.column(c, width=wd)
        etree.pack(fill="both", expand=True, padx=16, pady=4)
        row_ids = []
        for it in items:
            row_ids.append(etree.insert("", "end", values=(
                it["item_code"], it["item_name"], f"{it['qty']:g}",
                f"{it['price']:.2f}", f"{it['discount_percent']:g}", it.get("serial_no") or "")))

        f3 = ctk.CTkFrame(win, fg_color="transparent")
        f3.pack(fill="x", padx=16, pady=6)
        ctk.CTkLabel(f3, text="Selected line → Qty / Disc% / Serial:").pack(side="left")
        e_q = ctk.CTkEntry(f3, width=70, height=30)
        e_q.pack(side="left", padx=4)
        e_d = ctk.CTkEntry(f3, width=70, height=30)
        e_d.pack(side="left", padx=4)
        e_s = ctk.CTkEntry(f3, width=170, height=30)
        e_s.pack(side="left", padx=4)

        def load_line(_ev=None):
            sel = etree.selection()
            if sel:
                v = etree.item(sel[0], "values")
                for e, val in ((e_q, v[2]), (e_d, v[4]), (e_s, v[5])):
                    e.delete(0, "end")
                    e.insert(0, val)

        def apply_line():
            sel = etree.selection()
            if not sel:
                return
            v = list(etree.item(sel[0], "values"))
            v[2], v[4], v[5] = e_q.get() or v[2], e_d.get() or v[4], e_s.get()
            etree.item(sel[0], values=v)

        etree.bind("<<TreeviewSelect>>", load_line)
        ctk.CTkButton(f3, text="Apply to line", width=110, height=30,
                      fg_color=COLORS["accent"], command=apply_line).pack(side="left", padx=6)

        def on_save():
            new_lines = []
            for rid in row_ids:
                v = etree.item(rid, "values")
                old = next(x for x in items if x["item_code"] == v[0])
                new_lines.append({
                    "product_id": old["product_id"], "item_name": old["item_name"],
                    "item_code": old["item_code"], "brand": old.get("brand", ""),
                    "serial_no": v[5].strip(), "qty": _f(v[2], 0),
                    "price": float(old["price"]),
                    "discount_percent": _f(v[4], 0),
                    "gst_percent": float(old["gst_percent"])})
            try:
                t = db.update_bill(b["id"],
                                   {"name": e_name.get(), "address": e_addr.get(), "mobile": e_mob.get()},
                                   new_lines, _f(e_over.get()), _f(e_fest.get()),
                                   e_coupon.get().strip())
                try:
                    pdf_bill.generate_bill_pdf(b["id"])
                except Exception:
                    pass
                win.destroy()
                refresh()
                messagebox.showinfo("Saved",
                                    f"{hdr['invoice_no']} updated — new total ₹ {t['grand_total']:.2f}")
            except ValueError as ex:
                messagebox.showerror("Cannot save", str(ex))

        ctk.CTkButton(win, text="💾 Save Changes (same invoice no)", height=40,
                      fg_color=COLORS["success"], command=on_save).pack(pady=10)

    e_search.bind("<Return>", lambda _e: refresh())
    refresh()


# ---------------- Sales & GST (Step 6) ----------------

def _section_sales(parent, app):
    import customtkinter as ctk
    from tkinter import ttk, messagebox, filedialog
    from theme import COLORS, FONTS
    import database as db

    frow = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    frow.pack(fill="x", padx=4, pady=4)
    ctk.CTkLabel(frow, text="From (YYYY-MM-DD)", font=FONTS["body"]).pack(side="left", padx=(16, 4), pady=12)
    e_from = ctk.CTkEntry(frow, width=120, height=32)
    e_from.insert(0, str(date.today().replace(day=1)))
    e_from.pack(side="left")
    ctk.CTkLabel(frow, text="To", font=FONTS["body"]).pack(side="left", padx=(12, 4))
    e_to = ctk.CTkEntry(frow, width=120, height=32)
    e_to.insert(0, str(date.today()))
    e_to.pack(side="left")
    ctk.CTkButton(frow, text="Generate", width=120, height=32, fg_color=COLORS["accent"],
                  hover_color=COLORS["accent_hover"],
                  command=lambda: run()).pack(side="left", padx=12)
    ctk.CTkButton(frow, text="⬇ Export CSV", width=130, height=32, fg_color=COLORS["success"],
                  hover_color="#1E8449", command=lambda: on_csv()).pack(side="left")
    cards = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    cards.pack(fill="x", padx=4, pady=4)
    stat = {}
    for i, key in enumerate(["bills", "sales", "discounts", "taxable", "gst"]):
        f = ctk.CTkFrame(cards, fg_color="transparent")
        f.grid(row=0, column=i, padx=16, pady=10, sticky="w")
        cards.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(f, text={"bills": "Bills", "sales": "Total Sales", "discounts": "Discounts Given",
                              "taxable": "Taxable Value", "gst": "GST Collected"}[key],
                     font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w")
        v = ctk.CTkLabel(f, text="–", font=FONTS["heading"], text_color=COLORS["text_dark"])
        v.pack(anchor="w")
        stat[key] = v
    slab_frame = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    slab_frame.pack(fill="both", expand=True, padx=4, pady=4)
    ctk.CTkLabel(slab_frame, text="GST Slab Breakup (taxable allocated per line — reconciles with bill GST)",
                 font=FONTS["heading"], text_color=COLORS["text_dark"]).pack(anchor="w", padx=16, pady=(10, 2))
    tree = ttk.Treeview(slab_frame, columns=("rate", "taxable", "gst", "total"),
                        show="headings", height=8)
    for c, h in [("rate", "GST Slab %"), ("taxable", "Taxable ₹"), ("gst", "GST ₹"), ("total", "Total ₹")]:
        tree.heading(c, text=h)
        tree.column(c, width=150, anchor="center")
    tree.pack(fill="both", expand=True, padx=16, pady=8)
    cache = {"rep": None}

    def run():
        try:
            rep = db.sales_report(e_from.get().strip(), e_to.get().strip())
        except Exception as ex:
            messagebox.showerror("Report", f"Check dates (YYYY-MM-DD).\n{ex}")
            return
        cache["rep"] = rep
        t = rep["totals"]
        stat["bills"].configure(text=str(t["bills"]))
        stat["sales"].configure(text=f"₹ {t['sales']:,.2f}")
        stat["discounts"].configure(text=f"₹ {t['discounts']:,.2f}")
        stat["taxable"].configure(text=f"₹ {t['taxable']:,.2f}")
        stat["gst"].configure(text=f"₹ {t['gst']:,.2f}")
        for r in tree.get_children():
            tree.delete(r)
        for s in rep["slabs"]:
            tree.insert("", "end", values=(f"{s['rate']:g}%", f"₹ {s['taxable']:,.2f}",
                                           f"₹ {s['gst']:,.2f}", f"₹ {s['taxable'] + s['gst']:,.2f}"))

    def on_csv():
        rep = cache.get("rep")
        if not rep:
            messagebox.showwarning("CSV", "Generate the report first.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".csv",
                                         filetypes=[("CSV", "*.csv")],
                                         initialfile=f"sales_{e_from.get()}_{e_to.get()}.csv")
        if not p:
            return
        import csv
        with open(p, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["invoice_no", "date", "customer", "mobile", "subtotal", "discounts",
                        "taxable", "gst", "grand_total", "coupon"])
            for b in rep["bills"]:
                disc = (float(b["item_discount_total"]) + float(b["overall_discount_amt"])
                        + float(b["festive_amt"]) + float(b["coupon_discount_amt"]))
                w.writerow([b["invoice_no"], b["bill_date"], b["customer_name"], b["customer_mobile"],
                            b["subtotal"], round(disc, 2), b.get("taxable_value", 0),
                            b["gst_total"], b["grand_total"], b["coupon_code"]])
            w.writerow([])
            w.writerow(["GST slab %", "Taxable", "GST"])
            for s in rep["slabs"]:
                w.writerow([s["rate"], s["taxable"], s["gst"]])
        messagebox.showinfo("CSV", f"Saved:\n{p}")

    run()


# ---------------- Stock & Access export (Step 6) ----------------

def _section_stock(parent, app):
    import customtkinter as ctk
    from tkinter import ttk, messagebox, filedialog
    from theme import COLORS, FONTS
    import database as db

    summ = db.inventory_summary()
    cards = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    cards.pack(fill="x", padx=4, pady=4)
    for i, (label, val, col) in enumerate([
        ("Products", str(summ["total_products"]), COLORS["text_dark"]),
        ("Stock Qty", f"{summ['total_qty']:g}", COLORS["text_dark"]),
        ("Stock Value", f"₹ {summ['stock_value']:,.2f}", COLORS["text_dark"]),
        ("Low Stock", str(summ["low_count"]),
         COLORS["danger"] if summ["low_count"] else COLORS["success"])]):
        f = ctk.CTkFrame(cards, fg_color="transparent")
        f.grid(row=0, column=i, padx=16, pady=10, sticky="w")
        cards.grid_columnconfigure(i, weight=1)
        ctk.CTkLabel(f, text=label, font=FONTS["small"],
                     text_color=COLORS["text_muted"]).pack(anchor="w")
        ctk.CTkLabel(f, text=val, font=FONTS["heading"], text_color=col).pack(anchor="w")

    tframe = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    tframe.pack(fill="both", expand=True, padx=4, pady=4)
    ctk.CTkLabel(tframe, text="Current Stock (low-stock rows in red)",
                 font=FONTS["heading"], text_color=COLORS["text_dark"]).pack(anchor="w", padx=16, pady=(10, 2))
    tree = ttk.Treeview(tframe, columns=("code", "name", "brand", "stock", "limit", "value"),
                        show="headings", height=10)
    for c, h, wd in [("code", "Code", 110), ("name", "Product", 220), ("brand", "Brand", 110),
                     ("stock", "Stock", 80), ("limit", "Low Limit", 80), ("value", "Value ₹", 110)]:
        tree.heading(c, text=h)
        tree.column(c, width=wd, anchor="center" if c != "name" else "w")
    tree.tag_configure("low", background="#FDECEA", foreground="#C0392B")
    tree.pack(fill="both", expand=True, padx=16, pady=4)
    for p in db.list_products():
        low = p["stock_qty"] <= p["low_stock_limit"]
        tree.insert("", "end", values=(
            p["item_code"], p["item_name"], p.get("brand", ""), f"{p['stock_qty']:g}",
            f"{p['low_stock_limit']:g}", f"{p['stock_qty'] * p['selling_price']:,.2f}"),
            tags=("low",) if low else ())

    brow = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    brow.pack(fill="x", padx=4, pady=4)
    ctk.CTkButton(brow, text="⬇ Stock CSV", height=36, width=140, fg_color=COLORS["success"],
                  hover_color="#1E8449", command=lambda: on_stock_csv()).pack(side="left", padx=8, pady=8)
    ctk.CTkButton(brow, text="⤴ Export to Access (.accdb)", height=36, width=220,
                  fg_color=COLORS["navy"], hover_color=COLORS["navy_light"],
                  command=lambda: on_access()).pack(side="left", padx=8, pady=8)
    ctk.CTkLabel(parent, text="Access export needs Windows + Access Database Engine (free from Microsoft) + pip install pyodbc.",
                 font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=10)

    def on_stock_csv():
        p = filedialog.asksaveasfilename(defaultextension=".csv",
                                         filetypes=[("CSV", "*.csv")], initialfile="stock.csv")
        if not p:
            return
        import csv
        with open(p, "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["item_code", "item_name", "brand", "sku", "unit", "rack",
                        "selling_price", "stock_qty", "low_limit", "stock_value"])
            for pr in db.list_products():
                w.writerow([pr["item_code"], pr["item_name"], pr.get("brand", ""), pr["sku"],
                            pr["unit"], pr["rack_no"], pr["selling_price"], pr["stock_qty"],
                            pr["low_stock_limit"], round(pr["stock_qty"] * pr["selling_price"], 2)])
        messagebox.showinfo("CSV", f"Saved:\n{p}")

    def on_access():
        p = filedialog.asksaveasfilename(defaultextension=".accdb",
                                         filetypes=[("Access DB", "*.accdb")],
                                         initialfile="billing_data.accdb")
        if not p:
            return
        try:
            db.export_to_access(p)
            messagebox.showinfo("Access", f"Exported all 7 tables to:\n{p}")
        except ImportError:
            messagebox.showerror("Access", "Run on Windows with:  pip install pyodbc")
        except Exception as ex:
            messagebox.showerror("Access",
                                 f"Failed: {ex}\n\nNeeds Microsoft Access Database Engine (ODBC).")
