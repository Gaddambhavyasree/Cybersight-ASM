import re
from bson import ObjectId
from fastapi import APIRouter,Depends,HTTPException,Query
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.vulnerability import VulnerabilityListResponse,VulnerabilityResponse,VulnerabilityStatsResponse
router=APIRouter(prefix='/api/vulnerabilities',tags=['Vulnerabilities'])
async def ids(db,u):
 role = str(getattr(u.get('role'), 'value', u.get('role')) or '').lower()
 if role == 'admin': q = {}
 else:
  owner = str(u['_id']); q = {'$or': [{'created_by': owner}]}
  if ObjectId.is_valid(owner): q['$or'].append({'created_by': ObjectId(owner)})
 return [str(x['_id']) async for x in db.projects.find(q,{'_id':1})]
async def dec(db,ds):
 ps=await db.projects.find({'_id':{'$in':[ObjectId(x) for x in {d.get('project_id') for d in ds} if isinstance(x,str) and ObjectId.is_valid(x)]}},{'name':1}).to_list(None);ss=await db.scans.find({'_id':{'$in':[ObjectId(x) for x in {d.get('scan_id') for d in ds} if isinstance(x,str) and ObjectId.is_valid(x)]}},{'scan_name':1}).to_list(None);pn={str(x['_id']):x.get('name') for x in ps};sn={str(x['_id']):x.get('scan_name') for x in ss}
 for d in ds:d['id']=str(d.pop('_id'));d['project_name']=pn.get(d.get('project_id'));d['scan_name']=sn.get(d.get('scan_id'),d.get('scan_id'))
 return ds
@router.get('',response_model=VulnerabilityListResponse)
async def listing(page:int=Query(1,ge=1),per_page:int=Query(50,ge=1,le=200),severity:str|None=None,hostname:str|None=None,cve:str|None=None,template:str|None=None,status:str|None=None,project_id:str|None=None,scan_id:str|None=None,search:str|None=None,sort:str='last_seen',current_user:dict=Depends(get_current_user),db=Depends(get_database)):
 ps=await ids(db,current_user);q={'project_id':project_id if project_id in ps else {'$in':[]}} if project_id else {'project_id':{'$in':ps}}
 for k,v in [('hostname',hostname),('cve',cve),('template_name',template)]:
  if v:q[k]={'$regex':re.escape(v),'$options':'i'}
 if severity:q['severity']=severity.lower()
 if status:q['status']=status
 if scan_id:q['scan_id']=scan_id
 if search:q['$or']=[{k:{'$regex':re.escape(search),'$options':'i'}} for k in ('hostname','url','template_id','template_name','cve','description')]
 total=await db.vulnerabilities.count_documents(q);field=sort if sort in ('last_seen','first_seen','severity','hostname','cvss') else 'last_seen';ds=await db.vulnerabilities.find(q).sort(field,-1).skip((page-1)*per_page).limit(per_page).to_list(per_page);return VulnerabilityListResponse(records=await dec(db,ds),total=total,page=page,per_page=per_page)
@router.get('/stats',response_model=VulnerabilityStatsResponse)
async def stats(current_user:dict=Depends(get_current_user),db=Depends(get_database)):
 q={'project_id':{'$in':await ids(db,current_user)}};groups=await db.vulnerabilities.aggregate([{'$match':q},{'$group':{'_id':'$severity','count':{'$sum':1}}}]).to_list(None);ta=await db.vulnerabilities.aggregate([{'$match':q},{'$group':{'_id':'$hostname','count':{'$sum':1}}},{'$sort':{'count':-1}},{'$limit':10}]).to_list(None);tc=await db.vulnerabilities.aggregate([{'$match':q},{'$match':{'cve':{'$ne':None}}},{'$group':{'_id':'$cve','count':{'$sum':1}}},{'$sort':{'count':-1}},{'$limit':10}]).to_list(None);tt=await db.vulnerabilities.aggregate([{'$match':q},{'$group':{'_id':'$template_name','count':{'$sum':1}}},{'$sort':{'count':-1}},{'$limit':10}]).to_list(None);latest=await db.vulnerabilities.find_one(q,sort=[('last_seen',-1)]);vals={x['_id']:x['count'] for x in groups};return VulnerabilityStatsResponse(**{s:vals.get(s,0) for s in ('critical','high','medium','low','info')},total_findings=sum(vals.values()),affected_assets=len(await db.vulnerabilities.distinct('asset_id',q)),last_scan=latest.get('last_seen') if latest else None,severity_distribution=[{'label':x['_id'],'count':x['count']} for x in groups],top_assets=[{'label':x['_id'],'count':x['count']} for x in ta],top_cves=[{'label':x['_id'],'count':x['count']} for x in tc],top_templates=[{'label':x['_id'],'count':x['count']} for x in tt])
@router.get('/{finding_id}',response_model=VulnerabilityResponse)
async def detail(finding_id:str,current_user:dict=Depends(get_current_user),db=Depends(get_database)):
 if not ObjectId.is_valid(finding_id):raise HTTPException(404,'Vulnerability not found')
 d=await db.vulnerabilities.find_one({'_id':ObjectId(finding_id),'project_id':{'$in':await ids(db,current_user)}})
 if not d:raise HTTPException(404,'Vulnerability not found')
 return VulnerabilityResponse(**(await dec(db,[d]))[0])
