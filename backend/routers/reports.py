from html import escape

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from core.database import get_db
from models.report import Report
from schemas.report import ManualReportCreate, ReportCreate, ReportResponse
from sap.sap_service import sap_service
from services.report_service import ReportService


router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


def display(value: object) -> str:
    if value is None or value == "":
        return "Non renseigné"
    if isinstance(value, bool):
        return "Oui" if value else "Non"
    return escape(str(value))


def render_reports_html(reports: list[Report]) -> str:
    rows = "".join(
        f"""
        <tr>
          <td><strong>{display(report.report_number)}</strong></td>
          <td>{display(report.reclamant_name or report.declarant)}</td>
          <td>{display(report.classification)}</td>
          <td>{display(report.location)}</td>
          <td>{display(report.event_datetime)}</td>
          <td>{display(report.immediate_danger)}</td>
          <td><span class=\"status\">{display(report.status)}</span></td>
          <td><a class=\"pdf-link\" href=\"/reports/{report.id}/pdf\" target=\"_blank\">PDF</a></td>
        </tr>
        """
        for report in reports
    )
    if not rows:
        rows = "<tr><td colspan=\"8\" class=\"empty\">Aucune réclamation enregistrée.</td></tr>"

    return f"""
    <!doctype html>
    <html lang=\"fr\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Réclamations HSE - AMANE AI</title>
        <style>
          :root {{
            --ink: #12201a;
            --muted: #66756e;
            --line: rgba(30, 57, 46, 0.14);
            --brand: #1f7a5b;
            --panel: rgba(255, 255, 255, 0.88);
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }}
          * {{ box-sizing: border-box; }}
          body {{
            margin: 0;
            min-height: 100vh;
            color: var(--ink);
            background: linear-gradient(145deg, #f7faf8 0%, #e9f1ed 52%, #f8f5f1 100%);
          }}
          main {{ width: min(1180px, calc(100% - 32px)); margin: 0 auto; padding: 28px 0; }}
          header {{ display: flex; align-items: end; justify-content: space-between; gap: 16px; margin-bottom: 18px; }}
          h1 {{ margin: 0 0 6px; font-size: clamp(28px, 4vw, 44px); letter-spacing: 0; }}
          p {{ margin: 0; color: var(--muted); }}
          a {{ color: var(--brand); font-weight: 800; text-decoration: none; }}
          .actions {{ display: flex; gap: 10px; flex-wrap: wrap; }}
          .pdf-link,
          .button {{ display: inline-flex; align-items: center; justify-content: center; min-height: 34px; border-radius: 8px; padding: 0 10px; background: #1f7a5b; color: white; font-size: 12px; font-weight: 900; }}
          .button.secondary {{ border: 1px solid var(--line); background: white; color: var(--ink); }}
          .card {{ overflow: hidden; border: 1px solid var(--line); border-radius: 8px; background: var(--panel); box-shadow: 0 24px 70px rgba(18, 32, 26, 0.14); backdrop-filter: blur(16px); }}
          table {{ width: 100%; border-collapse: collapse; background: white; }}
          th, td {{ padding: 12px 14px; border-bottom: 1px solid rgba(30, 57, 46, 0.1); text-align: left; vertical-align: top; font-size: 14px; line-height: 1.45; }}
          th {{ color: #14543f; background: #eef8f2; font-size: 12px; font-weight: 900; text-transform: uppercase; }}
          tr:last-child td {{ border-bottom: 0; }}
          td {{ overflow-wrap: anywhere; }}
          .status {{ display: inline-flex; align-items: center; min-height: 26px; border-radius: 999px; padding: 0 10px; background: #e7f3ec; color: #14543f; font-size: 12px; font-weight: 900; text-transform: capitalize; }}
          .empty {{ color: var(--muted); text-align: center; }}
          @media print {{ .actions {{ display: none; }} main {{ width: 100%; padding: 0; }} .card {{ box-shadow: none; }} }}
          @media (max-width: 860px) {{ header {{ display: grid; }} .card {{ overflow-x: auto; }} table {{ min-width: 960px; }} }}
        </style>
      </head>
      <body>
        <main>
          <header>
            <div>
              <h1>Réclamations HSE</h1>
              <p>Table professionnelle des déclarations enregistrées par AMANE AI.</p>
            </div>
            <div class=\"actions\">
              <a class=\"button secondary\" href=\"/app/\">Retour assistant</a>
              <a class=\"button\" href=\"javascript:window.print()\">Imprimer la liste</a>
            </div>
          </header>
          <section class=\"card\">
            <table>
              <thead>
                <tr>
                  <th>Numéro</th>
                  <th>Réclamant</th>
                  <th>Type</th>
                  <th>Site / Localisation</th>
                  <th>Date événement</th>
                  <th>Danger immédiat</th>
                  <th>Statut</th>
                  <th>Export</th>
                </tr>
              </thead>
              <tbody>{rows}</tbody>
            </table>
          </section>
        </main>
      </body>
    </html>
    """



