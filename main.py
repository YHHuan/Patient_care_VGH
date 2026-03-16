"""CLI entry point — typer-based."""

from __future__ import annotations

import asyncio
import logging
import sys

import typer
from rich.console import Console
from rich.logging import RichHandler

from config.settings import settings

app = typer.Typer(help="VGHTPE Patient Scraper + AI Clinical Summary Generator")
console = Console()


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


async def _run_full(doctor_code: str, from_cache: bool = False) -> None:
    from scraper.session import VGHSession
    from scraper.fetchers import fetch_searched_patients
    from scraper.orchestrator import Orchestrator
    from output.markdown import save_patient_markdown
    from output.docx_export import export_docx

    session = VGHSession()
    await session.start()
    try:
        await session.login()

        console.print(f"[bold]Fetching patients for doctor code {doctor_code}...[/bold]")
        patients = await fetch_searched_patients(session, doc_id=doctor_code)
        console.print(f"Found [green]{len(patients)}[/green] patients")

        # Build hist_no list from search results
        pat_list = []
        for row in patients:
            hist_no = row[1] if len(row) > 1 else row[0]
            pat_list.append({"hist_no": hist_no})

        orch = Orchestrator(session)
        results = await orch.process_patient_list(
            pat_list,
            on_progress=lambda msg: console.print(f"  {msg}"),
        )

        # Save outputs
        summaries: list[tuple[str, str]] = []
        for hist_no, md, err in results:
            if md:
                save_patient_markdown(hist_no, md)
                summaries.append((hist_no, md))
                console.print(f"[green]✓[/green] {hist_no}")
            else:
                console.print(f"[red]✗[/red] {hist_no}: {err}")

        if summaries:
            path = export_docx(summaries, doctor_code=doctor_code)
            console.print(f"\n[bold green]Word document saved:[/bold green] {path}")

    finally:
        await session.close()


async def _run_single(chart_no: str, from_cache: bool = False) -> None:
    from scraper.session import VGHSession
    from scraper.orchestrator import Orchestrator
    from output.markdown import save_patient_markdown

    session = VGHSession()
    await session.start()
    try:
        if not from_cache:
            await session.login()

        orch = Orchestrator(session)
        md = await orch.process_patient(
            chart_no,
            from_cache=from_cache,
            on_progress=lambda msg: console.print(f"  {msg}"),
        )
        path = save_patient_markdown(chart_no, md)
        console.print(f"\n[bold green]Summary saved:[/bold green] {path}")
        console.print(md)
    finally:
        await session.close()


async def _retry_failed() -> None:
    from cache.manager import list_cached_patients, load_cache
    from scraper.session import VGHSession
    from scraper.orchestrator import Orchestrator
    from output.markdown import save_patient_markdown

    cached = list_cached_patients()
    if not cached:
        console.print("[yellow]No cached patients found[/yellow]")
        return

    session = VGHSession()
    await session.start()
    try:
        await session.login()
        orch = Orchestrator(session)

        for chart_no in cached:
            # Check if summary already exists
            from cache.manager import _cache_dir
            summary_path = _cache_dir() / f"{chart_no}_summary.md"
            if summary_path.exists():
                continue

            console.print(f"Retrying [yellow]{chart_no}[/yellow]...")
            try:
                md = await orch.process_patient(
                    chart_no,
                    on_progress=lambda msg: console.print(f"  {msg}"),
                )
                save_patient_markdown(chart_no, md)
                console.print(f"[green]✓[/green] {chart_no}")
            except Exception as e:
                console.print(f"[red]✗[/red] {chart_no}: {e}")
    finally:
        await session.close()


@app.command()
def run(
    doctor_code: str = typer.Option("", "--doctor-code", "-d", help="Doctor code for patient list"),
    chart_no: str = typer.Option("", "--chart-no", "-c", help="Single patient chart number"),
    api_key: str = typer.Option("", "--api-key", "-k", help="OpenRouter API key (overrides .env)"),
    retry_failed: bool = typer.Option(False, "--retry-failed", help="Retry previously failed patients"),
    from_cache: bool = typer.Option(False, "--from-cache", help="Skip scraping, re-run AI on cached data"),
) -> None:
    """Run the patient scraper + AI summary pipeline."""
    _setup_logging()

    if api_key:
        settings.openrouter_api_key = api_key

    if retry_failed:
        asyncio.run(_retry_failed())
    elif chart_no:
        asyncio.run(_run_single(chart_no, from_cache=from_cache))
    elif doctor_code:
        asyncio.run(_run_full(doctor_code, from_cache=from_cache))
    else:
        dc = settings.doctor_code
        if dc:
            asyncio.run(_run_full(dc))
        else:
            console.print("[red]Provide --doctor-code or --chart-no[/red]")
            raise typer.Exit(1)


if __name__ == "__main__":
    app()
