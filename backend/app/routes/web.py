import re
from bson import ObjectId
from fastapi import APIRouter, Depends, Query, HTTPException
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.web import WebAssetListResponse, WebAssetResponse, WebStatsResponse
router = APIRouter(prefix="/api/web-assets", tags=["Web Crawling"])
async def _ids(db, user):
 q = {} if user["role"] == "admin" else {"created_by": str(user["_id"])}; return [str(x["_id"]) async for x in db.projects.find(q, {"_id": 1})]
async def _dec(db, docs):
 ps = await db.projects.find({"_id": {"$in": [ObjectId(x) for x in {d.get('project_id') for d in docs} if isinstance(x, str) and ObjectId.is_valid(x)]}}, {"name": 1}).to_list(None); ss = await db.scans.find({"_id": {"$in": [ObjectId(x) for x in {d.get('scan_id') for d in docs} if isinstance(x, str) and ObjectId.is_valid(x)]}}, {"scan_name": 1}).to_list(None); pn = {str(x['_id']): x.get('name') for x in ps}; sn = {str(x['_id']): x.get('scan_name') for x in ss}
 for d in docs: d['id'] = str(d.pop('_id')); d['project_name'] = pn.get(d.get('project_id')); d['scan_name'] = sn.get(d.get('scan_id'), d.get('scan_id'))
 return docs
@router.get('', response_model=WebAssetListResponse)
async def list_web(page: int = Query(1, ge=1), per_page: int = Query(50, ge=1, le=200), search: str | None = None, hostname: str | None = None, resource_type: str | None = None, sensitive_only: bool = False, path: str | None = None, project_id: str | None = None, scan_id: str | None = None, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
 ids = await _ids(db, current_user); q = {'project_id': project_id if project_id in ids else {'$in': []}} if project_id else {'project_id': {'$in': ids}}
 for k, v in (("hostname", hostname), ("path", path)): 
  if v: q[k] = {'$regex': re.escape(v), '$options': 'i'}
 if resource_type: q['resource_type'] = resource_type
 if sensitive_only: q['is_sensitive'] = True
 if scan_id: q['scan_id'] = scan_id
 if search: q['$or'] = [{k: {'$regex': re.escape(search), '$options': 'i'}} for k in ('hostname', 'url', 'path', 'title', 'resource_type')]
 total = await db.web_assets.count_documents(q); docs = await db.web_assets.find(q).sort([('last_seen', -1), ('hostname', 1)]).skip((page-1)*per_page).limit(per_page).to_list(per_page); return WebAssetListResponse(records=await _dec(db, docs), total=total, page=page, per_page=per_page)
@router.get('/stats', response_model=WebStatsResponse)
async def web_stats(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
 q={'project_id': {'$in': await _ids(db,current_user)}}; agg=lambda field: db.web_assets.aggregate([{'$match':q},{'$group':{'_id':f'${field}','count':{'$sum':1}}},{'$sort':{'count':-1}}]).to_list(None); types=await agg('resource_type'); hosts=await agg('hostname'); latest=await db.web_assets.find_one(q,sort=[('last_seen',-1)])
 return WebStatsResponse(total_urls=await db.web_assets.count_documents(q), sensitive_endpoints=await db.web_assets.count_documents({**q,'is_sensitive':True}), javascript_files=await db.web_assets.count_documents({**q,'resource_type':'javascript'}), api_endpoints=await db.web_assets.count_documents({**q,'resource_type':'api'}), admin_panels=await db.web_assets.count_documents({**q,'sensitive_reason':{'$regex':'admin|panel|console','$options':'i'}}), last_crawl=latest.get('last_seen') if latest else None, resource_types=[{'label':x['_id'],'count':x['count']} for x in types], hosts=[{'label':x['_id'],'count':x['count']} for x in hosts[:10]])
@router.get('/{record_id}', response_model=WebAssetResponse)
async def web_detail(record_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
 if not ObjectId.is_valid(record_id): raise HTTPException(404,'Web asset not found')
 doc=await db.web_assets.find_one({'_id':ObjectId(record_id),'project_id':{'$in':await _ids(db,current_user)}})
 if not doc: raise HTTPException(404,'Web asset not found')
 return WebAssetResponse(**(await _dec(db,[doc]))[0])
