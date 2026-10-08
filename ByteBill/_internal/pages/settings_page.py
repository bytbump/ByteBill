"""STEP 2 — Business Settings page: details + branding + invoice format + PDF folder."""
import os
import re
import shutil

import sys
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$")
BUSINESS_TYPES = ["Retail", "Wholesale", "Services", "Restaurant", "Pharmacy", "Grocery", "Electronics", "Other"]
CURRENCIES = ["INR", "USD", "EUR"]


def _copy_to_assets(src_path):
    os.makedirs(ASSETS_DIR, exist_ok=True)
    fname = os.path.basename(src_path)
    dst = os.path.join(ASSETS_DIR, fname)
    if os.path.abspath(src_path) != os.path.abspath(dst):
        shutil.copy2(src_path, dst)
    return dst


def build(parent, app):
    import customtkinter as ctk
    from tkinter import filedialog
    from theme import COLORS, FONTS
    import database as db

    for w in parent.winfo_children():
        w.destroy()

    s = db.get_settings()
    state = {"logo": s.get("logo_path") or "", "stamp": s.get("stamp_path") or "",
             "signature": s.get("signature_path") or ""}

    scroll = ctk.CTkFrame(parent, fg_color="transparent")
    scroll.pack(fill="both", expand=True)

    def card(title):
        c = ctk.CTkFrame(scroll, fg_color=COLORS["card"], corner_radius=12)
        c.pack(fill="x", padx=4, pady=6)
        ctk.CTkLabel(c, text=title, font=FONTS["heading"],
                     text_color=COLORS["text_dark"]).pack(anchor="w", padx=20, pady=(14, 8))
        return c

    def field(frame, label, initial="", width=340):
        row = ctk.CTkFrame(frame, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=4)
        ctk.CTkLabel(row, text=label, font=FONTS["body"], text_color=COLORS["text_dark"],
                     width=160, anchor="w").pack(side="left")
        e = ctk.CTkEntry(row, width=width, height=34)
        e.insert(0, str(initial))
        e.pack(side="left", padx=8)
        return e

    # ---- 1. Business details ----
    c1 = card("1  •  Business Details")
    e_name = field(c1, "Business Name *", s.get("business_name") or "")
    # address (multiline)
    arow = ctk.CTkFrame(c1, fg_color="transparent")
    arow.pack(fill="x", padx=20, pady=4)
    ctk.CTkLabel(arow, text="Address", font=FONTS["body"],
                 text_color=COLORS["text_dark"], width=160, anchor="w").pack(side="left", anchor="n")
    t_addr = ctk.CTkTextbox(arow, width=340, height=70)
    t_addr.insert("1.0", s.get("address") or "")
    t_addr.pack(side="left", padx=8)
    e_gstin = field(c1, "GSTIN (optional)", s.get("gstin") or "")
    # business type dropdown
    trow = ctk.CTkFrame(c1, fg_color="transparent")
    trow.pack(fill="x", padx=20, pady=4)
    ctk.CTkLabel(trow, text="Business Type", font=FONTS["body"],
                 text_color=COLORS["text_dark"], width=160, anchor="w").pack(side="left")
    om_type = ctk.CTkOptionMenu(trow, values=BUSINESS_TYPES, width=200)
    try:
        om_type.set(s.get("business_type") or "Retail")
    except Exception:
        pass
    om_type.pack(side="left", padx=8)
    e_mobile = field(c1, "Mobile Number *", s.get("mobile") or "")
    e_email = field(c1, "Email", s.get("email") or "")

    # ---- 2. Logo / Stamp / Signature ----
    c2 = card("2  •  Logo, Stamp & Signature (uploads)")
    upload_rows = {}

    for key, label in [("logo", "Business Logo"), ("stamp", "Stamp"), ("signature", "Signature")]:
        r = ctk.CTkFrame(c2, fg_color="transparent")
        r.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(r, text=label, font=FONTS["body"], text_color=COLORS["text_dark"],
                     width=160, anchor="w").pack(side="left")
        path_lbl = ctk.CTkLabel(r, text=os.path.basename(state[key]) or "No file chosen",
                                font=FONTS["small"], text_color=COLORS["text_muted"], width=260, anchor="w")
        path_lbl.pack(side="left", padx=8)

        def browse(k=key, lbl=path_lbl):
            p = filedialog.askopenfilename(
                title=f"Choose {k}",
                filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp"), ("All files", "*.*")])
            if p:
                try:
                    state[k] = _copy_to_assets(p)
                    lbl.configure(text=os.path.basename(state[k]))
                    msg.configure(text=f"{k} attached ✓", text_color=COLORS["success"])
                except Exception as ex:
                    msg.configure(text=f"Copy failed: {ex}", text_color=COLORS["danger"])

        def clear(k=key, lbl=path_lbl):
            state[k] = ""
            lbl.configure(text="No file chosen")

        ctk.CTkButton(r, text="Browse", width=90, height=30, fg_color=COLORS["accent"],
                      hover_color=COLORS["accent_hover"], command=browse).pack(side="left", padx=4)
        ctk.CTkButton(r, text="Clear", width=70, height=30, fg_color="#95A5B8",
                      hover_color="#7F8C9B", command=clear).pack(side="left")

    ctk.CTkLabel(c2, text="PNG/JPG recommended. Logo prints on the bill header; stamp + signature print at bill bottom.",
                 font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=20, pady=(0, 12))

    # ---- 3. Invoice numbering + PDF folder ----
    c3 = card("3  •  Invoice Number Format & PDF Folder")
    r3 = ctk.CTkFrame(c3, fg_color="transparent")
    r3.pack(fill="x", padx=20, pady=4)
    ctk.CTkLabel(r3, text="Prefix", font=FONTS["body"], width=160, anchor="w").pack(side="left")
    e_prefix = ctk.CTkEntry(r3, width=120, height=34)
    e_prefix.insert(0, s.get("invoice_prefix") or "INV")
    e_prefix.pack(side="left", padx=8)
    ctk.CTkLabel(r3, text="Next No", font=FONTS["body"]).pack(side="left", padx=(16, 0))
    e_next = ctk.CTkEntry(r3, width=100, height=34)
    e_next.insert(0, str(s.get("invoice_next_no") or 1))
    e_next.pack(side="left", padx=8)
    ctk.CTkLabel(r3, text="Suffix", font=FONTS["body"]).pack(side="left", padx=(16, 0))
    e_suffix = ctk.CTkEntry(r3, width=100, height=34)
    e_suffix.insert(0, s.get("invoice_suffix") or "")
    e_suffix.pack(side="left", padx=8)
    preview_lbl = ctk.CTkLabel(c3, text="", font=FONTS["mono"], text_color=COLORS["accent"])
    preview_lbl.pack(anchor="w", padx=20, pady=2)

    def refresh_preview(*_):
        preview_lbl.configure(
            text=f"Preview → next bill no: {e_prefix.get().strip() or 'INV'}-{e_next.get().strip() or '1'}{e_suffix.get().strip()}")

    for e in (e_prefix, e_next, e_suffix):
        e.bind("<KeyRelease>", refresh_preview)
    refresh_preview()

    pf = ctk.CTkFrame(c3, fg_color="transparent")
    pf.pack(fill="x", padx=20, pady=4)
    ctk.CTkLabel(pf, text="Bill PDF Folder", font=FONTS["body"], width=160, anchor="w").pack(side="left")
    e_pdf = ctk.CTkEntry(pf, width=300, height=34)
    e_pdf.insert(0, s.get("pdf_folder") or "bills")
    e_pdf.pack(side="left", padx=8)

    def browse_pdf():
        d = filedialog.askdirectory(title="Choose folder for saved bill PDFs")
        if d:
            e_pdf.delete(0, "end")
            e_pdf.insert(0, d)

    ctk.CTkButton(pf, text="Browse", width=90, height=30, fg_color=COLORS["accent"],
                  hover_color=COLORS["accent_hover"], command=browse_pdf).pack(side="left", padx=4)

    prow = ctk.CTkFrame(c3, fg_color="transparent")
    prow.pack(fill="x", padx=20, pady=4)
    ctk.CTkLabel(prow, text="Default Bill Paper", font=FONTS["body"], width=160, anchor="w").pack(side="left")
    om_paper = ctk.CTkOptionMenu(prow, values=["A4", "Thermal 80mm", "Thermal 58mm"], width=160)
    try:
        _pv = (s.get("paper_size") or "A4").upper()
        om_paper.set("Thermal 80mm" if _pv == "T80" else ("Thermal 58mm" if _pv == "T58" else "A4"))
    except Exception:
        pass
    om_paper.pack(side="left", padx=8)
    ctk.CTkLabel(c3, text="Thermal receipts print from any 58/80mm printer. Reports can reprint any bill in any size.",
                 font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=20, pady=(0, 12))

    # ---- 4. Festive default + currency ----
    c4 = card("4  •  Festive Offer Default & Currency")
    e_fest_name = field(c4, "Festive Name", s.get("festive_name") or "Festive Sale")
    e_fest_pct = field(c4, "Festive % (default)", s.get("festive_percent") or 0, width=120)
    crow = ctk.CTkFrame(c4, fg_color="transparent")
    crow.pack(fill="x", padx=20, pady=4)
    ctk.CTkLabel(crow, text="Currency", font=FONTS["body"], width=160, anchor="w").pack(side="left")
    om_cur = ctk.CTkOptionMenu(crow, values=CURRENCIES, width=120)
    om_cur.set(s.get("currency") or "INR")
    om_cur.pack(side="left", padx=8)
    ctk.CTkLabel(c4, text="Coupons are created on the Coupons page. This % auto-suggests in Billing.",
                 font=FONTS["small"], text_color=COLORS["text_muted"]).pack(anchor="w", padx=20, pady=(0, 12))

    # ---- Save bar ----
    bar = ctk.CTkFrame(scroll, fg_color="transparent")
    bar.pack(fill="x", padx=4, pady=8)
    msg = ctk.CTkLabel(bar, text="", font=FONTS["body"])
    msg.pack(side="left", padx=10)
    ctk.CTkButton(bar, text="Save Settings", height=40, width=180, fg_color=COLORS["success"],
                  hover_color="#1E8449", command=lambda: on_save()).pack(side="right", padx=6)
    ctk.CTkButton(bar, text="Back to Welcome", height=40, width=150, fg_color="#95A5B8",
                  hover_color="#7F8C9B",
                  command=lambda: app.show_page("welcome")).pack(side="right")

    def on_save():
        name = e_name.get().strip()
        mobile = e_mobile.get().strip()
        gstin = e_gstin.get().strip().upper()
        if not name:
            msg.configure(text="⚠ Business Name is required.", text_color=COLORS["danger"])
            return
        if not mobile:
            msg.configure(text="⚠ Mobile Number is required.", text_color=COLORS["danger"])
            return
        if gstin and not GSTIN_RE.match(gstin):
            msg.configure(text="⚠ GSTIN looks invalid (15 chars). Saved anyway — please verify.",
                          text_color=COLORS["warning"])
        try:
            nxt = int(e_next.get().strip() or "1")
            if nxt < 1:
                raise ValueError
        except ValueError:
            msg.configure(text="⚠ Next No must be a positive number.", text_color=COLORS["danger"])
            return
        try:
            fpct = float(e_fest_pct.get().strip() or "0")
        except ValueError:
            msg.configure(text="⚠ Festive % must be a number.", text_color=COLORS["danger"])
            return
        pdf_folder = e_pdf.get().strip() or "bills"
        try:
            target = pdf_folder if os.path.isabs(pdf_folder) else os.path.join(BASE_DIR, pdf_folder)
            os.makedirs(target, exist_ok=True)
        except Exception as ex:
            msg.configure(text=f"⚠ Cannot create PDF folder: {ex}", text_color=COLORS["danger"])
            return
        db.save_settings({
            "business_name": name,
            "address": t_addr.get("1.0", "end").strip(),
            "gstin": gstin,
            "business_type": om_type.get(),
            "mobile": mobile,
            "email": e_email.get().strip(),
            "logo_path": state["logo"],
            "stamp_path": state["stamp"],
            "signature_path": state["signature"],
            "invoice_prefix": e_prefix.get().strip() or "INV",
            "invoice_next_no": nxt,
            "invoice_suffix": e_suffix.get().strip(),
            "pdf_folder": pdf_folder,
            "paper_size": {"THERMAL 80MM": "T80", "THERMAL 58MM": "T58"}.get(
                om_paper.get().upper(), "A4"),
            "festive_name": e_fest_name.get().strip() or "Festive Sale",
            "festive_percent": fpct,
            "currency": om_cur.get(),
        })
        if not msg.cget("text").startswith("⚠"):
            msg.configure(text="✓ Settings saved. Welcome screen + next bill number updated.",
                          text_color=COLORS["success"])
        try:
            app.refresh_topbar()
        except Exception:
            pass
