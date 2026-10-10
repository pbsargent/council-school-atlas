"""Resolve canonical unit pages with exact legacy ID verification and bounded retries."""
import concurrent.futures,datetime,html,re,subprocess,tempfile,time
from pathlib import Path
from atlas_refresh import ROOT,OUTPUT,atomic_json,read_json
CANONICAL=re.compile(r'^https://beascout\.scouting\.org/units/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',re.I)
def verify_page(body,url,id,name):
 if not CANONICAL.fullmatch(url):return 'Resolver did not reach a canonical unit page'
 # Exact authoritative numeric ID in the rendered unit payload is stronger than name-only matching.
 identities=set(re.findall(r'legacyUnitId\s*:\s*(\d+)',body))
 if identities!={str(int(id))}:return 'Returned page does not identify the exact source unit ID'
 title=re.search(r'<title>(.*?)</title>',body,re.S)
 if not title:return 'Unit title missing'
 title=html.unescape(title.group(1));expected=re.match(r'(Pack|Troop|Crew|Post|Ship)\s*0*(\d+)',name,re.I)
 actual=re.match(r'(Pack|Troop|Crew|Post|Ship)\s*0*(\d+)',title,re.I)
 if expected and actual and (expected.group(1).lower(),int(expected.group(2)))!=(actual.group(1).lower(),int(actual.group(2))):return 'Unit program or number contradicts source identity'
 return None
def resolve(unit):
 id=unit['id'];zip=unit.get('zipCode')
 if not zip or not re.fullmatch(r'\d{5}',zip):return id,None,'ZIP5 unavailable'
 url=f'https://beascout.scouting.org/list/?zip={zip}&unitID={id}'
 try:
  with tempfile.NamedTemporaryFile(suffix='.html') as f:
   result=subprocess.run(['curl','--silent','--show-error','--location','--proto','=https','--proto-redir','=https','--max-time','30','--output',f.name,'--write-out','%{url_effective}\n%{http_code}',url],capture_output=True,text=True,timeout=35)
   if result.returncode:return id,None,'Resolver request failed or timed out'
   final,status=result.stdout.rsplit('\n',1)
   if status!='200':return id,None,'Resolver HTTP '+status
   body=Path(f.name).read_text(encoding='utf-8',errors='replace');error=verify_page(body,final,id,unit['name'])
   return id,final if not error else None,error
 except (OSError,ValueError,subprocess.TimeoutExpired):return id,None,'Resolver request failed or timed out'
def main():
 path=OUTPUT/'public/data/unit-pins.json';payload=read_json(path);units=payload['units'];results={};pending=units
 for attempt,workers in enumerate([3,2],1):
  with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
   for index,(id,url,reason) in enumerate(pool.map(resolve,pending),1):
    results[id]={'url':url,'reason':reason,'attempt':attempt}
    if index%25==0:print(f'Pass {attempt}: {index}/{len(pending)} units checked',flush=True)
  pending=[u for u in units if results[u['id']]['url'] is None]
  print(f'Pass {attempt}: {len(units)-len(pending)} verified, {len(pending)} unresolved',flush=True)
  if not pending:break
 # A canonical page cannot silently be attached to two different authoritative IDs.
 destinations={}
 for id,r in results.items():
  if r['url']:destinations.setdefault(r['url'],[]).append(id)
 for ids in destinations.values():
  if len(ids)>1:
   for id in ids:results[id].update(url=None,reason='Canonical page shared by distinct source IDs')
 stamp=datetime.datetime.now(datetime.timezone.utc).isoformat();audit=[]
 for u in units:
  r=results[u['id']];old=u.get('beascoutUrl');new=r['url']
  if new:u['beascoutUrl']=new;u['beascoutVerifiedAt']=stamp
  elif old and CANONICAL.fullmatch(old):pass # Preserve existing destination on verification failure.
  else:u['beascoutUrl']=None;u['beascoutVerifiedAt']=None
  audit.append({'id':u['id'],'name':u['name'],'previousUrl':old,'newUrl':u.get('beascoutUrl'),'outcome':'verified' if new else 'retained' if u.get('beascoutUrl') else 'unresolved','reason':r['reason']})
 payload['beascoutCheckedAt']=stamp;payload['beascoutSummary']={'verified':sum(r['outcome']=='verified' for r in audit),'retained':sum(r['outcome']=='retained' for r in audit),'unresolved':sum(r['outcome']=='unresolved' for r in audit)}
 atomic_json(path,payload)
 reread=read_json(path)
 if [(u['id'],u.get('beascoutUrl')) for u in reread['units']]!=[(u['id'],u.get('beascoutUrl')) for u in units]:raise ValueError('Written links failed readback')
 atomic_json(ROOT/'.atlas-refresh/beascout-link-audit.json',{'checkedAt':stamp,'records':audit})
 print(payload['beascoutSummary'],flush=True)
if __name__=='__main__':main()
