import csv
import hashlib
import io
import os
import secrets
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response

app = FastAPI(title="Northstar Hiring")
DB_PATH = os.environ.get("DATABASE_PATH", "pipeline.db")
STAGES = ["Applied", "Screening", "Interview", "Offer", "Hired"]
ACTIVE_STAGES = set(STAGES)
SOURCE_OPTIONS = ["Referral", "Careers page", "LinkedIn", "Agency", "Inbound"]

CSS = """
<style>
*{box-sizing:border-box}body{margin:0;background:#f7f8fc;color:#152033;font:14px Inter,system-ui,sans-serif}nav{background:#17243d;color:#fff;padding:15px 5vw;display:flex;gap:18px;align-items:center}nav a{color:#dce7ff;text-decoration:none}.brand{font-weight:800;color:#fff!important;font-size:17px;margin-right:auto}.badge{background:#f0a33d;color:#17243d;padding:2px 7px;border-radius:10px;font-weight:800}main{max-width:1180px;margin:28px auto;padding:0 20px}h1{font-size:27px;margin:0 0 7px}h2{font-size:18px;margin-top:0}.muted{color:#68758b}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.card,form,.panel{background:#fff;border:1px solid #e4e8f0;border-radius:10px;padding:17px;box-shadow:0 1px 2px #16274d08}.metric b{display:block;font-size:30px;margin-top:8px}.split{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:18px}table{width:100%;border-collapse:collapse;background:#fff;border:1px solid #e4e8f0;border-radius:10px;overflow:hidden}th,td{text-align:left;padding:11px;border-bottom:1px solid #edf0f5}th{font-size:12px;color:#657186;text-transform:uppercase;background:#fafbfe}tr:last-child td{border:0}a{color:#315cc5}button,.button{background:#315cc5;color:#fff;border:0;border-radius:6px;padding:8px 12px;font:inherit;text-decoration:none;cursor:pointer;display:inline-block}button.secondary,.button.secondary{background:#e9edf5;color:#26354e}button.danger{background:#bf3b4c}.stage{font-size:12px;padding:4px 8px;border-radius:12px;background:#e9eefb;color:#28468a;white-space:nowrap}.rejected{background:#fce7ea;color:#aa2537}.flash{padding:10px 13px;border-radius:7px;background:#fff0d9;color:#805309;margin-bottom:15px}.error{background:#fce7ea;color:#9e2635}input,select,textarea{width:100%;padding:8px;border:1px solid #cdd5e2;border-radius:6px;margin:4px 0 11px;font:inherit}label{font-size:12px;font-weight:700;color:#566276}.row{display:flex;gap:10px;align-items:end}.row>*{flex:1}.actions{display:flex;gap:8px;flex-wrap:wrap}.timeline{border-left:2px solid #d9e1ee;padding-left:16px}.event{padding:0 0 16px}.event small{color:#68758b;display:block;margin-top:3px}.filters{display:grid;grid-template-columns:2fr repeat(4,1fr);gap:9px;margin-bottom:15px}.alert{border-left:4px solid #e4962c;padding:11px;background:#fffaf1;margin:8px 0}.right{margin-left:auto}@media(max-width:800px){.grid{grid-template-columns:1fr 1fr}.split{grid-template-columns:1fr}.filters{grid-template-columns:1fr}.row{display:block}}
</style>"""

@contextmanager
def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    try:
        yield con
        con.commit()
    finally:
        con.close()