def render_dashboard_pdf_html(data: dict) -> str:
    kpis = data.get("kpis", {})
    reports = data.get("latest", [])

    def urgency_class(value: object) -> str:
        urgency = str(value or "").lower()
        if urgency in {"critical", "high"}:
            return "danger"
        if urgency == "medium":
            return "warning"
        return "neutral"

    def compact(value: object, max_len: int = 96) -> str:
        text = "Non renseigné" if value in (None, "") else str(value)
        return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…"

    rows = "".join(
        f"""
        <tr>
          <td class="num"><strong>{display(report.get('report_number'))}</strong><span>{display(report.get('event_datetime'))}</span></td>
          <td>{display(report.get('reclamant'))}</td>
          <td><span class="tag type">{display(report.get('classification'))}</span><small>{display(report.get('danger_type'))}</small></td>
          <td>{display(report.get('location_label') or report.get('location'))}</td>
          <td><span class="tag {urgency_class(report.get('urgency'))}">{display(report.get('urgency'))}</span></td>
          <td><span class="tag {'danger' if report.get('immediate_danger') else 'neutral'}">{display('Oui' if report.get('immediate_danger') else 'Non')}</span></td>
          <td><span class="tag {'ready' if report.get('sap_ready') else 'warning'}">{display('Prêt' if report.get('sap_ready') else 'Attente')}</span></td>
          <td><span class="tag neutral">{display(report.get('status'))}</span></td>
          <td>{display(compact(report.get('recommended_action'), 120))}</td>
          <td>{display(compact(report.get('source'), 70))}</td>
        </tr>
        """
        for report in reports
    )
    if not rows:
        rows = '<tr><td colspan="10" class="empty">Aucune réclamation enregistrée.</td></tr>'

    return f"""
    <!doctype html>
    <html lang="fr">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Export réclamations HSE - PDF</title>
        <style>
          @page {{ size: A4 landscape; margin: 10mm; }}
          :root {{ --ink: #2f3337; --muted: #6f7479; --line: #d9dee2; --brand: #f58220; --grey: #4a4f54; --soft: #fff3e8; font-family: Arial, sans-serif; }}
          * {{ box-sizing: border-box; }}
          body {{ margin: 0; color: var(--ink); background: #eef0f2; }}
          main {{ width: min(1240px, calc(100% - 24px)); margin: 14px auto; background: white; border: 1px solid var(--line); border-radius: 8px; padding: 18px; }}
          .actions {{ display: flex; gap: 10px; margin-bottom: 12px; }}
          button, a {{ min-height: 34px; border: 0; border-radius: 8px; padding: 0 13px; background: var(--brand); color: white; font: inherit; font-weight: 900; text-decoration: none; cursor: pointer; display: inline-flex; align-items: center; }}
          header {{ display: grid; grid-template-columns: 1fr auto; gap: 18px; align-items: start; border-bottom: 3px solid var(--brand); padding-bottom: 12px; margin-bottom: 14px; }}
          h1 {{ margin: 0 0 6px; font-size: 28px; }}
          p {{ margin: 0; color: var(--muted); line-height: 1.35; }}
          .brand {{ text-align: right; }}
          .brand strong {{ display: block; font-size: 24px; color: var(--grey); }}
          .brand span {{ display: block; margin-top: 4px; color: var(--brand); font-weight: 900; font-size: 12px; text-transform: uppercase; }}
          .meta {{ display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-bottom: 12px; }}
          .meta-item, .kpi {{ border: 1px solid var(--line); border-radius: 8px; padding: 9px; background: #fff; }}
          .meta-item span, .kpi span {{ display: block; color: var(--muted); font-size: 10px; font-weight: 900; text-transform: uppercase; }}
          .meta-item strong {{ display: block; margin-top: 5px; font-size: 12px; }}
          .kpis {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-bottom: 14px; }}
          .kpi {{ border-top: 4px solid var(--brand); }}
          .kpi strong {{ display: block; margin-top: 6px; font-size: 24px; color: var(--brand); }}
          .table-title {{ display: flex; justify-content: space-between; align-items: center; gap: 12px; margin: 10px 0 8px; }}
          .table-title h2 {{ margin: 0; font-size: 16px; }}
          .table-title span {{ color: var(--muted); font-size: 11px; font-weight: 800; }}
          table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
          th, td {{ padding: 7px 8px; border: 1px solid var(--line); text-align: left; vertical-align: top; font-size: 10.5px; line-height: 1.32; overflow-wrap: anywhere; }}
          th {{ background: var(--soft); color: var(--grey); font-weight: 900; text-transform: uppercase; }}
          th:nth-child(1) {{ width: 11%; }} th:nth-child(2) {{ width: 10%; }} th:nth-child(3) {{ width: 12%; }} th:nth-child(4) {{ width: 13%; }}
          th:nth-child(5), th:nth-child(6), th:nth-child(7), th:nth-child(8) {{ width: 7%; }} th:nth-child(9) {{ width: 19%; }} th:nth-child(10) {{ width: 7%; }}
          tbody tr:nth-child(even) {{ background: #fafafa; }}
          .num span, td small {{ display: block; margin-top: 3px; color: var(--muted); font-size: 9.5px; }}
          .tag {{ display: inline-flex; align-items: center; min-height: 20px; border-radius: 999px; padding: 0 7px; font-weight: 900; font-size: 9.5px; background: #eef0f2; color: var(--grey); }}
          .tag.type {{ background: #fff3e8; color: #a85100; }}
          .tag.danger {{ background: #fff0e8; color: #c9471f; }}
          .tag.warning {{ background: #fff6df; color: #8a5b13; }}
          .tag.ready {{ background: #eef7f1; color: #28724d; }}
          .tag.neutral {{ background: #eef0f2; color: var(--grey); }}
          .empty {{ text-align: center; color: var(--muted); padding: 22px; }}
          footer {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 14px; }}
          .signature {{ min-height: 54px; border: 1px solid var(--line); border-radius: 8px; padding: 8px; color: var(--muted); font-size: 10px; }}
          @media print {{ body {{ background: white; }} main {{ width: 100%; margin: 0; border: 0; padding: 0; }} .actions {{ display: none; }} }}
        </style>
      </head>
      <body>
        <main>
          <div class="actions">
            <button onclick="window.print()">Télécharger / Enregistrer en PDF</button>
            <a href="/app/dashboard.html">Retour dashboard</a>
          </div>
          <header>
            <div>
              <h1>Réclamations HSE</h1>
              <p>Export tabulaire des remontées SONASID collectées par AMANE. Document destiné au suivi HSE, au traitement manager et à la préparation SAP.</p>
            </div>
            <div class="brand"><strong>SONASID</strong><span>HSE Control Room</span></div>
          </header>
          <section class="meta">
            <div class="meta-item"><span>Société</span><strong>SONASID</strong></div>
            <div class="meta-item"><span>Site</span><strong>Nador</strong></div>
            <div class="meta-item"><span>Source</span><strong>AMANE</strong></div>
            <div class="meta-item"><span>Date export</span><strong>{display(data.get('updated_at'))}</strong></div>
          </section>
          <section class="kpis">
            <div class="kpi"><span>Total</span><strong>{display(kpis.get('total', 0))}</strong></div>
            <div class="kpi"><span>Aujourd'hui</span><strong>{display(kpis.get('created_today', 0))}</strong></div>
            <div class="kpi"><span>Ouvertes</span><strong>{display(kpis.get('open_reports', 0))}</strong></div>
            <div class="kpi"><span>Priorité</span><strong>{display(kpis.get('high_priority', 0))}</strong></div>
            <div class="kpi"><span>Danger immédiat</span><strong>{display(kpis.get('immediate_danger', 0))}</strong></div>
            <div class="kpi"><span>SAP prêt</span><strong>{display(kpis.get('sap_ready', 0))}</strong></div>
          </section>
          <div class="table-title"><h2>Tableau des réclamations</h2><span>{display(len(reports))} ligne(s) exportée(s)</span></div>
          <table>
            <thead>
              <tr><th>Numéro / date</th><th>Réclamant</th><th>Type / danger</th><th>Zone</th><th>Urgence</th><th>Danger immédiat</th><th>SAP</th><th>Statut</th><th>Action recommandée</th><th>Source</th></tr>
            </thead>
            <tbody>{rows}</tbody>
          </table>
          <footer>
            <div class="signature">Validation Responsable HSE</div>
            <div class="signature">Traitement manager / maintenance</div>
            <div class="signature">Commentaire / clôture</div>
          </footer>
        </main>
      </body>
    </html>
    """
