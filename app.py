"""Local web server for the Project Cost Estimation Tool demo (Python standard library)."""
from __future__ import annotations
import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, unquote

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from database.db import initialize_database, DB_PATH, get_connection
from backend.controllers.project_controller import create_project, update_project, get_one, get_many, remove
from backend.models.spm_model import workspace_data, list_items, create_item, update_item, delete_item, seed_spm_data


class Handler(BaseHTTPRequestHandler):
    server_version = "PCETDemo/1.0"

    def send_json(self, data, status=200):
        encoded = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(encoded)

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise ValueError("Request is too large.")
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        try:
            if path == "/api/health":
                self.send_json({"status": "ok", "service": "Project Cost Estimation Tool", "database": "connected"})
                return
            if path == "/api/projects":
                search = parse_qs(parsed.query).get("search", [""])[0]
                self.send_json({"projects": get_many(search)})
                return
            if path == "/api/spm/data":
                self.send_json(workspace_data())
                return
            if path.startswith("/api/spm/"):
                resource = path.strip("/").split("/")[-1]
                if resource in ("requirements", "tasks", "risks", "team", "changes"):
                    self.send_json({resource: list_items(resource)})
                    return
            if path.startswith("/api/projects/"):
                project_id = int(path.rsplit("/", 1)[1])
                project = get_one(project_id)
                if project:
                    self.send_json(project)
                else:
                    self.send_json({"error": "Project not found."}, 404)
                return
            if path == "/api/database-summary":
                # Local-development evidence endpoint. Do not expose this endpoint in a public deployment.
                with get_connection() as con:
                    counts = {table: con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                              for table in ("users", "projects", "team_members", "cost_items", "estimates")}
                    rows = [dict(x) for x in con.execute(
                        "SELECT p.id,p.name,p.project_type,e.total_cost,e.created_at FROM projects p "
                        "LEFT JOIN estimates e ON e.id=(SELECT MAX(e2.id) FROM estimates e2 WHERE e2.project_id=p.id) "
                        "ORDER BY p.id")]
                self.send_json({"counts": counts, "projects": rows})
                return
            if path == "/" or path == "/index.html":
                target = ROOT / "frontend" / "index.html"
            elif path.startswith("/frontend/"):
                target = (ROOT / path.lstrip("/")).resolve()
                if ROOT not in target.parents:
                    self.send_json({"error": "Invalid path."}, 400)
                    return
            else:
                self.send_json({"error": "Route not found."}, 404)
                return
            if not target.is_file():
                self.send_json({"error": "Static file not found."}, 404)
                return
            body = target.read_bytes()
            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type in ("application/javascript", "application/json"):
                content_type += "; charset=utf-8"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, 400)
        except Exception as exc:
            self.send_json({"error": "Internal server error", "detail": str(exc)}, 500)

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/projects":
            try:
                payload = self.read_json()
                project = create_project(payload)
                self.send_json({"message": "Estimate saved successfully.", "project": project}, 201)
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except Exception as exc:
                self.send_json({"error": "Unable to save estimate.", "detail": str(exc)}, 500)
        elif path.startswith("/api/spm/"):
            try:
                resource = path.strip("/").split("/")[-1]
                if resource not in ("requirements", "tasks", "risks", "team", "changes"):
                    self.send_json({"error": "Unknown SPM resource."}, 404); return
                item = create_item(resource, self.read_json())
                self.send_json({"message": "SPM record created.", "item": item}, 201)
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except Exception as exc:
                self.send_json({"error": "Unable to create SPM record.", "detail": str(exc)}, 500)
        else:
            self.send_json({"error": "Route not found."}, 404)

    def do_PUT(self):
        path = urlparse(self.path).path
        if path.startswith("/api/projects/"):
            try:
                project_id = int(path.rsplit("/", 1)[1])
                project = update_project(project_id, self.read_json())
                self.send_json({"message": "Estimate updated and new history snapshot saved.", "project": project})
            except LookupError as exc:
                self.send_json({"error": str(exc)}, 404)
            except (ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except Exception as exc:
                self.send_json({"error": "Unable to update estimate.", "detail": str(exc)}, 500)
        elif path.startswith("/api/spm/"):
            try:
                bits = path.strip("/").split("/")
                resource = bits[2]
                item_id = int(bits[3])
                if resource not in ("requirements", "tasks", "risks", "team", "changes"):
                    self.send_json({"error": "Unknown SPM resource."}, 404); return
                item = update_item(resource, item_id, self.read_json())
                self.send_json({"message": "SPM record updated.", "item": item})
            except LookupError as exc:
                self.send_json({"error": str(exc)}, 404)
            except (ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as exc:
                self.send_json({"error": str(exc)}, 400)
            except Exception as exc:
                self.send_json({"error": "Unable to update SPM record.", "detail": str(exc)}, 500)
        else:
            self.send_json({"error": "Route not found."}, 404)

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith("/api/projects/"):
            try:
                project_id = int(path.rsplit("/", 1)[1])
                if remove(project_id):
                    self.send_json({"message": "Project deleted."})
                else:
                    self.send_json({"error": "Project not found."}, 404)
            except ValueError:
                self.send_json({"error": "Project ID must be numeric."}, 400)
        elif path.startswith("/api/spm/"):
            try:
                bits = path.strip("/").split("/")
                resource, item_id = bits[2], int(bits[3])
                if resource not in ("requirements", "tasks", "risks", "team", "changes"):
                    self.send_json({"error": "Unknown SPM resource."}, 404); return
                if delete_item(resource, item_id): self.send_json({"message": "SPM record deleted."})
                else: self.send_json({"error": "SPM record not found."}, 404)
            except (ValueError, IndexError):
                self.send_json({"error": "Invalid SPM resource or record ID."}, 400)
        else:
            self.send_json({"error": "Route not found."}, 404)

    def log_message(self, fmt, *args):
        print("[%s] %s" % (self.log_date_time_string(), fmt % args))


def seed_demo_data():
    with get_connection() as con:
        count = con.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
    if count:
        return
    from backend.models.project_model import save_project
    demos = [
        {
            "name": "Customer Portal Revamp", "description": "Refresh the customer-facing portal and account workflows.",
            "project_type": "Web Application", "duration_months": 3, "hours_per_day": 8,
            "working_days_per_week": 5, "contingency_percent": 10, "actual_cost": 0,
            "team": [{"role":"Developer","count":2,"hourly_rate":550},{"role":"Designer","count":1,"hourly_rate":450},{"role":"Tester","count":1,"hourly_rate":350}],
            "resources": [{"name":"Cloud hosting","amount":18000},{"name":"Software licences","amount":8500}],
            "testing": [{"name":"QA environment and tools","amount":12000}],
            "overhead": [{"name":"Project administration","amount":7000}],
        },
        {
            "name": "Inventory Analytics", "description": "Dashboard to track stock, replenishment and reports.",
            "project_type": "Analytics Dashboard", "duration_months": 2, "hours_per_day": 7,
            "working_days_per_week": 5, "contingency_percent": 12, "actual_cost": 0,
            "team": [{"role":"Developer","count":2,"hourly_rate":600},{"role":"Data Analyst","count":1,"hourly_rate":500}],
            "resources": [{"name":"Cloud hosting","amount":12000},{"name":"Analytics tools","amount":5000}],
            "testing": [{"name":"Functional testing","amount":9000}],
            "overhead": [{"name":"Documentation and coordination","amount":4500}],
        },
        {
            "name": "Mobile Banking Dashboard", "description": "Sample estimate for a secure mobile banking dashboard.",
            "project_type": "Mobile Application", "duration_months": 4, "hours_per_day": 7.5,
            "working_days_per_week": 5, "contingency_percent": 15, "actual_cost": 0,
            "team": [{"role":"Developer","count":3,"hourly_rate":700},{"role":"Designer","count":1,"hourly_rate":500},{"role":"Tester","count":2,"hourly_rate":420}],
            "resources": [{"name":"Hosting and monitoring","amount":35000},{"name":"Development tools","amount":15000}],
            "testing": [{"name":"Security and QA testing","amount":28000}],
            "overhead": [{"name":"Project management","amount":14000}],
        },
    ]
    for demo in demos:
        save_project(demo)


def main():
    initialize_database()
    seed_demo_data()
    seed_spm_data()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    print(f"Project Cost Estimation Tool running at http://127.0.0.1:{port}")
    print(f"SQLite database: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
