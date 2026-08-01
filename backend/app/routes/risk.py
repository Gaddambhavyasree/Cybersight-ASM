from bson import ObjectId
from fastapi import APIRouter,Depends,Query
from app.database import get_database
from app.dependencies.auth import get_current_user
from app.schemas.risk import RiskAsset,RiskList,RiskStats
router=APIRouter(prefix='/api/risk-assessment',tags=['Risk Assessment'])
async def ids(db,u):
 q={} if str(u.get('role','')).lower()=='admin' else {'created_by':str(u['_id'])};return [str(x['_id']) async for x in db.projects.find(q,{'_id':1})]
def conv(d):
    d = dict(d)
    d['id'] = str(d.pop('_id'))
    d['hostname'] = d.get('hostname') or d.get('ip') or 'Unknown asset'
    return d
@router.get('',response_model=RiskList)
async def listing(page:int=Query(1,ge=1),per_page:int=Query(25,ge=1,le=200),project_id:str|None=None,search:str|None=None,current_user:dict=Depends(get_current_user),db=Depends(get_database)):
 ps=await ids(db,current_user);q={'project_id':project_id if project_id in ps else {'$in':[]}} if project_id else {'project_id':{'$in':ps}}
 if search:q['hostname']={'$regex':search,'$options':'i'}
 total=await db.assets.count_documents({**q,'risk_score':{'$exists':True}});docs=await db.assets.find({**q,'risk_score':{'$exists':True}}).sort('risk_score',-1).skip((page-1)*per_page).limit(per_page).to_list(per_page);return RiskList(records=[RiskAsset(**conv(x)) for x in docs],total=total,page=page,per_page=per_page)
@router.get('/stats',response_model=RiskStats)
async def stats(project_id:str|None=None,current_user:dict=Depends(get_current_user),db=Depends(get_database)):
 ps=await ids(db,current_user);q={'project_id':project_id if project_id in ps else {'$in':[]}} if project_id else {'project_id':{'$in':ps}};docs=await db.assets.find({**q,'risk_score':{'$exists':True}}).sort('risk_score',-1).to_list(None);levels=('Critical','High','Medium','Low','Very Low');dist=[{'label':x,'count':sum(1 for d in docs if d.get('risk_level')==x)} for x in levels];highest=RiskAsset(**conv(dict(docs[0]))) if docs else None;avg=round(sum(d.get('risk_score',0) for d in docs)/len(docs)) if docs else 0;return RiskStats(overall_risk_score=avg,overall_risk_level=highest.risk_level if highest else 'Very Low',critical_assets=sum(1 for d in docs if d.get('risk_level')=='Critical'),average_asset_risk=avg,highest_risk_asset=highest,risk_distribution=dist,top_assets=[RiskAsset(**conv(dict(d))) for d in docs[:10]],last_calculation=max((d.get('last_risk_calculation') for d in docs if d.get('last_risk_calculation')),default=None))

@router.get('/{asset_id}', response_model=RiskAsset)
async def detail(asset_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    ps = await ids(db, current_user)
    from fastapi import HTTPException
    try:
        object_id = ObjectId(asset_id)
    except Exception:
        raise HTTPException(status_code=404, detail='Risk assessment not found')
    doc = await db.assets.find_one({'_id': object_id, 'project_id': {'$in': ps}, 'risk_score': {'$exists': True}})
    if not doc:
        raise HTTPException(status_code=404, detail='Risk assessment not found')
    return RiskAsset(**conv(doc))