def render_report_pdf_html(report: Report) -> str:
    fields = [
        ("Numéro de réclamation", report.report_number),
        ("Société", "SONASID"),
        ("Réclamant", report.reclamant_name or report.declarant),
        ("Type de signalement", report.classification),
        ("Date et heure", report.event_datetime),
        ("Site / Localisation", report.location),
        ("Danger immédiat", report.immediate_danger),
        ("Personne observée", report.observed_person),
        ("Description", report.description),
        ("Action immédiate", report.immediate_action),
        ("Analyse du risque", report.risk_analysis),
        ("Action recommandée IA", report.recommended_action),
        ("Urgence", report.urgency),
        ("Type de danger IA", report.danger_type),
        ("Statut", report.status),
    ]
    optional_ai_labels = {"Action recommand?e IA", "Urgence", "Type de danger IA"}
    visible_fields = [
        (label, value)
        for label, value in fields
        if label not in optional_ai_labels or value not in (None, "")
    ]
    rows = "".join(
        f"<tr><th>{display(label)}</th><td>{display(value)}</td></tr>"
        for label, value in visible_fields
    )
    return f"""
    <!doctype html>
    <html lang=\"fr\">
      <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>{display(report.report_number)} - PDF</title>
        <style>
          @page {{ size: A4; margin: 16mm; }}
          :root {{ --ink: #12201a; --muted: #66756e; --line: #d8e2dc; --brand: #1f7a5b; font-family: Arial, sans-serif; }}
          * {{ box-sizing: border-box; }}
          body {{ margin: 0; color: var(--ink); background: #eef3f0; }}
          main {{ width: min(900px, calc(100% - 32px)); margin: 24px auto; background: white; border: 1px solid var(--line); border-radius: 8px; padding: 28px; }}
          header {{ display: flex; justify-content: space-between; gap: 18px; border-bottom: 3px solid var(--brand); padding-bottom: 16px; margin-bottom: 22px; }}
          h1 {{ margin: 0 0 8px; font-size: 28px; letter-spacing: 0; }}
          p {{ margin: 0; color: var(--muted); line-height: 1.45; }}
          .brand {{ color: var(--brand); font-weight: 900; font-size: 20px; }}
          .actions {{ display: flex; gap: 10px; margin-bottom: 18px; }}
          button, a {{ min-height: 38px; border: 0; border-radius: 8px; padding: 0 14px; background: var(--brand); color: white; font: inherit; font-weight: 900; text-decoration: none; cursor: pointer; }}
          a {{ display: inline-flex; align-items: center; }}
          table {{ width: 100%; border-collapse: collapse; }}
          th, td {{ padding: 11px 12px; border: 1px solid var(--line); text-align: left; vertical-align: top; font-size: 14px; line-height: 1.45; }}
          th {{ width: 32%; background: #eef8f2; color: #14543f; font-weight: 900; }}
          footer {{ margin-top: 26px; display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }}
          .signature {{ min-height: 86px; border: 1px solid var(--line); padding: 12px; color: var(--muted); }}
          @media print {{ body {{ background: white; }} main {{ width: 100%; margin: 0; border: 0; border-radius: 0; padding: 0; }} .actions {{ display: none; }} }}
        </style>
      </head>
      <body>
        <main>
          <div class=\"actions\">
            <button onclick=\"window.print()\">Télécharger / Enregistrer en PDF</button>
            <a href=\"/reports/\">Retour rapports</a>
          </div>
          <header>
            <div>
              <h1>Fiche de réclamation HSE</h1>
              <p>Rapport généré par AMANE AI à partir de la déclaration vocale.</p>
            </div>
            <div class=\"brand\">SONASID</div>
          </header>
          <table><tbody>{rows}</tbody></table>
          <footer>
            <div class=\"signature\">Validation Responsable HSE</div>
            <div class=\"signature\">Signature / Commentaire</div>
          </footer>
        </main>
      </body>
    </html>
    """



