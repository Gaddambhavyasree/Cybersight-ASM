from datetime import datetime
from typing import Optional
from pydantic import BaseModel
class RiskAsset(BaseModel):
 id:str;project_id:str;hostname:str;ip:Optional[str]=None;risk_score:int=0;risk_level:str='Very Low';risk_breakdown:dict={};risk_recommendations:list[str]=[];last_risk_calculation:Optional[datetime]=None
class RiskList(BaseModel): records:list[RiskAsset];total:int;page:int;per_page:int
class RiskStats(BaseModel): overall_risk_score:int=0;overall_risk_level:str='Very Low';critical_assets:int=0;average_asset_risk:int=0;highest_risk_asset:Optional[RiskAsset]=None;risk_distribution:list[dict]=[];top_assets:list[RiskAsset]=[];last_calculation:Optional[datetime]=None
