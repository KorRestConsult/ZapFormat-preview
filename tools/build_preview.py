#!/usr/bin/env python3
"""Publish a frontend-only, API-isolated snapshot of ZapFormat/design-preview."""
import json
import re
import shutil
import subprocess
from pathlib import Path

source = Path("source")
public = Path("public")
if public.exists():
    shutil.rmtree(public)
public.mkdir()
for filename in ("index.html", "styles.css", "premium.css", "app.js", "config.js", "admin-desk.js"):
    path = source / filename
    if not path.is_file():
        raise RuntimeError(f"Required frontend file missing: {filename}")
    shutil.copy2(path, public / filename)
for directory in ("admin", "assets", "images", "img", "fonts", "icons"):
    path = source / directory
    if path.is_dir():
        shutil.copytree(path, public / directory)

# Never connect preview to live ZapFormat API, database, or PartGrade.
(public / "config.js").write_text(
    'window.ZAPFORMAT_CONFIG={apiBase:location.origin+"/__preview_api_disabled"};\n',
    encoding="utf-8",
)
sha = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
infra_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
version = sha[:12] + "-" + infra_sha[:12]
(public / "preview-version.json").write_text(
    json.dumps({"source_branch": "design-preview", "sha": version, "source_sha": sha}, ensure_ascii=False),
    encoding="utf-8",
)
(public / ".nojekyll").touch()

def patch_html(path: Path, root: bool = False):
    content = path.read_text(encoding="utf-8")
    # Pin CSS and JS to this build so iPad Safari does not reuse stale assets.
    content = re.sub(
        r'(?P<asset>(?:\.\.?/)[^\s"\']+\.(?:css|js))\?v=',
        lambda m: m.group("asset") + "?preview_build=" + version + "&v=",
        content,
    )
    if "</head>" not in content:
        raise RuntimeError(f"Cannot insert preview safety headers in {path}")
    safety = (
        '<meta name="robots" content="noindex,nofollow,noarchive">'
        '<meta http-equiv="Content-Security-Policy" '
        'content="connect-src &#39;self&#39;; form-action &#39;self&#39;">'
    )
    content = content.replace("</head>", safety + "</head>", 1)
    label = (
        '<div id="zf-preview-label" aria-label="Тестовая версия">'
        'ТЕСТОВАЯ ВЕРСИЯ · ЗАКАЗЫ ОТКЛЮЧЕНЫ</div>'
        '<style>#zf-preview-label{position:fixed;z-index:2147483000;'
        'bottom:calc(env(safe-area-inset-bottom,0px) + 8px);'
        'right:10px;background:#172535f0;color:#fff;font:600 10px/1.4 '
        'system-ui,sans-serif;letter-spacing:.05em;padding:6px 11px;'
        'border-radius:100px;pointer-events:none;box-shadow:0 4px 12px #0003}'
        '</style>'
    )
    content = content.replace("</body>", label + "</body>", 1)
    if root:
        poll = (
            '<script>(function(){const current='+json.dumps(version)+';'
            'let busy=false;async function check(){if(busy)return;busy=true;try{'
            'const r=await fetch("./preview-version.json?t="+Date.now(),{cache:"no-store"});'
            'if(!r.ok)return;const j=await r.json();'
            'if(j.sha&&j.sha!==current){const u=new URL(location.href);'
            'u.searchParams.set("preview_build",j.sha);location.replace(u.href);}'
            '}catch(e){}finally{busy=false;}}'
            'setInterval(check,4000);window.addEventListener("focus",check);'
            'document.addEventListener("visibilitychange",function(){if(!document.hidden)check();});'
            '})();</script>'
        )
        content = content.replace("</body>", poll + "</body>", 1)
    path.write_text(content, encoding="utf-8")

patch_html(public / "index.html", root=True)
admin_html = public / "admin" / "index.html"
if admin_html.exists():
    patch_html(admin_html)
admin_js = public / "admin" / "admin.js"
if admin_js.exists():
    text = admin_js.read_text(encoding="utf-8")
    text = text.replace('https://zapformat.ru/', '../')
    admin_js.write_text(text, encoding="utf-8")
print("Preview built from", sha, "with production connections blocked.")