@router.post("/manual", response_model=ReportResponse)
def create_manual_report(
    report: ManualReportCreate,
    db: Session = Depends(get_db),
):
    report_number = ReportService.generate_report_number(db)
    data = report.model_dump()
    report_ai = {
        "title": f"Réclamation HSE - {data['classification']}",
        "urgency": data.get("urgency") or "MEDIUM",
        "danger_type": data.get("danger_type") or data["classification"],
        "recommended_action": data.get("recommended_action") or data["immediate_action"],
        "missing_fields": [],
        "sap_ready": True,
        "rag_sources": [],
    }
    sap_payload = sap_service.build_notification_payload(
        report_number=report_number,
        collected_data=data,
        report_ai=report_ai,
    )

    data["report_number"] = report_number
    data["source"] = "manual_sap_form"
    data["language"] = "fr"
    data["ai_title"] = report_ai["title"]
    data["urgency"] = report_ai["urgency"]
    data["danger_type"] = report_ai["danger_type"]
    data["recommended_action"] = report_ai["recommended_action"]
    data["rag_sources"] = []
    data["agent_trace"] = {"mode": "manual_sap_form", "report": report_ai}
    data["sap_payload"] = sap_payload
    data["raw_collected_data"] = dict(data)
    return ReportService.create(db, ReportCreate(**data))

@router.post("/", response_model=ReportResponse)
def create_report(
    report: ReportCreate,
    db: Session = Depends(get_db),
):
    return ReportService.create(db, report)



@router.get("/dashboard")
def dashboard_page():
    return RedirectResponse(url="/app/dashboard.html")



@router.get("/dashboard/pdf", response_class=HTMLResponse)
def dashboard_pdf(db: Session = Depends(get_db)):
    return HTMLResponse(render_dashboard_pdf_html(ReportService.dashboard_data(db)))
@router.get("/dashboard/data")
def dashboard_data(db: Session = Depends(get_db)):
    return ReportService.dashboard_data(db)

@router.get("/{report_id}/pdf", response_class=HTMLResponse)
def download_report_pdf_page(
    report_id: int,
    db: Session = Depends(get_db),
):
    report = ReportService.get_by_id(db, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Réclamation introuvable")
    return HTMLResponse(render_report_pdf_html(report))


@router.get("/", response_model=list[ReportResponse] | None)
def get_reports(
    request: Request,
    db: Session = Depends(get_db),
):
    reports = ReportService.get_all(db)
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        return HTMLResponse(render_reports_html(reports))
    return reports






