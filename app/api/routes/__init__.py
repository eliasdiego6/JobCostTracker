from app.api.routes import export, jobs, notes, qb, sync, users

ROUTERS = [users.router, jobs.router, notes.router, qb.router, sync.router, export.router]
