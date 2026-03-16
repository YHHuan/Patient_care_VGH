"""Tkinter GUI — login, search, generate AI summaries."""

from __future__ import annotations

import asyncio
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext

from config.settings import settings

logger = logging.getLogger(__name__)


class App:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("VGHTPE 查房摘要產生器 (AI)")
        self.root.geometry("900x700")
        self.root.configure(bg="#f0f0f0")

        self._session = None  # VGHSession (created on login)
        self._orch = None     # Orchestrator
        self._patients: list[list[str]] = []

        self._build_ui()

    # ── UI construction ─────────────────────────────────────────

    def _build_ui(self) -> None:
        # Title
        title_f = tk.Frame(self.root, bg="#2c3e50", height=60)
        title_f.pack(fill="x", padx=10, pady=(10, 0))
        title_f.pack_propagate(False)
        tk.Label(
            title_f, text="VGHTPE 查房摘要產生器 (AI)",
            font=("Arial", 16, "bold"), fg="white", bg="#2c3e50",
        ).pack(expand=True)

        # Login frame
        login_f = tk.LabelFrame(self.root, text="登入資訊", font=("Arial", 11, "bold"), bg="#f0f0f0")
        login_f.pack(fill="x", padx=10, pady=5)

        tk.Label(login_f, text="帳號:", bg="#f0f0f0").grid(row=0, column=0, padx=8, pady=4, sticky="w")
        self.entry_user = tk.Entry(login_f, width=20)
        self.entry_user.grid(row=0, column=1, padx=8, pady=4)

        tk.Label(login_f, text="密碼:", bg="#f0f0f0").grid(row=1, column=0, padx=8, pady=4, sticky="w")
        self.entry_pass = tk.Entry(login_f, show="*", width=20)
        self.entry_pass.grid(row=1, column=1, padx=8, pady=4)

        tk.Label(login_f, text="OpenRouter Key:", bg="#f0f0f0").grid(row=0, column=2, padx=8, pady=4, sticky="w")
        self.entry_api = tk.Entry(login_f, width=30, show="*")
        self.entry_api.grid(row=0, column=3, padx=8, pady=4)
        if settings.openrouter_api_key:
            self.entry_api.insert(0, settings.openrouter_api_key)

        self.btn_login = tk.Button(
            login_f, text="登入", bg="#3498db", fg="white", width=10,
            command=self._on_login,
        )
        self.btn_login.grid(row=1, column=2, columnspan=2, padx=8, pady=4)

        self.lbl_status = tk.Label(login_f, text="未登入", fg="red", bg="#f0f0f0")
        self.lbl_status.grid(row=2, column=0, columnspan=4, pady=4)

        # Search frame
        search_f = tk.LabelFrame(self.root, text="搜尋", font=("Arial", 11, "bold"), bg="#f0f0f0")
        search_f.pack(fill="x", padx=10, pady=5)

        self.search_var = tk.StringVar(value="doc")
        for i, (txt, val) in enumerate([("依燈號", "doc"), ("依病房", "ward"), ("依病歷號", "pat")]):
            tk.Radiobutton(search_f, text=txt, variable=self.search_var, value=val, bg="#f0f0f0").grid(
                row=0, column=i, padx=10, pady=4
            )

        tk.Label(search_f, text="輸入:", bg="#f0f0f0").grid(row=1, column=0, padx=8, sticky="w")
        self.entry_search = tk.Entry(search_f, width=30)
        self.entry_search.grid(row=1, column=1, padx=8, pady=4)

        self.btn_search = tk.Button(
            search_f, text="搜尋病人", bg="#27ae60", fg="white", width=12,
            command=self._on_search, state="disabled",
        )
        self.btn_search.grid(row=1, column=2, padx=8, pady=4)

        # Action buttons
        btn_f = tk.Frame(self.root, bg="#f0f0f0")
        btn_f.pack(fill="x", padx=10, pady=5)

        self.btn_generate = tk.Button(
            btn_f, text="產生 AI 摘要", bg="#e74c3c", fg="white", width=15,
            command=self._on_generate, state="disabled",
        )
        self.btn_generate.pack(side="left", padx=5)

        self.btn_word = tk.Button(
            btn_f, text="匯出 Word", bg="#8e44ad", fg="white", width=12,
            command=self._on_export_word, state="disabled",
        )
        self.btn_word.pack(side="left", padx=5)

        tk.Button(
            btn_f, text="清除", bg="#95a5a6", fg="white", width=8,
            command=self._on_clear,
        ).pack(side="left", padx=5)

        # Progress
        prog_f = tk.LabelFrame(self.root, text="進度", bg="#f0f0f0")
        prog_f.pack(fill="x", padx=10, pady=5)
        self.progress_var = tk.StringVar(value="等待中...")
        tk.Label(prog_f, textvariable=self.progress_var, bg="#f0f0f0").pack(pady=6)
        self.progress_bar = ttk.Progressbar(prog_f, mode="indeterminate")
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 6))

        # Log output
        log_f = tk.LabelFrame(self.root, text="輸出", bg="#f0f0f0")
        log_f.pack(fill="both", expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_f, font=("Consolas", 9), height=12, bg="white")
        self.log_text.pack(fill="both", expand=True, padx=8, pady=8)

    # ── helpers ──────────────────────────────────────────────────

    def _log(self, msg: str) -> None:
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)

    def _run_async(self, coro, *, on_done=None, on_error=None):
        """Run an async coroutine in a background thread."""

        def _thread():
            loop = asyncio.new_event_loop()
            try:
                result = loop.run_until_complete(coro)
                if on_done:
                    self.root.after(0, lambda: on_done(result))
            except Exception as e:
                logger.exception("Async task failed")
                if on_error:
                    self.root.after(0, lambda: on_error(e))
            finally:
                loop.close()

        threading.Thread(target=_thread, daemon=True).start()

    # ── callbacks ────────────────────────────────────────────────

    def _on_login(self) -> None:
        from scraper.session import VGHSession

        user = self.entry_user.get().strip()
        pw = self.entry_pass.get().strip()
        api_key = self.entry_api.get().strip()

        if not user or not pw:
            messagebox.showerror("錯誤", "請輸入帳號和密碼")
            return

        if api_key:
            settings.openrouter_api_key = api_key

        self.btn_login.config(state="disabled", text="登入中...")
        self.lbl_status.config(text="登入中...", fg="orange")

        async def _do():
            s = VGHSession()
            await s.start()
            await s.login(user, pw)
            return s

        def _ok(session):
            self._session = session
            from scraper.orchestrator import Orchestrator
            self._orch = Orchestrator(session)
            self.lbl_status.config(text="✓ 登入成功", fg="green")
            self.btn_login.config(state="normal", text="登入")
            self.btn_search.config(state="normal")
            self._log("登入成功！")

        def _err(e):
            self.lbl_status.config(text="✗ 登入失敗", fg="red")
            self.btn_login.config(state="normal", text="登入")
            messagebox.showerror("登入失敗", str(e))

        self._run_async(_do(), on_done=_ok, on_error=_err)

    def _on_search(self) -> None:
        from scraper.fetchers import fetch_searched_patients

        val = self.entry_search.get().strip()
        if not val:
            messagebox.showerror("錯誤", "請輸入搜尋條件")
            return

        mode = self.search_var.get()
        self.btn_search.config(state="disabled", text="搜尋中...")
        self.progress_bar.start()

        async def _do():
            if mode == "doc":
                return await fetch_searched_patients(self._session, doc_id=val)
            elif mode == "ward":
                return await fetch_searched_patients(self._session, ward=val)
            else:
                return await fetch_searched_patients(self._session, hist_no=val)

        def _ok(patients):
            self._patients = patients
            self.btn_search.config(state="normal", text="搜尋病人")
            self.progress_bar.stop()
            self.progress_var.set(f"找到 {len(patients)} 位病人")
            self._log(f"找到 {len(patients)} 位病人")
            for i, p in enumerate(patients[:15], 1):
                self._log(f"  {i}. {' | '.join(p[:4])}")
            if patients:
                self.btn_generate.config(state="normal")

        def _err(e):
            self.btn_search.config(state="normal", text="搜尋病人")
            self.progress_bar.stop()
            messagebox.showerror("搜尋失敗", str(e))

        self._run_async(_do(), on_done=_ok, on_error=_err)

    def _on_generate(self) -> None:
        if not self._patients or not self._orch:
            return

        self.btn_generate.config(state="disabled", text="產生中...")
        self.progress_bar.start()

        mode = self.search_var.get()

        pat_list = []
        for row in self._patients:
            if mode == "ward":
                hist_no = row[2] if len(row) > 2 else row[0]
            else:
                hist_no = row[1] if len(row) > 1 else row[0]
            pat_list.append({"hist_no": hist_no})

        async def _do():
            return await self._orch.process_patient_list(
                pat_list,
                on_progress=lambda msg: self.root.after(0, lambda m=msg: self._update_progress(m)),
            )

        def _ok(results):
            self._results = results
            self.btn_generate.config(state="normal", text="產生 AI 摘要")
            self.progress_bar.stop()
            ok_count = sum(1 for _, md, _ in results if md)
            self.progress_var.set(f"完成！成功 {ok_count}/{len(results)}")
            for hist_no, md, err in results:
                if md:
                    self._log(f"✓ {hist_no}")
                else:
                    self._log(f"✗ {hist_no}: {err}")
            if ok_count > 0:
                self.btn_word.config(state="normal")

        def _err(e):
            self.btn_generate.config(state="normal", text="產生 AI 摘要")
            self.progress_bar.stop()
            messagebox.showerror("產生失敗", str(e))

        self._run_async(_do(), on_done=_ok, on_error=_err)

    def _on_export_word(self) -> None:
        from output.docx_export import export_docx

        if not hasattr(self, "_results"):
            return

        summaries = [(h, md) for h, md, _ in self._results if md]
        doc_code = self.entry_search.get().strip() if self.search_var.get() == "doc" else ""
        path = export_docx(summaries, doctor_code=doc_code)
        self._log(f"Word 文件已儲存: {path}")
        messagebox.showinfo("完成", f"Word 文件已儲存:\n{path}")

    def _on_clear(self) -> None:
        self.log_text.delete("1.0", tk.END)
        self._patients = []
        self._results = []
        self.btn_generate.config(state="disabled")
        self.btn_word.config(state="disabled")
        self.progress_var.set("等待中...")

    def _update_progress(self, msg: str) -> None:
        self.progress_var.set(msg)
        self._log(msg)


def main() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
