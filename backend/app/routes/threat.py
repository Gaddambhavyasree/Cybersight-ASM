import re
from bson import ObjectId
from fastapi import APIRouter,Depends,HTTPException,Query
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.threat import ThreatListResponse,ThreatResponse,ThreatStatsResponse
router=APIRouter(prefix='/api/threat-intelligence',tags=['Threat Intelligence'])
async def ids(db,u):
 role=str(getattr(u.get('role'),'value',u.get('role')) or '').lower();q={} if role=='admin' else {'created_by':str(u['_id'])};return [str(x['_id']) async for x in db.projects.find(q,{'_id':1})]
async def dec(db,ds):
 ps=await db.projects.find({'_id':{'$in':[ObjectId(x) for x in {d.get('project_id') for d in ds} if isinstance(x,str) and ObjectId.is_valid(x)]}},{'name':1}).to_list(None);ss=await db.scans.find({'_id':{'$in':[ObjectId(x) for x in {d.get('scan_id') for d in ds} if isinstance(x,str) and ObjectId.is_valid(x)]}},{'scan_name':1}).to_list(None);pn={str(x['_id']):x.get('name') for x in ps};sn={str(x['_id']):x.get('scan_name') for x in ss}
 for d in ds:d['id']=str(d.pop('_id'));d['project_name']=pn.get(d.get('project_id'));d['scan_name']=sn.get(d.get('scan_id'),d.get('scan_id'))
 return ds
@router.get('',response_model=ThreatListResponse)
async def listing(page:int=Query(1,ge=1),per_page:int=Query(50,ge=1,le=200),search:str|None=None,cve:str|None=None,severity:str|None=None,project_id:str|None=None,scan_id:str|None=None,current_user:dict=Depends(get_current_user),db=Depends(get_database)):
 ps=await ids(db,current_user);q={'project_id':project_id if project_id in ps else {'$in':[]}} if project_id else {'project_id':{'$in':ps}}
 if cve:q['cve']={'$regex':re.escape(cve),'$options':'i'}
 if severity:q['severity']=severity.lower()
 if scan_id:q['scan_id']=scan_id
 if search:q['$or']=[{k:{'$regex':re.escape(search),'$options':'i'}} for k in ('hostname','ip','cve','description','kev_vendor','kev_product')]
 total=await db.threat_intelligence.count_documents(q);ds=await db.threat_intelligence.find(q).sort('updated_at',-1).skip((page-1)*per_page).limit(per_page).to_list(per_page);return ThreatListResponse(records=await dec(db,ds),total=total,page=page,per_page=per_page)
@router.get('/stats',response_model=ThreatStatsResponse)
async def stats(current_user:dict=Depends(get_current_user),db=Depends(get_database)):
 q={'project_id':{'$in':await ids(db,current_user)}};latest=await db.threat_intelligence.find_one(q,sort=[('updated_at',-1)]);sev=await db.threat_intelligence.aggregate([{'$match':q},{'$group':{'_id':'$severity','count':{'$sum':1}}}]).to_list(None);vendors=await db.threat_intelligence.aggregate([{'$match':q},{'$group':{'_id':'$kev_vendor','count':{'$sum':1}}},{'$sort':{'count':-1}},{'$limit':10}]).to_list(None);return ThreatStatsResponse(total_cves=len(await db.threat_intelligence.distinct('cve',q)),known_exploited=await db.threat_intelligence.count_documents({**q,'kev':True}),critical_cves=await db.threat_intelligence.count_documents({**q,'severity':'critical'}),assets_enriched=len(await db.threat_intelligence.distinct('asset_id',q)),last_sync=latest.get('updated_at') if latest else None,severity_distribution=[{'label':x['_id'],'count':x['count']} for x in sev],top_vendors=[{'label':x['_id'],'count':x['count']} for x in vendors])
@router.get('/{record_id}',response_model=ThreatResponse)
async def detail(record_id:str,current_user:dict=Depends(get_current_user),db=Depends(get_database)):
 if not ObjectId.is_valid(record_id):raise HTTPException(404,'Threat intelligence not found')
 d=await db.threat_intelligence.find_one({'_id':ObjectId(record_id),'project_id':{'$in':await ids(db,current_user)}})
 if not d:raise HTTPException(404,'Threat intelligence not found')
 return ThreatResponse(**(await dec(db,[d]))[0])
