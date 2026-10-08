"""STEP 4 — Billing page: customer + product autofill + qty + item/overall/festive/coupon discounts."""
from datetime import date


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

    cart = []           # [{product_id, item_name, item_code, brand, serial_no, qty, ...}]
    picked = {"p": None}

    # ---------- Customer card ----------
    cc = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    cc.pack(fill="x", padx=4, pady=(4, 6))
    ctk.CTkLabel(cc, text="1  •  Customer", font=FONTS["heading"],
                 text_color=COLORS["text_dark"]).pack(anchor="w", padx=16, pady=(10, 2))
    crow = ctk.CTkFrame(cc, fg_color="transparent")
    crow.pack(fill="x", padx=16, pady=(0, 12))
    e_cname = ctk.CTkEntry(crow, width=220, height=32, placeholder_text="Customer name *")
    e_cname.pack(side="left", padx=(0, 8))
    e_caddr = ctk.CTkEntry(crow, width=300, height=32, placeholder_text="Address")
    e_caddr.pack(side="left", padx=8)
    e_cmob = ctk.CTkEntry(crow, width=160, height=32, placeholder_text="Mobile")
    e_cmob.pack(side="left", padx=8)

    # ---------- Add-product card ----------
    pc = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    pc.pack(fill="x", padx=4, pady=6)
    ctk.CTkLabel(pc, text="2  •  Add Product  (type name / code / SKU / brand → autofill)", font=FONTS["heading"],
                 text_color=COLORS["text_dark"]).pack(anchor="w", padx=16, pady=(10, 2))
    prow = ctk.CTkFrame(pc, fg_color="transparent")
    prow.pack(fill="x", padx=16, pady=2)
    e_search = ctk.CTkEntry(prow, width=220, height=32, placeholder_text="🔍 name / code / brand…")
    e_search.pack(side="left", padx=(0, 8))
    info_lbl = ctk.CTkLabel(prow, text="No product selected", font=FONTS["small"],
                            text_color=COLORS["text_muted"], width=280, anchor="w")
    info_lbl.pack(side="left", padx=8)
    ctk.CTkLabel(prow, text="Serial/Batch/IMEI", font=FONTS["body"]).pack(side="left", padx=(8, 2))
    e_serial = ctk.CTkComboBox(prow, width=170, height=32, values=[],
                               command=None)
    e_serial.set("Pick or type…")
    e_serial.pack(side="left")
    # second row so Qty/Disc/Add never overflow off-screen
    prow2 = ctk.CTkFrame(pc, fg_color="transparent")
    prow2.pack(fill="x", padx=16, pady=(2, 6))
    ctk.CTkLabel(prow2, text="Qty", font=FONTS["body"]).pack(side="left", padx=(0, 2))
    e_qty = ctk.CTkEntry(prow2, width=70, height=32)
    e_qty.insert(0, "1")
    e_qty.pack(side="left")
    ctk.CTkLabel(prow2, text="Item Disc%", font=FONTS["body"]).pack(side="left", padx=(8, 2))
    e_idisc = ctk.CTkEntry(prow2, width=70, height=32)
    e_idisc.insert(0, "0")
    e_idisc.pack(side="left")
    btn_add = ctk.CTkButton(prow2, text="＋ Add to Bill", width=160, height=36, fg_color=COLORS["success"],
                            hover_color="#1E8449", command=lambda: on_add_line())
    btn_add.pack(side="left", padx=10)

    # suggestion dropdown
    sugg = ctk.CTkFrame(pc, fg_color=COLORS["bg"], corner_radius=8)
    sugg_box = None

    def hide_sugg():
        nonlocal sugg_box
        if sugg_box is not None:
            sugg_box.destroy()
            sugg_box = None

    def on_type(_ev=None):
        nonlocal sugg_box
        hide_sugg()
        q = e_search.get().strip()
        if len(q) < 1:
            return
        matches = db.search_products(q, 8)
        if not matches:
            return
        sugg_box = ctk.CTkFrame(pc, fg_color=COLORS["bg"], corner_radius=8)
        sugg_box.pack(fill="x", padx=16, pady=4)
        for m in matches:
            brand = f"[{m.get('brand','')}] " if m.get("brand") else ""
            b = ctk.CTkButton(sugg_box, fg_color="transparent", hover_color="#D6E4F0",
                              text_color=COLORS["text_dark"], anchor="w", height=28,
                              text=f"{brand}{m['item_name']}  |  {m['item_code']}  |  ₹{m['selling_price']:g}  |  stock {m['stock_qty']:g}",
                              command=lambda mm=m: pick(mm))
            b.pack(fill="x", padx=4, pady=1)

    def pick(m):
        picked["p"] = m
        e_search.delete(0, "end")
        e_search.insert(0, m["item_name"])
        brand = f"[{m.get('brand','')}] " if m.get("brand") else ""
        info_lbl.configure(
            text=f"{brand}{m['item_code']} • ₹{m['selling_price']:g} • GST {m['gst_percent']:g}% • stock {m['stock_qty']:g}",
            text_color=COLORS["text_dark"])
        # load tracked numbers into the dropdown; free batch text still allowed
        try:
            tracked = db.available_serials(m["id"], "", 200)
        except Exception:
            tracked = []
        e_serial.configure(values=tracked)
        if m.get("serial_no"):
            e_serial.set(m["serial_no"])
        elif tracked:
            e_serial.set(tracked[0])
        else:
            e_serial.set("")
        try:
            c = db.serial_count(m["id"])
            if tracked:
                info_lbl.configure(
                    text=info_lbl.cget("text") + f"  •  📦 {len(tracked)} to pick from ▼",
                    text_color=COLORS["text_dark"])
        except Exception:
            pass
        hide_sugg()

    e_search.bind("<KeyRelease>", on_type)

    def on_add_line():
        p = picked["p"]
        # allow direct code match if user typed exact code without picking
        if p is None:
            q = e_search.get().strip()
            if q:
                m = db.get_product_by_code(q) or (db.search_products(q, 1) or [None])[0]
                if m:
                    pick(m)
                    p = m
        if p is None:
            msg.configure(text="⚠ Search and pick a product first.", text_color=COLORS["danger"])
            return
        qty = _f(e_qty.get(), 0)
        disc = _f(e_idisc.get(), 0)
        serial = e_serial.get().strip()
        if serial == "Pick or type…":
            serial = ""
        if qty <= 0:
            msg.configure(text="⚠ Qty must be > 0.", text_color=COLORS["danger"])
            return
        if disc < 0 or disc > 90:
            msg.configure(text="⚠ Item discount must be 0–90%.", text_color=COLORS["danger"])
            return
        if qty > float(p["stock_qty"]):
            msg.configure(text=f"⚠ Only {p['stock_qty']:g} in stock.", text_color=COLORS["danger"])
            return
        # tracked-serial rule: one IMEI = one unit → one line, qty 1
        try:
            if serial and serial in db.available_serials(p["id"], serial, 50) and qty != 1:
                msg.configure(text="⚠ Tracked serial/IMEI sells one unit per line — set Qty 1 "
                                   "(add a line per IMEI; batch codes may use qty > 1).",
                              text_color=COLORS["danger"])
                return
        except ValueError:
            raise
        except Exception:
            pass
        # merge if same product + same serial already in cart
        for ln in cart:
            if ln["product_id"] == p["id"] and ln.get("serial_no", "") == serial:
                if ln["qty"] + qty > float(p["stock_qty"]):
                    msg.configure(text=f"⚠ Cart would exceed stock ({p['stock_qty']:g}).",
                                  text_color=COLORS["danger"])
                    return
                ln["qty"] += qty
                ln["discount_percent"] = disc
                break
        else:
            cart.append({"product_id": p["id"], "item_name": p["item_name"],
                         "item_code": p["item_code"], "brand": p.get("brand", ""),
                         "serial_no": serial, "qty": qty, "price": float(p["selling_price"]),
                         "discount_percent": disc, "gst_percent": float(p["gst_percent"]),
                         "stock": float(p["stock_qty"])})
        picked["p"] = None
        e_search.delete(0, "end")
        e_serial.configure(values=[])
        e_serial.set("")
        e_qty.delete(0, "end"); e_qty.insert(0, "1")
        e_idisc.delete(0, "end"); e_idisc.insert(0, "0")
        info_lbl.configure(text="No product selected", text_color=COLORS["text_muted"])
        msg.configure(text="")
        refresh_cart()

    # ---------- Cart card ----------
    kc = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    kc.pack(fill="both", expand=True, padx=4, pady=6)
    ctk.CTkLabel(kc, text="3  •  Bill Items", font=FONTS["heading"],
                 text_color=COLORS["text_dark"]).pack(anchor="w", padx=16, pady=(10, 2))
    cols = ("code", "brand", "name", "serial", "qty", "price", "disc", "gst", "total")
    tree = ttk.Treeview(kc, columns=cols, show="headings", height=6)
    for c, h, wd in [("code", "Code", 90), ("brand", "Brand", 90), ("name", "Product", 180),
                     ("serial", "Serial/Batch/IMEI", 140), ("qty", "Qty", 55),
                     ("price", "Price", 85), ("disc", "Disc%", 55), ("gst", "GST%", 55),
                     ("total", "Line Total", 100)]:
        tree.heading(c, text=h)
        tree.column(c, width=wd, anchor="center" if c not in ("name", "serial") else "w")
    tree.pack(fill="both", expand=True, padx=16, pady=4)
    krow = ctk.CTkFrame(kc, fg_color="transparent")
    krow.pack(fill="x", padx=16, pady=(0, 8))
    ctk.CTkButton(krow, text="Remove Selected", width=140, height=30, fg_color=COLORS["danger"],
                  hover_color="#C0392B", command=lambda: on_remove()).pack(side="left")
    ctk.CTkButton(krow, text="Clear Cart", width=110, height=30, fg_color="#95A5B8",
                  hover_color="#7F8C9B",
                  command=lambda: (cart.clear(), refresh_cart())).pack(side="left", padx=8)

    def on_remove():
        sel = tree.selection()
        if not sel:
            return
        idx = tree.index(sel[0])
        if 0 <= idx < len(cart):
            cart.pop(idx)
            refresh_cart()

    # ---------- Discounts + totals ----------
    dc = ctk.CTkFrame(parent, fg_color=COLORS["card"], corner_radius=12)
    dc.pack(fill="x", padx=4, pady=6)
    drow = ctk.CTkFrame(dc, fg_color="transparent")
    drow.pack(fill="x", padx=16, pady=8)
    s = db.get_settings()
    ctk.CTkLabel(drow, text="Overall Disc%", font=FONTS["body"]).pack(side="left")
    e_over = ctk.CTkEntry(drow, width=70, height=30)
    e_over.insert(0, "0")
    e_over.pack(side="left", padx=6)
    ctk.CTkLabel(drow, text=f"{s.get('festive_name') or 'Festive'} %", font=FONTS["body"]).pack(side="left", padx=(10, 0))
    e_fest = ctk.CTkEntry(drow, width=70, height=30)
    e_fest.insert(0, str(s.get("festive_percent") or 0))
    e_fest.pack(side="left", padx=6)
    ctk.CTkLabel(drow, text="Coupon", font=FONTS["body"]).pack(side="left", padx=(10, 0))
    e_coupon = ctk.CTkEntry(drow, width=130, height=30, placeholder_text="e.g. WELCOME10")
    e_coupon.pack(side="left", padx=6)
    coupon_lbl = ctk.CTkLabel(drow, text="", font=FONTS["small"])
    coupon_lbl.pack(side="left", padx=6)

    for e in (e_over, e_fest, e_coupon):
        e.bind("<KeyRelease>", lambda _e: refresh_cart())

    trow = ctk.CTkFrame(dc, fg_color="transparent")
    trow.pack(fill="x", padx=16, pady=(0, 4))
    total_lbls = {}
    for key in ["subtotal", "item_disc", "overall", "festive", "coupon", "taxable", "gst"]:
        f = ctk.CTkFrame(trow, fg_color="transparent")
        f.pack(side="left", padx=8)
        ctk.CTkLabel(f, text={"subtotal": "Subtotal", "item_disc": "Item Disc",
                              "overall": "Overall", "festive": "Festive",
                              "coupon": "Coupon", "taxable": "Taxable",
                              "gst": "GST"}[key],
                     font=FONTS["small"], text_color=COLORS["text_muted"]).pack()
        v = ctk.CTkLabel(f, text="₹ 0.00", font=FONTS["body"], text_color=COLORS["text_dark"])
        v.pack()
        total_lbls[key] = v
    grand_lbl = ctk.CTkLabel(trow, text="Grand: ₹ 0.00", font=("Segoe UI", 18, "bold"),
                             text_color=COLORS["accent"])
    grand_lbl.pack(side="right", padx=10)

    msg = ctk.CTkLabel(parent, text="", font=FONTS["body"])
    msg.pack(anchor="w", padx=10)

    brow = ctk.CTkFrame(parent, fg_color="transparent")
    brow.pack(fill="x", padx=4, pady=4)
    ctk.CTkButton(brow, text="✓  Generate Bill (OK)", height=42, width=230, fg_color=COLORS["success"],
                  hover_color="#1E8449", command=lambda: on_generate()).pack(side="right", padx=4)
    ctk.CTkLabel(brow, text="Generate saves bill + PDF (folder from Settings) + updates stock.",
                 font=FONTS["small"], text_color=COLORS["text_muted"]).pack(side="left", padx=8)

    def current_totals():
        coupon = None
        code = e_coupon.get().strip()
        if code:
            coupon = db.validate_coupon(code)
            if coupon:
                coupon_lbl.configure(text=f"✓ {coupon['code']} {coupon['discount_percent']:g}%",
                                     text_color=COLORS["success"])
            else:
                coupon_lbl.configure(text="✗ invalid/expired", text_color=COLORS["danger"])
        else:
            coupon_lbl.configure(text="")
        return db.compute_cart_totals(cart, _f(e_over.get()), _f(e_fest.get()), coupon)

    def refresh_cart():
        for r in tree.get_children():
            tree.delete(r)
        for ln in cart:
            gross = ln["qty"] * ln["price"]
            d = gross * ln["discount_percent"] / 100.0
            net = gross - d
            lt = net + net * ln["gst_percent"] / 100.0
            tree.insert("", "end", values=(
                ln["item_code"], ln.get("brand", ""), ln["item_name"], ln.get("serial_no", ""),
                f"{ln['qty']:g}",
                f"₹{ln['price']:.2f}", f"{ln['discount_percent']:g}",
                f"{ln['gst_percent']:g}", f"₹{lt:.2f}"))
        t = current_totals()
        total_lbls["subtotal"].configure(text=f"₹ {t['subtotal']:.2f}")
        total_lbls["item_disc"].configure(text=f"− ₹ {t['item_discount_total']:.2f}")
        total_lbls["overall"].configure(text=f"− ₹ {t['overall_discount_amt']:.2f}")
        total_lbls["festive"].configure(text=f"− ₹ {t['festive_amt']:.2f}")
        total_lbls["coupon"].configure(text=f"− ₹ {t['coupon_discount_amt']:.2f}")
        total_lbls["taxable"].configure(text=f"₹ {t['taxable_value']:.2f}")
        total_lbls["gst"].configure(text=f"₹ {t['gst_total']:.2f}")
        grand_lbl.configure(text=f"Grand: ₹ {t['grand_total']:.2f}")

    def on_generate():
        code = e_coupon.get().strip()
        try:
            inv, _bid, t = db.create_bill(
                {"name": e_cname.get(), "address": e_caddr.get(), "mobile": e_cmob.get()},
                cart, _f(e_over.get()), _f(e_fest.get()), code)
            try:
                import pdf_bill
                pdf_path = pdf_bill.generate_bill_pdf(_bid)
                pdf_note = f"\nPDF: {pdf_path}"
            except Exception as ex:
                pdf_path = ""
                pdf_note = f"\n(Bill saved, but PDF failed: {ex})"
            cart.clear()
            e_cname.delete(0, "end"); e_caddr.delete(0, "end"); e_cmob.delete(0, "end")
            e_coupon.delete(0, "end"); e_over.delete(0, "end"); e_over.insert(0, "0")
            refresh_cart()
            msg.configure(text=f"✓ Bill {inv} saved — total ₹ {t['grand_total']:.2f}. Stock updated."
                              + (" PDF ready." if pdf_path else " (PDF failed — see Reports to retry.)"),
                          text_color=COLORS["success"])
            messagebox.showinfo("Bill Saved",
                                f"Invoice {inv}\nGrand Total ₹ {t['grand_total']:.2f}{pdf_note}\n\n"
                                "See Reports → Bills history to view / edit / delete.")
        except ValueError as ex:
            msg.configure(text=f"⚠ {ex}", text_color=COLORS["danger"])

    refresh_cart()
