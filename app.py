"""Interface local para converter PDFs em Markdown com Docling e OCR."""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import tkinter as tk
from tkinter import filedialog, messagebox, ttk


OUTPUT_DIR_NAME = "saida_docling"
OCR_LANGUAGES = ["iso:pt"]


@dataclass
class WorkerEvent:
    """Mensagem enviada pela thread de processamento para a interface."""

    kind: str
    data: Any = None


def create_converter() -> Any:
    """Cria o conversor uma única vez, com OCR e reconhecimento de tabelas ativos."""
    # O import é adiado para que a interface ainda abra e explique a ausência do
    # Docling caso o ambiente virtual não tenha sido preparado.
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = True
    pipeline_options.do_table_structure = True

    # RapidOCR roda localmente sobre ONNX Runtime e não exige o executável do
    # Tesseract. A versão atual do motor trabalha com um idioma por vez; por
    # isso o aplicativo prioriza português para o perfil de documentos alvo.
    pipeline_options.ocr_options = RapidOcrOptions(lang=OCR_LANGUAGES)

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )


def list_pdfs(folder: Path) -> list[Path]:
    """Lista somente PDFs diretamente na pasta escolhida, em ordem alfabética."""
    return sorted(
        (path for path in folder.iterdir() if path.is_file() and path.suffix.lower() == ".pdf"),
        key=lambda path: path.name.casefold(),
    )


def error_message(error: BaseException) -> str:
    """Mantém mensagens de erro de relatório em uma única linha legível."""
    text = str(error).strip() or error.__class__.__name__
    return " ".join(text.splitlines())


def write_error_report(output_dir: Path, errors: list[tuple[Path, str]]) -> None:
    """Cria erros.txt somente quando houver arquivos que falharam."""
    if not errors:
        return

    lines = [f"{pdf.name} | {message}" for pdf, message in errors]
    (output_dir / "erros.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def process_pdfs_in_background(
    pdfs: list[Path], output_dir: Path, events: queue.Queue[WorkerEvent]
) -> None:
    """Executa o lote fora da thread do Tkinter e informa progresso por fila."""
    errors: list[tuple[Path, str]] = []
    successes = 0
    total = len(pdfs)

    try:
        output_dir.mkdir(exist_ok=True)
        events.put(WorkerEvent("log", "Inicializando Docling e OCR..."))
        converter = create_converter()
        events.put(WorkerEvent("log", "Docling inicializado."))
    except Exception as error:
        message = error_message(error)
        events.put(WorkerEvent("log", f"ERRO ao inicializar Docling: {message}"))
        errors = [(pdf, f"Falha ao inicializar Docling: {message}") for pdf in pdfs]
        try:
            write_error_report(output_dir, errors)
        except Exception as report_error:
            events.put(
                WorkerEvent(
                    "log", f"ERRO ao criar erros.txt: {error_message(report_error)}"
                )
            )
        events.put(WorkerEvent("done", (total, successes, errors, output_dir)))
        return

    for index, pdf_path in enumerate(pdfs, start=1):
        events.put(WorkerEvent("current", (index, total, pdf_path.name)))
        events.put(WorkerEvent("log", f"[{index}/{total}] Processando {pdf_path.name}"))

        try:
            result = converter.convert(pdf_path)
            markdown = result.document.export_to_markdown()
            output_path = output_dir / f"{pdf_path.stem}.md"
            output_path.write_text(markdown, encoding="utf-8")
            successes += 1
            events.put(WorkerEvent("log", f"OK: {output_path.name}"))
        except Exception as error:
            message = error_message(error)
            errors.append((pdf_path, message))
            events.put(WorkerEvent("log", f"ERRO: {pdf_path.name} | {message}"))
            # A exceção de um documento não interrompe os demais.
        finally:
            events.put(WorkerEvent("progress", (index, total)))

    try:
        write_error_report(output_dir, errors)
    except Exception as error:
        events.put(WorkerEvent("log", f"ERRO ao criar erros.txt: {error_message(error)}"))

    events.put(WorkerEvent("done", (total, successes, errors, output_dir)))


class PdfExtractorApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Extrator de PDFs com Docling + OCR")
        self.root.minsize(760, 520)

        self.selected_folder: Path | None = None
        self.pdfs: list[Path] = []
        self.output_dir: Path | None = None
        self.events: queue.Queue[WorkerEvent] = queue.Queue()
        self.is_processing = False

        self.folder_var = tk.StringVar(value="Nenhuma pasta selecionada.")
        self.count_var = tk.StringVar(value="0 arquivos PDF encontrados.")
        self.current_var = tk.StringVar(value="Selecione uma pasta para começar.")
        self.summary_var = tk.StringVar(value="Aguardando seleção da pasta.")
        self.progress_var = tk.IntVar(value=0)

        self._build_interface()
        self.root.after(100, self._consume_events)

    def _build_interface(self) -> None:
        container = ttk.Frame(self.root, padding=14)
        container.grid(sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(5, weight=1)

        ttk.Label(container, text="Pasta com PDFs:").grid(row=0, column=0, sticky="w")

        folder_row = ttk.Frame(container)
        folder_row.grid(row=1, column=0, sticky="ew", pady=(3, 10))
        folder_row.columnconfigure(0, weight=1)
        ttk.Entry(folder_row, textvariable=self.folder_var, state="readonly").grid(
            row=0, column=0, sticky="ew", padx=(0, 8)
        )
        self.select_button = ttk.Button(
            folder_row, text="Selecionar pasta", command=self.select_folder
        )
        self.select_button.grid(row=0, column=1)

        ttk.Label(container, textvariable=self.count_var).grid(row=2, column=0, sticky="w")
        ttk.Label(container, textvariable=self.current_var, wraplength=720).grid(
            row=3, column=0, sticky="w", pady=(8, 3)
        )

        self.progress = ttk.Progressbar(
            container, variable=self.progress_var, maximum=1, mode="determinate"
        )
        self.progress.grid(row=4, column=0, sticky="ew", pady=(0, 10))

        log_frame = ttk.LabelFrame(container, text="Log", padding=6)
        log_frame.grid(row=5, column=0, sticky="nsew")
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(log_frame, height=16, wrap="word", state="disabled")
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

        buttons_row = ttk.Frame(container)
        buttons_row.grid(row=6, column=0, sticky="ew", pady=(10, 4))
        self.process_button = ttk.Button(
            buttons_row, text="Processar PDFs", command=self.start_processing
        )
        self.process_button.grid(row=0, column=0, padx=(0, 8))
        self.open_output_button = ttk.Button(
            buttons_row, text="Abrir pasta de saída", command=self.open_output_folder
        )
        self.open_output_button.grid(row=0, column=1)

        ttk.Label(container, textvariable=self.summary_var, wraplength=720).grid(
            row=7, column=0, sticky="w", pady=(4, 0)
        )

    def append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def select_folder(self) -> None:
        selected = filedialog.askdirectory(title="Selecione a pasta com os PDFs")
        if not selected:
            return

        folder = Path(selected)
        try:
            pdfs = list_pdfs(folder)
        except OSError as error:
            messagebox.showerror("Não foi possível ler a pasta", error_message(error))
            return

        self.selected_folder = folder
        self.pdfs = pdfs
        self.output_dir = folder / OUTPUT_DIR_NAME
        self.folder_var.set(str(folder))
        self.count_var.set(f"{len(pdfs)} arquivo(s) PDF encontrado(s).")
        self.current_var.set("Pronto para processar.")
        self.summary_var.set("Aguardando início do processamento.")
        self.progress.configure(maximum=max(len(pdfs), 1))
        self.progress_var.set(0)
        self.append_log(f"Pasta selecionada:\n{folder}\n")
        self.append_log(f"{len(pdfs)} PDF(s) encontrado(s).")

    def start_processing(self) -> None:
        if self.is_processing:
            return
        if self.selected_folder is None or self.output_dir is None:
            messagebox.showwarning("Selecione uma pasta", "Selecione uma pasta contendo PDFs.")
            return
        if not self.pdfs:
            messagebox.showinfo("Nenhum PDF", "Não foram encontrados PDFs diretamente nesta pasta.")
            return

        self.is_processing = True
        self.select_button.configure(state="disabled")
        self.process_button.configure(state="disabled")
        self.progress.configure(maximum=len(self.pdfs))
        self.progress_var.set(0)
        self.summary_var.set("Processamento em andamento...")

        worker = threading.Thread(
            target=process_pdfs_in_background,
            args=(self.pdfs, self.output_dir, self.events),
            daemon=True,
        )
        worker.start()

    def _consume_events(self) -> None:
        try:
            while True:
                event = self.events.get_nowait()
                if event.kind == "log":
                    self.append_log(str(event.data))
                elif event.kind == "current":
                    index, total, name = event.data
                    self.current_var.set(f"Processando {index} de {total}: {name}")
                elif event.kind == "progress":
                    index, total = event.data
                    self.progress.configure(maximum=total)
                    self.progress_var.set(index)
                elif event.kind == "done":
                    self._finish_processing(*event.data)
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self._consume_events)

    def _finish_processing(
        self, total: int, successes: int, errors: list[tuple[Path, str]], output_dir: Path
    ) -> None:
        self.is_processing = False
        self.select_button.configure(state="normal")
        self.process_button.configure(state="normal")
        self.output_dir = output_dir
        self.current_var.set("Processamento concluído.")
        self.summary_var.set(
            f"Concluído. Total: {total} | Sucesso: {successes} | Erros: {len(errors)} | "
            f"Saída: {output_dir}"
        )
        self.append_log("\nProcessamento concluído.")
        self.append_log(f"Sucesso: {successes}")
        self.append_log(f"Erros: {len(errors)}")
        self.append_log(f"Pasta de saída: {output_dir}")
        if errors:
            self.append_log("Detalhes das falhas foram salvos em erros.txt.")

    def open_output_folder(self) -> None:
        if self.output_dir is None:
            messagebox.showinfo("Pasta de saída", "Selecione uma pasta primeiro.")
            return
        if not self.output_dir.exists():
            messagebox.showinfo(
                "Pasta de saída", "A pasta de saída será criada ao processar os PDFs."
            )
            return

        try:
            if sys.platform.startswith("win"):
                os.startfile(str(self.output_dir))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.output_dir)], check=False)
            else:
                subprocess.run(["xdg-open", str(self.output_dir)], check=False)
        except OSError as error:
            messagebox.showerror("Não foi possível abrir a pasta", error_message(error))


def main() -> None:
    root = tk.Tk()
    PdfExtractorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