def password(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()

def init_db():
    with db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('recruiter','interviewer')));
        CREATE TABLE IF NOT EXISTS openings (id INTEGER PRIMARY KEY, title TEXT NOT NULL, department TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('open','archived')), created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS applications (id INTEGER PRIMARY KEY, opening_id INTEGER NOT NULL REFERENCES openings(id), candidate_name TEXT NOT NULL, email TEXT NOT NULL, source TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '', stage TEXT NOT NULL, rejected_from TEXT, applied_at TEXT NOT NULL, stage_changed_at TEXT NOT NULL, updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS assignments (application_id INTEGER NOT NULL REFERENCES applications(id) ON DELETE CASCADE, user_id INTEGER NOT NULL REFERENCES users(id), PRIMARY KEY(application_id,user_id));
        CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, application_id INTEGER NOT NULL REFERENCES applications(id), actor_id INTEGER REFERENCES users(id), kind TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS alert_dismissals (application_id INTEGER NOT NULL REFERENCES applications(id), stage TEXT NOT NULL, dismissed_by INTEGER NOT NULL REFERENCES users(id), PRIMARY KEY(application_id,stage));
        """)
        if not con.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            now = datetime.utcnow().isoformat()
            con.executemany("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)", [
                ("Riley Recruiter", "recruiter@northstar.test", password("demo-password"), "recruiter"),
                ("Ira Interviewer", "interviewer@northstar.test", password("demo-password"), "interviewer"),
                ("Mae Interviewer", "mae@northstar.test", password("demo-password"), "interviewer")])
            con.executemany("INSERT INTO openings(title,department,description,status,created_at,updated_at) VALUES(?,?,?,?,?,?)", [
                ("Senior Backend Engineer","Engineering","Build reliable workflow services.","open",now,now),
                ("Account Executive","Sales","Grow our mid-market accounts.","open",now,now),
                ("Support Specialist","Customer Success","Help customers get value quickly.","open",now,now),
                ("Product Designer","Design","Archived example role.","archived",now,now)])
            seed = [(1,"Avery Chen","avery@example.test","Referral","Interview",14),(1,"Mina Patel","mina@example.test","Careers page","Screening",3),(1,"Jordan Lee","jordan@example.test","LinkedIn","Applied",1),(2,"Sam Rivera","sam@example.test","Agency","Offer",2),(2,"Taylor Kim","taylor@example.test","Inbound","Interview",8),(3,"Nora Diaz","nora@example.test","Careers page","Rejected",12)]
            for opening, name, email, source, stage, age in seed:
                stamp=(datetime.utcnow()-timedelta(days=age)).isoformat()
                rejected_from="Screening" if stage=="Rejected" else None
                cur=con.execute("INSERT INTO applications(opening_id,candidate_name,email,source,notes,stage,rejected_from,applied_at,stage_changed_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",(opening,name,email,source,"Seeded candidate.",stage,rejected_from,stamp,stamp,stamp))
                aid=cur.lastrowid
                con.execute("INSERT INTO events(application_id,actor_id,kind,detail,created_at) VALUES(?,?,?,?,?)",(aid,1,"created","Application created",stamp))
                if stage != "Applied": con.execute("INSERT INTO events(application_id,actor_id,kind,detail,created_at) VALUES(?,?,?,?,?)",(aid,1,"stage",f"Applied → {stage}",stamp))
            con.executemany("INSERT INTO assignments(application_id,user_id) VALUES(?,?)",[(1,2),(1,3),(5,2)])

@app.on_event("startup")
def startup(): init_db()

def now(): return datetime.utcnow().isoformat()
def current_user(request: Request):
    uid=request.cookies.get("user_id")
    if not uid: return None
    with db() as con: return con.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
def require(request: Request, role: Optional[str]=None):
    user=current_user(request)
    if not user: raise HTTPException(401, "Please sign in")
    if role and user["role"] != role: raise HTTPException(403, "You do not have permission for this action")
    return user
def event(con, app_id, actor_id, kind, detail):
    con.execute("INSERT INTO events(application_id,actor_id,kind,detail,created_at) VALUES(?,?,?,?,?)",(app_id,actor_id,kind,detail,now()))
def visible_clause(user):
    return ("", []) if user["role"]=="recruiter" else (" JOIN assignments vis ON vis.application_id=a.id WHERE vis.user_id=?", [user["id"]])
def page(title, body, user=None, message=""):
    nav=""
    if user:
        stalled=0
        if user["role"]=="recruiter":
            with db() as con: stalled=con.execute("SELECT count(*) FROM applications a LEFT JOIN alert_dismissals d ON d.application_id=a.id AND d.stage=a.stage WHERE a.stage != 'Rejected' AND datetime(a.stage_changed_at) < datetime('now','-10 days') AND d.application_id IS NULL").fetchone()[0]
        nav=f'<nav><a class="brand" href="/">Northstar Hiring</a><a href="/applications">Applications</a><a href="/openings">Openings</a>'+ (f'<a href="/alerts">Alerts <span class="badge">{stalled}</span></a>' if user["role"]=="recruiter" else '') + f'<span class="muted">{user["name"]} · {user["role"]}</span><a href="/logout">Sign out</a></nav>'
    flash=f'<div class="flash">{message}</div>' if message else ''
    return HTMLResponse(f'<!doctype html><html><head><meta charset="utf-8"><title>{title} · Northstar</title>{CSS}</head><body>{nav}<main>{flash}{body}</main></body></html>')
def redirect(path, message=""):
    return RedirectResponse(path + (("?message="+message.replace(" ","+")) if message else ""),303)
def app_for_user(con, app_id, user):
    row=con.execute("SELECT a.*,o.title opening_title FROM applications a JOIN openings o ON o.id=a.opening_id WHERE a.id=?",(app_id,)).fetchone()
    if not row: raise HTTPException(404,"Application not found")
    if user["role"]=="interviewer" and not con.execute("SELECT 1 FROM assignments WHERE application_id=? AND user_id=?",(app_id,user["id"])).fetchone(): raise HTTPException(403,"You are not assigned to this application")
    return row

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request): return page("Sign in",'<div style="max-width:420px;margin:70px auto"><h1>Welcome back</h1><p class="muted">Use a seeded demo account to explore the pipeline.</p><form method="post"><label>Email</label><input name="email" value="recruiter@northstar.test" type="email"><label>Password</label><input name="password" value="demo-password" type="password"><button>Sign in</button></form></div>')
@app.post("/login")
def login(email: str=Form(...), password_value: str=Form(..., alias="password")):
    with db() as con: user=con.execute("SELECT * FROM users WHERE email=? AND password_hash=?",(email.lower(),password(password_value))).fetchone()
    if not user: return page("Sign in",'<div style="max-width:420px;margin:70px auto"><h1>Welcome back</h1><div class="flash error">Invalid email or password.</div><form method="post"><label>Email</label><input name="email" type="email"><label>Password</label><input name="password" type="password"><button>Sign in</button></form></div>')
    r=RedirectResponse("/",303); r.set_cookie("user_id",str(user["id"]),httponly=True,samesite="lax"); return r
@app.get("/logout")
def logout():
    r=RedirectResponse("/login",303);r.delete_cookie("user_id");return r

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request, message: str=""):
    user=require(request)
    with db() as con:
        where,args=visible_clause(user)
        if user["role"]=="recruiter":
            open_count=con.execute("SELECT count(*) FROM openings WHERE status='open'").fetchone()[0]
            active=con.execute("SELECT count(*) FROM applications WHERE stage != 'Rejected'").fetchone()[0]
            scheduled=con.execute("""
                SELECT count(*) FROM applications
                WHERE stage='Interview'
                AND datetime(stage_changed_at) >= datetime('now','weekday 0','-6 days')
                AND datetime(stage_changed_at) < datetime('now','weekday 0','+1 day')
            """).fetchone()[0]
            hires=con.execute("""
                SELECT count(*) FROM applications
                WHERE stage='Hired'
                AND datetime(stage_changed_at) >= datetime('now','start of month')
            """).fetchone()[0]
            by_opening=con.execute("SELECT o.title,count(a.id) total FROM openings o LEFT JOIN applications a ON a.opening_id=o.id WHERE o.status='open' GROUP BY o.id").fetchall()
            by_stage=con.execute("SELECT stage,count(*) total FROM applications GROUP BY stage").fetchall()
            weeks=con.execute("SELECT strftime('%Y-%W',applied_at) week,count(*) total FROM applications WHERE applied_at >= date('now','-3 months') GROUP BY week ORDER BY week").fetchall()
            charts=''.join(f'<tr><td>{x["week"]}</td><td>{x["total"]}</td><td><div style="height:8px;background:#315cc5;width:{min(x["total"]*35,300)}px;border-radius:4px"></div></td></tr>' for x in weeks) or '<tr><td colspan="3">No applications this quarter.</td></tr>'
            body=f'<h1>Pipeline overview</h1><p class="muted">A live view of recruiting work across open positions.</p><div class="grid">{metric("Open positions",open_count)}{metric("Active applications",active)}{metric("Interviews scheduled",scheduled)}{metric("Hires this month",hires)}</div><div class="split"><section class="panel"><h2>Applications by opening</h2>{table_rows(by_opening,"title,total")}</section><section class="panel"><h2>Applications by stage</h2>{table_rows(by_stage,"stage,total")}</section></div><section class="panel" style="margin-top:18px"><h2>Applications received per week · last quarter</h2><table><tr><th>Week</th><th>Applications</th><th>Volume</th></tr>{charts}</table></section>'
        else:
            mine=con.execute("SELECT a.*,o.title opening_title FROM applications a JOIN assignments x ON x.application_id=a.id JOIN openings o ON o.id=a.opening_id WHERE x.user_id=? ORDER BY a.updated_at DESC",(user["id"],)).fetchall()
            body=f'<h1>My interview panel</h1><p class="muted">Only applications you are assigned to appear here.</p>{application_table(mine,user)}'
    return page("Dashboard",body,user,message)
def metric(label,value): return f'<div class="card metric"><span class="muted">{label}</span><b>{value}</b></div>'
def table_rows(rows, keys):
    keys=keys.split(","); return '<table>'+''.join('<tr>'+''.join(f'<td>{r[k]}</td>' for k in keys)+'</tr>' for r in rows)+'</table>'
def application_table(rows,user,selectable=False):
    select='<th></th>' if selectable else ''
    out=f'<table><tr>{select}<th>Candidate</th><th>Opening</th><th>Stage</th><th>Source</th><th>Updated</th></tr>'
    for a in rows:
        check=f'<td><input type="checkbox" name="ids" value="{a["id"]}"></td>' if selectable else ''
        klass=' rejected' if a['stage']=='Rejected' else ''
        out+=f'<tr>{check}<td><a href="/applications/{a["id"]}">{a["candidate_name"]}</a><br><small>{a["email"]}</small></td><td>{a["opening_title"]}</td><td><span class="stage{klass}">{a["stage"]}</span></td><td>{a["source"]}</td><td>{a["updated_at"][:10]}</td></tr>'
    return out+'</table>'

@app.get("/openings", response_class=HTMLResponse)
def openings(request: Request, archived: int=0, message: str=""):
    user=require(request,"recruiter")
    with db() as con: rows=con.execute("SELECT o.*,count(a.id) apps FROM openings o LEFT JOIN applications a ON a.opening_id=o.id WHERE o.status=? GROUP BY o.id ORDER BY o.updated_at DESC",('archived' if archived else 'open',)).fetchall()
    body=f'<div class="actions"><div><h1>Job openings</h1><p class="muted">{ "Archived openings are retained with their applications." if archived else "Open roles and their candidate pipelines."}</p></div><a class="button right" href="/openings/new">New opening</a></div><p><a href="/openings">Open</a> · <a href="/openings?archived=1">Archived</a></p><table><tr><th>Role</th><th>Department</th><th>Applications</th><th></th></tr>'+''.join(f'<tr><td><a href="/openings/{r["id"]}">{r["title"]}</a></td><td>{r["department"]}</td><td>{r["apps"]}</td><td><a href="/openings/{r["id"]}/edit">Edit</a></td></tr>' for r in rows)+'</table>'
    return page("Openings",body,user,message)
@app.get("/openings/new", response_class=HTMLResponse)
def new_opening(request: Request):
    user=require(request,"recruiter"); return page("New opening",opening_form("/openings/new","Create opening"),user)
@app.post("/openings/new")
def create_opening(request: Request,title:str=Form(...),department:str=Form(...),description:str=Form(...)):
    require(request,"recruiter"); t=now()
    with db() as con: con.execute("INSERT INTO openings(title,department,description,status,created_at,updated_at) VALUES(?,?,?,?,?,?)",(title,department,description,'open',t,t))
    return redirect('/openings','Opening created')
def opening_form(action,label,r=None):
    r=r or {"title":"","department":"","description":""}
    return f'<h1>{label}</h1><form method="post" action="{action}" style="max-width:650px"><label>Title</label><input name="title" value="{r["title"]}" required><label>Department</label><input name="department" value="{r["department"]}" required><label>Description</label><textarea name="description" rows="5" required>{r["description"]}</textarea><button>{label}</button></form>'
@app.get("/openings/{opening_id}", response_class=HTMLResponse)
def opening_detail(request:Request,opening_id:int,message:str=""):
    user=require(request,"recruiter")
    with db() as con:
        o=con.execute("SELECT * FROM openings WHERE id=?",(opening_id,)).fetchone()
        if not o: raise HTTPException(404,"Opening not found")
        rows=con.execute("SELECT a.*,o.title opening_title FROM applications a JOIN openings o ON o.id=a.opening_id WHERE a.opening_id=? ORDER BY a.updated_at DESC",(opening_id,)).fetchall()
    state='Restore' if o['status']=='archived' else 'Archive'
    return page(o['title'],f'<div class="actions"><div><h1>{o["title"]}</h1><p class="muted">{o["department"]} · {o["description"]}</p></div><a class="button right" href="/applications/new?opening_id={opening_id}">Add application</a><a class="button secondary" href="/openings/{opening_id}/edit">Edit</a><form method="post" action="/openings/{opening_id}/toggle"><button class="secondary">{state}</button></form></div>{application_table(rows,user)}',user,message)
@app.get("/openings/{opening_id}/edit",response_class=HTMLResponse)
def edit_opening_page(request:Request,opening_id:int):
    user=require(request,"recruiter")
    with db() as con:r=con.execute("SELECT * FROM openings WHERE id=?",(opening_id,)).fetchone()
    if not r: raise HTTPException(404,"Opening not found")
    return page("Edit opening",opening_form(f'/openings/{opening_id}/edit','Save opening',r),user)
@app.post("/openings/{opening_id}/edit")
def edit_opening(request:Request,opening_id:int,title:str=Form(...),department:str=Form(...),description:str=Form(...)):
    require(request,"recruiter")
    with db() as con: con.execute("UPDATE openings SET title=?,department=?,description=?,updated_at=? WHERE id=?",(title,department,description,now(),opening_id))
    return redirect(f'/openings/{opening_id}','Opening saved')
@app.post("/openings/{opening_id}/toggle")
def toggle_opening(request:Request,opening_id:int):
    require(request,"recruiter")
    with db() as con:
        o=con.execute("SELECT status FROM openings WHERE id=?",(opening_id,)).fetchone()
        if not o:raise HTTPException(404,"Opening not found")
        status='archived' if o['status']=='open' else 'open';con.execute("UPDATE openings SET status=?,updated_at=? WHERE id=?",(status,now(),opening_id))
    return redirect('/openings','Opening '+status)

@app.get("/applications",response_class=HTMLResponse)
def applications(request:Request,q:str="",opening_id:str="",stage:str="",source:str="",sort:str="updated",page_num:int=1,message:str=""):
    user=require(request); page_num=max(1,page_num); order={"applied":"a.applied_at DESC","stage":"a.stage","updated":"a.updated_at DESC"}.get(sort,"a.updated_at DESC")
    with db() as con:
        joins,params=visible_clause(user); conditions=[]
        if q: conditions.append("(lower(a.candidate_name) LIKE ? OR lower(a.email) LIKE ?)");params.extend([f'%{q.lower()}%',f'%{q.lower()}%'])
        if opening_id:conditions.append("a.opening_id=?");params.append(opening_id)
        if stage:conditions.append("a.stage=?");params.append(stage)
        if source:conditions.append("a.source=?");params.append(source)
        where=(" AND " if " WHERE " in joins else " WHERE ")+" AND ".join(conditions) if conditions else ""
        base="FROM applications a JOIN openings o ON o.id=a.opening_id"+joins+where
        total=con.execute("SELECT count(*) "+base,params).fetchone()[0]
        rows=con.execute("SELECT a.*,o.title opening_title "+base+f" ORDER BY {order} LIMIT 20 OFFSET ?",params+[20*(page_num-1)]).fetchall()
        openings_list=con.execute("SELECT id,title FROM openings WHERE status='open' ORDER BY title").fetchall()
    opts=lambda rs,sel,label: '<option value="">'+label+'</option>'+''.join(f'<option value="{x[0]}" {"selected" if str(x[0])==sel else ""}>{x[1]}</option>' for x in rs)
    filters=f'<form method="get" class="filters"><input name="q" value="{q}" placeholder="Search name or email"><select name="opening_id">{opts([(o["id"],o["title"]) for o in openings_list],opening_id,"All openings")}</select><select name="stage">{opts([(s,s) for s in STAGES+["Rejected"]],stage,"All stages")}</select><select name="source">{opts([(s,s) for s in SOURCE_OPTIONS],source,"All sources")}</select><select name="sort">{opts([("updated","Last updated"),("applied","Applied date"),("stage","Stage")],sort,"Sort")}</select><button>Filter</button></form>'
    title='Applications' if user['role']=='recruiter' else 'My assigned applications'
    bulk='<div class="actions" style="margin:12px 0"><button formaction="/applications/bulk" formmethod="post" name="action" value="advance">Advance selected</button><button class="danger" formaction="/applications/bulk" formmethod="post" name="action" value="reject">Reject selected</button><a class="button secondary" href="/applications/export">Export open pipeline CSV</a></div>' if user['role']=='recruiter' else ''
    start='<form id="listform" method="post">' if user['role']=='recruiter' else ''
    end='</form>' if user['role']=='recruiter' else ''
    pages=f'<p class="muted">{total} match{ "es" if total!=1 else ""} · page {page_num}'+(f' · <a href="/applications?{request.url.query}&page_num={page_num+1}">Next page</a>' if total>page_num*20 else '')+'</p>'
    add='<a class="button right" href="/applications/new">Add application</a>' if user['role']=='recruiter' else ''
    return page(title,f'<div class="actions"><div><h1>{title}</h1><p class="muted">Search, filter and sort are performed on the server.</p></div>{add}</div>{filters}{start}{bulk}{application_table(rows,user,user["role"]=="recruiter")}{end}{pages}',user,message)

@app.get("/applications/new",response_class=HTMLResponse)
def new_application(request:Request,opening_id:int=0):
    user=require(request,"recruiter")
    with db() as con:opens=con.execute("SELECT id,title FROM openings WHERE status='open'").fetchall()
    return page('New application',application_form('/applications/new','Create application',opens,opening_id),user)
def application_form(action,label,openings,selected=0,a=None):
    a=a or {"candidate_name":"","email":"","source":"Careers page","notes":""}
    choices=''.join(f'<option value="{o["id"]}" {"selected" if o["id"]==selected else ""}>{o["title"]}</option>' for o in openings)
    sources=''.join(f'<option {"selected" if s==a["source"] else ""}>{s}</option>' for s in SOURCE_OPTIONS)
    return f'<h1>{label}</h1><form method="post" action="{action}" style="max-width:650px"><label>Job opening</label><select name="opening_id">{choices}</select><label>Candidate name</label><input name="candidate_name" value="{a["candidate_name"]}" required><label>Email</label><input type="email" name="email" value="{a["email"]}" required><label>Source</label><select name="source">{sources}</select><label>Notes</label><textarea name="notes" rows="4">{a["notes"]}</textarea><button>{label}</button></form>'
@app.post("/applications/new")
def create_application(request:Request,opening_id:int=Form(...),candidate_name:str=Form(...),email:str=Form(...),source:str=Form(...),notes:str=Form("")):
    user=require(request,"recruiter"); t=now()
    with db() as con:
        if not con.execute("SELECT 1 FROM openings WHERE id=? AND status='open'",(opening_id,)).fetchone():raise HTTPException(400,"Choose an open job opening")
        cur=con.execute("INSERT INTO applications(opening_id,candidate_name,email,source,notes,stage,applied_at,stage_changed_at,updated_at) VALUES(?,?,?,?,?,'Applied',?,?,?)",(opening_id,candidate_name,email.lower(),source,notes,t,t,t));event(con,cur.lastrowid,user['id'],'created','Application created')
    return redirect(f'/openings/{opening_id}','Application created')
@app.get("/applications/{app_id}",response_class=HTMLResponse)
def application_detail(request:Request,app_id:int,message:str=""):
    user=require(request)
    with db() as con:
        a=app_for_user(con,app_id,user)
        events=con.execute("SELECT e.*,u.name actor FROM events e LEFT JOIN users u ON u.id=e.actor_id WHERE e.application_id=? ORDER BY e.created_at DESC",(app_id,)).fetchall()
        interviewers=con.execute("SELECT u.* FROM users u JOIN assignments x ON x.user_id=u.id WHERE x.application_id=?",(app_id,)).fetchall()
        candidates=con.execute("SELECT * FROM users WHERE role='interviewer' ORDER BY name").fetchall()
    actions=''
    if user['role']=='recruiter':
        move='<form method="post" action="/applications/%s/advance"><button>Advance to next stage</button></form>'%app_id if a['stage'] in ACTIVE_STAGES and a['stage']!='Hired' else ''
        reinstate='<form method="post" action="/applications/%s/reinstate"><button>Reinstate to %s</button></form>'%(app_id,a['rejected_from']) if a['stage']=='Rejected' else ''
        reject='<form method="post" action="/applications/%s/reject"><button class="danger">Reject</button></form>'%app_id if a['stage']!='Rejected' else ''
        assigned=', '.join(x['name'] for x in interviewers) or 'No interviewers assigned'
        options=''.join(f'<option value="{x["id"]}">{x["name"]}</option>' for x in candidates if x['id'] not in [z['id'] for z in interviewers])
        actions=f'<div class="actions">{move}{reject}{reinstate}<a class="button secondary" href="/applications/{app_id}/edit">Edit</a></div><section class="panel" style="margin-top:16px"><h2>Interview panel</h2><p>{assigned}</p><form method="post" action="/applications/{app_id}/assign" class="row"><select name="user_id">{options}</select><button>Assign interviewer</button></form></section>'
    feedback='<section class="panel" style="margin-top:16px"><h2>Leave immutable feedback</h2><form method="post" action="/applications/%s/feedback"><textarea name="feedback" rows="3" placeholder="Interview feedback" required></textarea><button>Save feedback</button></form></section>'%app_id if user['role']=='interviewer' else ''
    timeline=''.join(f'<div class="event"><b>{e["kind"].title()}</b> — {e["detail"]}<small>{e["actor"] or "System"} · {e["created_at"][:16].replace("T"," ")}</small></div>' for e in events)
    klass=' rejected' if a['stage']=='Rejected' else ''
    body=f'<p><a href="/applications">← Back to applications</a></p><h1>{a["candidate_name"]} <span class="stage{klass}">{a["stage"]}</span></h1><p class="muted">{a["email"]} · {a["opening_title"]} · {a["source"]}</p><div class="split"><section><div class="panel"><h2>Notes</h2><p>{a["notes"] or "No notes."}</p>{actions}</div>{feedback}</section><section class="panel"><h2>Uneditable timeline</h2><div class="timeline">{timeline}</div></section></div>'
    return page(a['candidate_name'],body,user,message)
@app.get("/applications/{app_id}/edit",response_class=HTMLResponse)
def edit_application_page(request:Request,app_id:int):
    user=require(request,"recruiter")
    with db() as con:
        a=app_for_user(con,app_id,user);opens=con.execute("SELECT id,title FROM openings ORDER BY title").fetchall()
    return page('Edit application',application_form(f'/applications/{app_id}/edit','Save application',opens,a['opening_id'],a),user)
@app.post("/applications/{app_id}/edit")
def edit_application(request:Request,app_id:int,opening_id:int=Form(...),candidate_name:str=Form(...),email:str=Form(...),source:str=Form(...),notes:str=Form("")):
    user=require(request,"recruiter")
    with db() as con:
        app_for_user(con,app_id,user);con.execute("UPDATE applications SET opening_id=?,candidate_name=?,email=?,source=?,notes=?,updated_at=? WHERE id=?",(opening_id,candidate_name,email.lower(),source,notes,now(),app_id));event(con,app_id,user['id'],'edited','Application details updated')
    return redirect(f'/applications/{app_id}','Application saved')

def advance(con,a,user):
    if a['stage']=='Rejected': return False,'Rejected applications must be reinstated before advancing.'
    if a['stage']=='Hired': return False,'Hired is the final stage.'
    if a['stage'] not in STAGES: return False,'This application cannot advance.'
    next_stage=STAGES[STAGES.index(a['stage'])+1]
    con.execute("UPDATE applications SET stage=?,stage_changed_at=?,updated_at=? WHERE id=?",(next_stage,now(),now(),a['id']))
    con.execute("DELETE FROM alert_dismissals WHERE application_id=?",(a['id'],))
    event(con,a['id'],user['id'],'stage',f"{a['stage']} → {next_stage}")
    return True,f'Moved to {next_stage}.'
@app.post("/applications/{app_id}/advance")
def advance_one(request:Request,app_id:int):
    user=require(request,'recruiter')
    with db() as con:
        a=app_for_user(con,app_id,user); ok,msg=advance(con,a,user)
    return redirect(f'/applications/{app_id}',msg)
@app.post("/applications/{app_id}/reject")
def reject_one(request:Request,app_id:int):
    user=require(request,'recruiter')
    with db() as con:
        a=app_for_user(con,app_id,user)
        if a['stage']=='Rejected': return redirect(f'/applications/{app_id}','Application is already rejected.')
        con.execute("UPDATE applications SET rejected_from=stage,stage='Rejected',stage_changed_at=?,updated_at=? WHERE id=?",(now(),now(),app_id));event(con,app_id,user['id'],'rejected',f"Rejected from {a['stage']}")
    return redirect(f'/applications/{app_id}','Application rejected')
@app.post("/applications/{app_id}/reinstate")
def reinstate(request:Request,app_id:int):
    user=require(request,'recruiter')
    with db() as con:
        a=app_for_user(con,app_id,user)
        if a['stage']!='Rejected' or not a['rejected_from']: return redirect(f'/applications/{app_id}','Only rejected applications can be reinstated.')
        con.execute("UPDATE applications SET stage=?,rejected_from=NULL,stage_changed_at=?,updated_at=? WHERE id=?",(a['rejected_from'],now(),now(),app_id));event(con,app_id,user['id'],'reinstated',f"Reinstated to {a['rejected_from']}")
    return redirect(f'/applications/{app_id}','Application reinstated')
@app.post("/applications/{app_id}/assign")
def assign(request:Request,app_id:int,user_id:int=Form(...)):
    user=require(request,'recruiter')
    with db() as con:
        app_for_user(con,app_id,user); interviewer=con.execute("SELECT * FROM users WHERE id=? AND role='interviewer'",(user_id,)).fetchone()
        if not interviewer: raise HTTPException(400,'Only interviewer-role users can be assigned.')
        con.execute("INSERT OR IGNORE INTO assignments(application_id,user_id) VALUES(?,?)",(app_id,user_id));event(con,app_id,user['id'],'assignment',f"Assigned interviewer {interviewer['name']}")
    return redirect(f'/applications/{app_id}','Interviewer assigned')
@app.post("/applications/{app_id}/feedback")
def feedback(request:Request,app_id:int,feedback:str=Form(...)):
    user=require(request,'interviewer')
    with db() as con:
        app_for_user(con,app_id,user); event(con,app_id,user['id'],'feedback',feedback.strip())
    return redirect(f'/applications/{app_id}','Feedback added to the immutable timeline')
@app.post("/applications/bulk",response_class=HTMLResponse)
async def bulk(request:Request):
    user=require(request,'recruiter'); form=await request.form(); ids=[int(x) for x in form.getlist('ids')]; action=form.get('action')
    if not ids:return redirect('/applications','Select at least one application.')
    outcomes=[]
    with db() as con:
        for app_id in ids:
            a=app_for_user(con,app_id,user)
            if action=='advance':ok,msg=advance(con,a,user)
            elif action=='reject':
                if a['stage']=='Rejected':ok,msg=False,'Already rejected.'
                else:
                    con.execute("UPDATE applications SET rejected_from=stage,stage='Rejected',stage_changed_at=?,updated_at=? WHERE id=?",(now(),now(),app_id));event(con,app_id,user['id'],'rejected',f"Rejected from {a['stage']}");ok,msg=True,'Rejected.'
            else:ok,msg=False,'Unknown bulk action.'
            outcomes.append((a['candidate_name'],ok,msg))
    rows=''.join(f'<tr><td>{name}</td><td>{"Succeeded" if ok else "Refused"}</td><td>{msg}</td></tr>' for name,ok,msg in outcomes)
    return page('Bulk action results',f'<h1>Bulk action results</h1><p class="muted">Each application was evaluated independently; no ineligible candidate blocked the rest.</p><table><tr><th>Candidate</th><th>Outcome</th><th>Detail</th></tr>{rows}</table><p><a class="button" href="/applications">Back to applications</a></p>',user)
@app.get("/applications/export")
def export(request:Request):
    require(request,'recruiter')
    with db() as con: rows=con.execute("SELECT a.candidate_name,a.email,o.title opening,a.stage,a.source,a.applied_at FROM applications a JOIN openings o ON o.id=a.opening_id WHERE o.status='open' ORDER BY o.title,a.candidate_name").fetchall()
    out=io.StringIO();w=csv.writer(out);w.writerow(['candidate_name','email','opening','stage','source','applied_at']);w.writerows([tuple(r) for r in rows])
    return Response(out.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename=pipeline-snapshot.csv'})
@app.get('/alerts',response_class=HTMLResponse)
def alerts(request:Request,message:str=''):
    user=require(request,'recruiter')
    with db() as con: rows=con.execute("SELECT a.*,o.title opening_title FROM applications a JOIN openings o ON o.id=a.opening_id LEFT JOIN alert_dismissals d ON d.application_id=a.id AND d.stage=a.stage WHERE a.stage!='Rejected' AND datetime(a.stage_changed_at)<datetime('now','-10 days') AND d.application_id IS NULL ORDER BY a.stage_changed_at").fetchall()
    items=''.join(f'<div class="alert"><b><a href="/applications/{a["id"]}">{a["candidate_name"]}</a></b> has been in <span class="stage">{a["stage"]}</span> since {a["stage_changed_at"][:10]} · {a["opening_title"]}<form method="post" action="/alerts/{a["id"]}/dismiss" style="margin-top:8px"><button class="secondary">Dismiss this alert</button></form></div>' for a in rows) or '<div class="panel">No stalled applications right now.</div>'
    return page('Stalled alerts',f'<h1>Stalled applications</h1><p class="muted">An alert returns when a candidate advances and then remains at their new stage for another ten days.</p>{items}',user,message)
@app.post('/alerts/{app_id}/dismiss')
def dismiss_alert(request:Request,app_id:int):
    user=require(request,'recruiter')
    with db() as con:
        a=app_for_user(con,app_id,user);con.execute("INSERT OR REPLACE INTO alert_dismissals(application_id,stage,dismissed_by) VALUES(?,?,?)",(app_id,a['stage'],user['id']))
    return redirect('/alerts','Alert dismissed for this stage')
